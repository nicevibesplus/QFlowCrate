# -*- coding: utf-8 -*-
"""
Import Tab Widget - Widget for importing and visualizing RO-Crate workflows
"""

import ast
import json
import re
import zipfile
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from qflowcrate.Plugin.Graph.connection_arrow import ConnectionArrow
from qflowcrate.Plugin.Graph.graph_view import GraphView
from qflowcrate.Plugin.Graph.layer_node import LayerNode
from qflowcrate.Plugin.Graph.process_node import ProcessNode
from qflowcrate.Plugin.utility import get_logger


# ============================================================================
# MOCK OBJECTS FOR READ-ONLY METADATA DIALOGS
# ============================================================================

class ImportedLayer:
    """Mock layer object rich enough to satisfy LayerMetadataDialog"""
    def __init__(self, dataset_entity, entity_map):
        self.id = dataset_entity.get("@id", "unknown")
        self.name = dataset_entity.get("name", "Unknown Layer")
        self.clean_name = self.name
        self.description = dataset_entity.get("description", "")
        
        visible_val = dataset_entity.get("layerVisible", True)
        self.visible = str(visible_val).lower() == "true" if isinstance(visible_val, str) else bool(visible_val)

        # Prepare default values
        self.type = "Unknown"
        self.source = self.id
        self.external = False
        self.source_title = ""
        self.source_url = ""
        self.source_date = ""
        self.source_comment = ""

        # Find geometry entity which contains technical & external metadata
        geometry_entity = None
        has_parts = dataset_entity.get("hasPart", [])
        if isinstance(has_parts, dict): 
            has_parts = [has_parts]
            
        for part_ref in has_parts:
            part_id = part_ref if isinstance(part_ref, str) else part_ref.get("@id", "")
            if part_id in entity_map and "geometry" in part_id.lower():
                geometry_entity = entity_map[part_id]
                break

        # Extract metadata from geometry entity
        if geometry_entity:
            self.source = geometry_entity.get("@id", self.id)
            
            # Extract layer type (fall back to additionalType if layerType is somehow missing)
            raw_type = geometry_entity.get("layerType", geometry_entity.get("additionalType", "Unknown"))
            if isinstance(raw_type, list): 
                raw_type = raw_type[0]
                
            if "Vector" in raw_type or "Point" in raw_type or "Line" in raw_type or "Polygon" in raw_type:
                self.type = "Vector"
            elif "Raster" in raw_type:
                self.type = "Raster"
            else:
                self.type = raw_type
                
            # Extract optional external source info
            self.source_title = geometry_entity.get("sourceTitle", "")
            self.source_url = geometry_entity.get("sourceURL", "")
            self.source_date = geometry_entity.get("sourceDate", "")
            self.source_comment = geometry_entity.get("sourceComment", "")

            # Enable 'External Source' flag if data is present
            if self.source_title or self.source_url or self.source_comment:
                self.external = True


class ImportedProcess:
    """Mock process object rich enough to satisfy ProcessMetadataDialog"""
    def __init__(self, action_entity, instrument_entity=None):
        self.id = action_entity["@id"]
        self.name = action_entity.get("name", "Unknown Process")
        self.description = action_entity.get("description", "")
        
        if instrument_entity:
            self.algorithm_id = instrument_entity.get("name", "Unknown Algorithm")
        else:
            self.algorithm_id = "Unknown Algorithm"
            
        # Reconstruct timestamp from ID since the process exporter doesn't write it explicitly
        self.timestamp = action_entity.get("endTime", action_entity.get("startTime", ""))
        if not self.timestamp:
            match = re.search(r'(\d{2})(\d{2})(\d{4})(\d{2})(\d{2})(\d{2})$', self.id)
            if match:
                dd, mm, yyyy, hh, mnt, ss = match.groups()
                self.timestamp = f"{dd}.{mm}.{yyyy} {hh}:{mnt}:{ss}"
            else:
                self.timestamp = "Unknown Time"
        
        # Read custom QGIS properties
        self.log = action_entity.get("qgisLog", "")
        raw_params = action_entity.get("qgisParameters", "{}")
        raw_results = action_entity.get("qgisResults", "{}")
        
        # Convert JSON strings to dictionaries for UI rendering in the metadata dialog
        try:
            self.parameters = ast.literal_eval(raw_params) if isinstance(raw_params, str) else raw_params
        except Exception:
            self.parameters = raw_params
            
        try:
            self.results = ast.literal_eval(raw_results) if isinstance(raw_results, str) else raw_results
        except Exception:
            self.results = raw_results
            
    def set_input(self, ids): pass
    def set_result(self, ids): pass


