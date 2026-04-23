import tempfile
import zipfile
import json
import os

import pytest
from qgis.testing import start_app
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from qflowcrate.Plugin.Import.import_tab import ImportTab

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qgis_app():
    """Start QGIS application for tests."""
    yield start_app()


@pytest.fixture
def import_tab(qgis_app):
    """
    Fixture that creates the ImportTab widget.
    """
    import_tab = ImportTab()
    yield import_tab
    import_tab.deleteLater()


# ============================================================================
# COMPONENT TESTS
# ============================================================================
def test_main_layout_exists(import_tab):
    """Test that main layout is properly created"""
    layout = import_tab.layout()
    assert layout is not None
    assert isinstance(layout, QVBoxLayout)


def test_main_layout_geometry(import_tab):
    """Test that main layout has correct geometry"""
    layout = import_tab.layout()
    assert layout.spacing() == 12

    margins = layout.contentsMargins()
    assert margins.left() == 10
    assert margins.top() == 10
    assert margins.right() == 10
    assert margins.bottom() == 10


def test_ui_components_exist(import_tab):
    """Main UI components are present and have expected defaults."""
    assert hasattr(import_tab, "file_path_lineedit")
    assert hasattr(import_tab, "browse_btn")
    assert hasattr(import_tab, "clear_btn")
    assert hasattr(import_tab, "graph_view")

    # Check placeholders and text
    assert import_tab.file_path_lineedit.placeholderText() == "Select RO-Crate .zip file..."
    assert import_tab.browse_btn.text() == "Browse..."
    assert import_tab.clear_btn.text() == "Clear Graph"


def test_graph_view_properties(import_tab):
    """Test graph view is properly configured"""
    assert import_tab.graph_view is not None
    assert import_tab.graph_view.minimumHeight() == 400
    assert not import_tab.graph_view.acceptDrops()


def test_initial_state(import_tab):
    """Test that ImportTab initializes with empty state"""
    assert isinstance(import_tab.nodes_map, dict)
    assert isinstance(import_tab.entity_map, dict)
    assert isinstance(import_tab.normalized_datasets, dict)
    assert len(import_tab.nodes_map) == 0
    assert len(import_tab.entity_map) == 0
    assert len(import_tab.normalized_datasets) == 0
    assert import_tab.file_path_lineedit.text() == ""


def test_normalize_id(import_tab):
    """Test ID normalization"""
    assert import_tab._normalize_id("./data/layer.shp") == "data/layer.shp"
    assert import_tab._normalize_id("data/layer.shp/") == "data/layer.shp"
    assert import_tab._normalize_id("./data/layer.shp/") == "data/layer.shp"
    assert import_tab._normalize_id("data") == "data"
    assert import_tab._normalize_id("") == ""


def test_clear_graph(import_tab):
    """Test clearing the graph"""
    # Add some dummy data
    import_tab.nodes_map["node1"] = "dummy"
    import_tab.entity_map["entity1"] = "dummy"
    import_tab.normalized_datasets["dataset1"] = "dummy"
    import_tab.file_path_lineedit.setText("path.zip")

    # Clear
    import_tab.clear_graph()

    # Check cleared
    assert len(import_tab.nodes_map) == 0
    assert len(import_tab.entity_map) == 0
    assert len(import_tab.normalized_datasets) == 0
    assert import_tab.file_path_lineedit.text() == ""


def test_load_graph_from_crate_minimal():
    """Test loading a minimal valid RO-Crate"""
    import_tab = ImportTab()

    # Create minimal RO-Crate data
    metadata = {
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Root Dataset"
            },
            {
                "@id": "https://orcid.org/0000-0000-0000-0000",
                "@type": "Person",
                "name": "Open Source"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("ro-crate-metadata.json", json.dumps(metadata))

        # Load the crate
        import_tab.load_graph_from_crate(zip_path)

        # Should have parsed entities
        assert len(import_tab.entity_map) == 2
        assert "./" in import_tab.entity_map
        assert "https://orcid.org/0000-0000-0000-0000" in import_tab.entity_map


def test_load_graph_from_crate_with_process():
    """Test loading RO-Crate with a process"""
    import_tab = ImportTab()

    metadata = {
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset"
            },
            {
                "@id": "process1",
                "@type": "CreateAction",
                "name": "Test Process",
                "description": "A test process",
                "instrument": [{"@id": "tool1"}],
                "object": [{"@id": "input1"}],
                "result": [{"@id": "output1"}]
            },
            {
                "@id": "tool1",
                "@type": "SoftwareApplication",
                "name": "Test Tool"
            },
            {
                "@id": "input1",
                "@type": "Dataset",
                "name": "Input Layer",
                "description": "Input description",
                "layerVisible": True
            },
            {
                "@id": "output1",
                "@type": "Dataset",
                "name": "Output Layer",
                "description": "Output description",
                "layerVisible": False
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("ro-crate-metadata.json", json.dumps(metadata))

        # Load the crate
        import_tab.load_graph_from_crate(zip_path)

        # Should have nodes
        assert len(import_tab.nodes_map) >= 3  # process + 2 layers
        assert "process1" in import_tab.nodes_map
        assert "input1" in import_tab.nodes_map or import_tab._normalize_id("input1") in import_tab.nodes_map
        assert "output1" in import_tab.nodes_map or import_tab._normalize_id("output1") in import_tab.nodes_map