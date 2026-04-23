# -*- coding: utf-8 -*-
"""
Graph View - Custom graphics view for layer relationship graphs
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor
from qgis.PyQt.QtWidgets import (
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMessageBox,
)

from qflowcrate.Plugin.Graph.connection_arrow import ConnectionArrow
from qflowcrate.Plugin.Graph.layer_node import LayerNode
from qflowcrate.Plugin.Graph.process_node import ProcessNode


class GraphView(QGraphicsView):
    """Custom graphics view for layer relationships"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self):
        """Initialize the GraphView with scene and settings"""
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Enable keyboard focus for zoom shortcuts
        self.setFocusPolicy(Qt.StrongFocus)

        # Connection mode
        self.connection_mode = False
        self.connection_start = None

        # Set scene size
        self.scene.setSceneRect(0, 0, 1000, 800)

    # ============================================================================
    # DRAG AND DROP HANDLERS
    # ============================================================================

    def dragEnterEvent(self, event):  # noqa: N802
        """Accept drag events.

        :param event: Drag enter event
        :type event: QDragEnterEvent
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):  # noqa: N802
        """Handle drag move.

        :param event: Drag move event
        :type event: QDragMoveEvent
        """
        event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        """Handle drop events - create new nodes.

        :param event: Drop event
        :type event: QDropEvent
        """
        if event.mimeData().hasText():
            data = event.mimeData().text().split("|")
            node_type = data[0]
            name = data[1]

            # Convert to scene coordinates
            scene_pos = self.mapToScene(event.pos())

            if node_type == "layer":
                layer_type = data[2] if len(data) > 2 else "Vector"
                node = LayerNode(name, layer_type)
                node.setPos(scene_pos)
                self.scene.addItem(node)
            elif node_type == "process":
                algorithm = data[2] if len(data) > 2 else ""
                node = ProcessNode(name, algorithm)
                node.setPos(scene_pos)
                self.scene.addItem(node)

            event.acceptProposedAction()

    # ============================================================================
    # MOUSE EVENT HANDLERS
    # ============================================================================

    def keyPressEvent(self, event):  # noqa: N802
        """Handle keyboard shortcuts for zooming.

        :param event: Key press event
        :type event: QKeyEvent
        """
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Plus:
                # Zoom in
                zoom_factor = 1.2
                current_scale = self.transform().m11()
                new_scale = current_scale * zoom_factor
                if new_scale <= 5.0:
                    self.scale(zoom_factor, zoom_factor)
            elif event.key() == Qt.Key_Minus:
                # Zoom out
                zoom_factor = 1.0 / 1.2
                current_scale = self.transform().m11()
                new_scale = current_scale * zoom_factor
                if new_scale >= 0.1:
                    self.scale(zoom_factor, zoom_factor)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        """Handle mouse press for connections.

        :param event: Mouse press event
        :type event: QMouseEvent
        """
        if self.connection_mode and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())

            # If we clicked on a text item, get its parent node
            if isinstance(item, QGraphicsTextItem):
                item = item.parentItem()

            if isinstance(item, (LayerNode, ProcessNode)):
                if self.connection_start is None:
                    self.connection_start = item
                    item.setBrush(QBrush(QColor(255, 255, 0)))  # Highlight
                else:
                    # Check if connection is valid (layer <-> process only)
                    if self.is_valid_connection(self.connection_start, item):
                        arrow = ConnectionArrow(self.connection_start, item)
                        self.scene.addItem(arrow)
                    else:
                        QMessageBox.warning(
                            None,
                            "Invalid Connection",
                            "Connections are only allowed between layers and "
                            "processing steps.\n"
                            "Layer → Process or Process → Layer",
                        )

                    # Reset
                    self.connection_start.setBrush(
                        self._get_original_brush(self.connection_start)
                    )
                    self.connection_start = None
            else:
                # Cancel connection
                if self.connection_start:
                    self.connection_start.setBrush(
                        self._get_original_brush(self.connection_start)
                    )
                    self.connection_start = None
        else:
            super().mousePressEvent(event)

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def is_valid_connection(self, start_node, end_node):
        """Check if connection between two nodes is valid.

        :param start_node: Starting node for the connection
        :type start_node: LayerNode or ProcessNode
        :param end_node: Ending node for the connection
        :type end_node: LayerNode or ProcessNode
        :return: True if connection is valid, False otherwise
        :rtype: bool
        """
        # Only allow connections between different node types
        if type(start_node) is type(end_node):
            return False  # Same type (layer-layer or process-process) not allowed

        # If connecting TO a layer, check if it can accept input
        if isinstance(end_node, LayerNode):
            if not end_node.can_accept_input_connection():
                return False  # Layer already has an input connection

        return True  # Different types (layer-process) allowed

    def _get_original_brush(self, node):
        """Get original brush color for node type.

        :param node: The node to get the brush for
        :type node: LayerNode or ProcessNode
        :return: Brush with the original color for the node type
        :rtype: QBrush
        """
        if isinstance(node, LayerNode):
            if node.layer_type == "Vector":
                return QBrush(QColor(100, 149, 237))
            else:
                return QBrush(QColor(255, 140, 0))
        elif isinstance(node, ProcessNode):
            return QBrush(QColor(144, 238, 144))
        return QBrush(Qt.white)

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def toggle_connection_mode(self, enabled):
        """Toggle connection creation mode.

        :param enabled: Whether connection mode should be enabled
        :type enabled: bool
        """
        self.connection_mode = enabled
        if not enabled and self.connection_start:
            try:
                self.connection_start.setBrush(
                    self._get_original_brush(self.connection_start)
                )
            except RuntimeError:
                # Object has been deleted
                pass
            self.connection_start = None