# ============================================================================
# MAIN IMPORT TAB WIDGET
# ============================================================================

class ImportTab(QWidget):
    """Widget for importing and visualizing RO-Crate workflows"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ImportTab")
        self.nodes_map = {}  # Map of NORMALIZED @id -> Node instance
        self.entity_map = {} # Map of raw @id -> JSON entity
        self.normalized_datasets = {} # Map of NORMALIZED @id -> Dataset JSON

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface programmatically"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        instruction_label = QLabel(
            "Select an exported RO-Crate (.zip) file to visualize its workflow graph. "
            "This view is read-only. Right-click any node to inspect its metadata. "
            "To zoom in and out of the graph, use the keyboard shortcuts Ctrl & '+' / Ctrl & '-', respectively."
        )
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        file_layout = QHBoxLayout()
        file_layout.setSpacing(8)

        self.file_path_lineedit = QLineEdit()
        self.file_path_lineedit.setPlaceholderText("Select RO-Crate .zip file...")
        self.file_path_lineedit.setReadOnly(True)
        file_layout.addWidget(self.file_path_lineedit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)

        self.clear_btn = QPushButton("Clear Graph")
        self.clear_btn.clicked.connect(self.clear_graph)
        file_layout.addWidget(self.clear_btn)

        main_layout.addLayout(file_layout)

        self.graph_view = GraphView()
        self.graph_view.setMinimumHeight(400)
        self.graph_view.setAcceptDrops(False)
        main_layout.addWidget(self.graph_view)

        self.setLayout(main_layout)

    def browse_file(self):
        """Open file dialog to select RO-Crate zip"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select RO-Crate Archive", "", "ZIP Files (*.zip);;All Files (*)"
        )

        if file_path:
            self.file_path_lineedit.setText(file_path)
            self.load_graph_from_crate(file_path)

    def clear_graph(self):
        """Clear all items from graph"""
        self.graph_view.scene.clear()
        self.nodes_map.clear()
        self.entity_map.clear()
        self.normalized_datasets.clear()
        self.file_path_lineedit.clear()

    def _normalize_id(self, raw_id):
        """Normalizes IDs by stripping './' prefix and '/' suffix."""
        if not raw_id:
            return ""
        return raw_id.lstrip('./').rstrip('/')

    def load_graph_from_crate(self, zip_path):
        """Parse RO-Crate zip and build the visual graph."""
        self.graph_view.scene.clear()
        self.nodes_map.clear()
        self.entity_map.clear()
        self.normalized_datasets.clear()

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                if "ro-crate-metadata.json" not in zf.namelist():
                    raise ValueError("ro-crate-metadata.json missing in archive.")
                with zf.open("ro-crate-metadata.json") as f:
                    metadata = json.load(f)

            graph_data = metadata["@graph"]

            # 1. Map all entities
            self.entity_map = {item["@id"]: item for item in graph_data}
            
            # 2. Map Datasets specially to handle ID normalization 
            for item in graph_data:
                types = item["@type"]
                if not isinstance(types, list): 
                    types = [types]
                
                if "Dataset" in types and item["@id"] not in ["./", ".\\"]:
                    norm_id = self._normalize_id(item["@id"])
                    self.normalized_datasets[norm_id] = item

            # 3. Identify Processing Steps
            actions = []
            for item in graph_data:
                types = item["@type"]
                if not isinstance(types, list): 
                    types = [types]
                if "CreateAction" in types:
                    actions.append(item)

            # 4. Reconstruct Nodes and Connections
            connections_to_make = []

            for action in actions:
                action_id = action["@id"]
                
                # Fetch instrument entity to pass to our Mock Process
                instrument_refs = action.get("instrument", [])
                instrument_entity = None
                if instrument_refs:
                    ref_id = instrument_refs[0]["@id"] if isinstance(instrument_refs, list) else instrument_refs["@id"]
                    instrument_entity = self.entity_map.get(ref_id)

                # Create Process Node
                process_obj = ImportedProcess(action, instrument_entity)
                p_node = ProcessNode(process_obj)
                self._disable_interactions(p_node)
                self.nodes_map[action_id] = p_node
                self.graph_view.scene.addItem(p_node)

                # Process Inputs (Data -> Process)
                inputs = action.get("object", [])
                if isinstance(inputs, dict): 
                    inputs = [inputs]
                
                for input_ref in inputs:
                    in_id = input_ref.get("@id")
                    if in_id:
                        norm_in_id = self._ensure_layer_node_exists(in_id)
                        connections_to_make.append((norm_in_id, action_id))

                # Process Outputs (Process -> Data)
                outputs = action.get("result", [])
                if isinstance(outputs, dict): 
                    outputs = [outputs]
                
                for output_ref in outputs:
                    out_id = output_ref.get("@id")
                    if out_id:
                        norm_out_id = self._ensure_layer_node_exists(out_id)
                        connections_to_make.append((action_id, norm_out_id))

            # 5. Draw Connections
            for source_id, target_id in connections_to_make:
                source_node = self.nodes_map.get(source_id)
                target_node = self.nodes_map.get(target_id)
                
                if source_node and target_node:
                    arrow = ConnectionArrow(source_node, target_node, deletable=False)
                    self.graph_view.scene.addItem(arrow)

            # 6. Apply auto-layout
            self._apply_auto_layout(connections_to_make)

        except Exception as e:
            self.logger.error(f"Failed to load RO-Crate: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to parse RO-Crate:\n{str(e)}")
            self.clear_graph()

    def _ensure_layer_node_exists(self, raw_layer_ref):
        """Create a LayerNode. Handles the ID mismatch between inputs/outputs and datasets."""
        norm_id = self._normalize_id(raw_layer_ref)
        
        if norm_id not in self.nodes_map:
            # Get the correct dataset via normalized ID
            dataset_entity = self.normalized_datasets.get(norm_id)
            
            # Fallback if it is not a dataset
            if not dataset_entity:
                dataset_entity = self.entity_map.get(raw_layer_ref, {"@id": raw_layer_ref})
            
            layer_obj = ImportedLayer(dataset_entity, self.entity_map)
            l_node = LayerNode(layer_obj)
            self._disable_interactions(l_node)
            
            # Register node under NORMALIZED id for connections
            self.nodes_map[norm_id] = l_node
            self.graph_view.scene.addItem(l_node)
            
        return norm_id

    def _disable_interactions(self, node):
        """Replace standard context menu with a read-only inspect menu."""
        node.setToolTip(node.toolTip() + "\n(Right-click to Inspect)")
        
        def custom_context_menu(event):
            menu = QMenu()
            inspect_action = menu.addAction("Inspect Details")
            action = menu.exec_(event.screenPos())
            
            if action == inspect_action:
                if isinstance(node, LayerNode):
                    node._inspect_layer()
                elif isinstance(node, ProcessNode):
                    node._inspect_process()

        node.contextMenuEvent = custom_context_menu

    # ============================================================================
    # GRAPH LAYOUT ENGINE
    # ============================================================================

    def _apply_auto_layout(self, edges):
        """A simple left-to-right topological layout algorithm."""
        if not self.nodes_map:
            return

        in_degrees = {node_id: 0 for node_id in self.nodes_map.keys()}
        out_edges = {node_id: [] for node_id in self.nodes_map.keys()}
        
        for source, target in edges:
            in_degrees[target] = in_degrees.get(target, 0) + 1
            out_edges[source].append(target)

        queue = [node_id for node_id, degree in in_degrees.items() if degree == 0]
        
        if not queue and self.nodes_map:
            queue = [list(self.nodes_map.keys())[0]]

        levels = {}
        while queue:
            current_id = queue.pop(0)
            current_level = levels.get(current_id, 0)
            
            for neighbor in out_edges.get(current_id, []):
                levels[neighbor] = max(levels.get(neighbor, 0), current_level + 1)
                in_degrees[neighbor] -= 1
                if in_degrees[neighbor] <= 0:
                    queue.append(neighbor)

        for node_id in self.nodes_map:
            if node_id not in levels:
                levels[node_id] = 0

        level_groups = {}
        for node_id, lvl in levels.items():
            level_groups.setdefault(lvl, []).append(node_id)

        horizontal_spacing = 250
        vertical_spacing = 150
        
        for lvl, node_ids in level_groups.items():
            x_pos = 50 + (lvl * horizontal_spacing)
            
            total_height = len(node_ids) * vertical_spacing
            start_y = (self.graph_view.scene.sceneRect().height() - total_height) / 2
            
            for index, node_id in enumerate(node_ids):
                y_pos = max(50, start_y + (index * vertical_spacing))
                self.nodes_map[node_id].setPos(x_pos, y_pos)

        for node in self.nodes_map.values():
            if isinstance(node, LayerNode):
                for arrow in node.connections + node.input_arrows:
                    arrow.update_position()
            elif isinstance(node, ProcessNode):
                for arrow in node.input_arrows + node.output_arrows:
                    arrow.update_position()

        # Update scene rect to encompass all items
        scene_rect = self.graph_view.scene.itemsBoundingRect()
        self.graph_view.scene.setSceneRect(scene_rect)

        # Fit the view to show all items within the visible area
        self.graph_view.fitInView(scene_rect, Qt.KeepAspectRatio)