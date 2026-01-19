# -*- coding: utf-8 -*-
"""
Main Dialog - Main dialog class that coordinates all tab widgets
"""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
)
from qgis.PyQt import QtGui

import os

# Import individual tab widgets
from .Export.export_tab import ExportTab
from .Graph.graph_tab import GraphTab
from .Instruction.instruction_tab import InstructionTab


class MainDialog(QDialog):
    """Main dialog for automated workflow documentation"""

    # Signals for workflow events
    layer_documented = pyqtSignal(str, dict)  # layer_name, metadata
    layer_removed = pyqtSignal(str)  # layer_name

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None):
        """Initialize the Main Dialog.

        :param parent: Parent widget
        :type parent: QWidget
        """
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("QFlowCrate")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'icon.svg')
        self.setWindowIcon(QtGui.QIcon(icon_path))
        self.setMinimumSize(1000, 700)
        self.resize(1000, 700)

        # Make window resizable and allow maximizing
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # Setup the UI
        self.setup_ui()

        # Initialize tab widgets
        self._initialize_tab_widgets()

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    # ============================================================================
    # UI SETUP
    # ============================================================================

    def setup_ui(self):
        """Setup the user interface"""
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(False)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)
        self.tab_widget.setTabBarAutoHide(False)

        main_layout.addWidget(self.tab_widget)

        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal
        )

        # Connect button box signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

        # Set main layout
        self.setLayout(main_layout)

    def _initialize_tab_widgets(self):
        """Initialize and configure all tab widgets"""
        # Create tab widget instances
        self.instruction_tab = InstructionTab(parent=self)
        self.graph_tab = GraphTab(parent=self)
        self.export_tab = ExportTab(parent=self)

        # Add tabs to the main tab widget
        self.tab_widget.addTab(self.instruction_tab, "Instructions")
        self.tab_widget.addTab(self.graph_tab, "Graph")
        self.tab_widget.addTab(self.export_tab, "Export")

        # Set initial tab
        self.tab_widget.setCurrentIndex(0)  # Start with Instructions tab

        # Connect signals between tabs if needed
        self._setup_inter_tab_connections()

    def _setup_inter_tab_connections(self):
        """Setup connections between different tabs"""
        # Connect export tab to get graph data if needed
        # You can add connections here when export needs graph data
        pass

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def _on_tab_changed(self, index):
        """Handle tab change events.

        :param index: Index of the newly selected tab
        :type index: int
        """
        if index == 1:  # Graph tab
            # Focus on graph view when switching to graph tab
            self.graph_tab.graph_view.setFocus()

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def get_graph_data(self):
        """Get current graph data for export or other purposes.

        :return: Graph data
        :rtype: dict
        """
        return self.graph_tab.export_graph_data()

    def clear_graph(self):
        """Clear the graph - useful for export or reset functionality"""
        self.graph_tab.clear_graph()

    def load_graph_data(self, data):
        """Load graph data - useful for import functionality.

        :param data: Graph data to load
        :type data: dict
        """
        self.graph_tab.load_graph_data(data)
