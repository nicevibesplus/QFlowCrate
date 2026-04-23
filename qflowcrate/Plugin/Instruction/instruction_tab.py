# -*- coding: utf-8 -*-
"""
Instruction Tab Widget - Contains usage instructions for the application
"""

from qgis.PyQt.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class InstructionTab(QWidget):
    """Widget containing instructions for using the application"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None):
        """Initialize the Instruction tab widget.

        :param parent: Parent widget
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setup_ui()

    # ============================================================================
    # UI SETUP
    # ============================================================================

    def setup_ui(self):
        """Setup the UI with comprehensive instructions"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Create scroll area for instructions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.NoFrame)

        # Create container widget for scroll area content
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        self._add_section(
            container_layout,
            "Application Overview",
            "This plugin helps you to document your project and its creation workflow. "
            "It exports to RO-Crate 1.1 to enable sharing of the map. The export "
            "includes layers, processing steps, their dependencies and some additional "
            "provenance information.",
        )

        # Graph tab instructions
        self._add_section(
            container_layout,
            "Graph Tab - Creating Your Workflow",
            "This tab allows you to create your projects workflow. All the nodes in "
            "this graph will be exported to the RO-Crate.",
            "Step 1: Add all your projects layers to the graph. This should include "
            "all the visible map layers, that are part of your final map. But this "
            "should also include all the original source layers form where your "
            "visible layers may be derived from. When you add a layer to the graph, "
            "it will ask for a description. Also you can set the layer as external "
            "(from a external remote source), then you also will be asked to enter "
            "information about the files original source. Currently supported are: "
            "ogr, gdal, WMS, WFS, memory.",
            "Step 2: Add all the processing steps that were used in your project to "
            "the graph. This should include all the steps that created new layers from "
            "original sources. When you add a processing step to the graph, it will "
            "ask for a title and description.",
            "Step 3: Add connections between the graphs layers and processing steps. "
            "This creates a complete workflow diagram. Without this, the dependencies "
            "of the layers will be missing in the final export. "
            "The user can zoom in and out of the graph using the keyboard shortcuts "
            "Ctrl & '+' / Ctrl & '-', respectively.",
        )
        self._add_section(
            container_layout,
            "Export Tab - Exporting Your Workflow",
            "This tab allows you to export your projects workflow to RO-Crate.",
            "Step 1: Enter author information. This must include the authors name. "
            "If you have an ORCID, please enter it. You may also enter your "
            "affiliation to an organization or company.",
            "Step 2: Enter project information. This must include a license, a "
            "project title and description.",
            "Step 3: Select a path where to save the RO-Crate zip archive. It will "
            "also create a log file in the same directory. After you have done that, "
            "hit Export RO-Crate.",
        )
        self._add_section(
            container_layout,
            "Import Tab - Importing an Existing RO-Crate",
            "This tab allows you to import an existing RO-Crate. This can be used to "
            "recreate the workflow graph from a previously exported RO-Crate.",
        )

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def _add_section(self, layout, title, *content):
        """Add a formatted section with content to a layout.

        Creates a QGroupBox with the given title and adds all provided content
        items as word-wrapped QLabel widgets in a vertical arrangement.

        :param layout: The parent layout to which the section will be added
        :type layout: QLayout
        :param title: The title displayed in the group box header
        :type title: str
        :param content: Variable number of text strings to display as labels
        :type content: str
        """
        group = QGroupBox(self)
        group.setTitle(title)

        glayout = QFormLayout(group)
        glayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        glayout.setHorizontalSpacing(8)
        glayout.setVerticalSpacing(8)
        glayout.setContentsMargins(10, 10, 10, 10)

        for c in content:
            label = QLabel(c)
            label.setWordWrap(True)
            glayout.addRow(label)

        layout.addWidget(group)
