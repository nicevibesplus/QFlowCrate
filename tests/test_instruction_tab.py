import pytest
from qgis.testing import start_app
from qgis.PyQt.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
)
from qflowcrate.Plugin.Instruction.instruction_tab import InstructionTab

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qgis_app():
    """Start QGIS application for tests."""
    yield start_app()

@pytest.fixture
def instruction_tab(qgis_app):
    """
    Fixture that creates the InstructionTab widget.
    """
    instruction_tab = InstructionTab()
    yield instruction_tab
    instruction_tab.deleteLater()

# ============================================================================
# FUNCTIONALITY TESTS
# ============================================================================


def test_main_layout_exists(instruction_tab):
    """Test that main layout is properly created"""
    layout = instruction_tab.layout()
    assert layout is not None
    assert isinstance(layout, QVBoxLayout)

def test_main_layout_geometry(instruction_tab):
    """Test that main layout has correct geometry"""
    layout = instruction_tab.layout()
    assert layout.spacing() == 12

    margins = layout.contentsMargins()
    assert margins.left() == 10
    assert margins.top() == 10
    assert margins.right() == 10
    assert margins.bottom() == 10

def test_scroll_area_exists(instruction_tab):
    """Test that a scroll area is created in the layout"""
    layout = instruction_tab.layout()
    scroll_area = None
    
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item and isinstance(item.widget(), QScrollArea):
            scroll_area = item.widget()
            break
    
    assert scroll_area is not None
    assert scroll_area.widgetResizable()

def test_expected_sections_exist(instruction_tab):
    """All expected instruction sections should exist."""
    group_boxes = instruction_tab.findChildren(QGroupBox)

    # Should have 4 sections: Overview, Graph Tab, Export Tab, Import Tab
    assert len(group_boxes) == 4

    expected_titles = [
        "Application Overview",
        "Graph Tab - Creating Your Workflow",
        "Export Tab - Exporting Your Workflow",
        "Import Tab - Importing an Existing RO-Crate",
    ]
    titles = [g.title() for g in group_boxes]
    assert expected_titles == titles


def test_sections_have_content(instruction_tab):
    """Each section should contain at least one QLabel."""
    group_boxes = instruction_tab.findChildren(QGroupBox)

    for group in group_boxes:
        labels = group.findChildren(QLabel)
        assert len(labels) > 0, f"No labels found in section '{group.title()}'"


def test_content(instruction_tab):
    """High-level test of the instructions tab content."""
    labels = instruction_tab.findChildren(QLabel)
    all_text = " ".join([label.text() for label in labels])
    
    # Check for key concepts
    keywords = [
        "RO-Crate", "document", "layer", "processing",
        "workflow", "export","author", "license",
    ]
    for word in keywords:
        assert word in all_text, f"Missing info: {word}"


def test_content_word_wrapped(instruction_tab):
    """All instruction labels should have word wrap enabled."""
    labels = instruction_tab.findChildren(QLabel)

    # Should have labels for all content items
    assert len(labels) > 0
    
    # All labels should have word wrap enabled
    for label in labels:
        assert label.wordWrap()