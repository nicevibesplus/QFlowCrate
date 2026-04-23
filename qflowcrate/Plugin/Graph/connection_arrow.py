# -*- coding: utf-8 -*-
"""
Connection Arrow - Directional arrow connecting nodes in graph view
"""

import math

from qgis.PyQt.QtCore import QPointF, Qt
from qgis.PyQt.QtGui import QBrush, QPen, QPolygonF
from qgis.PyQt.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem

from qflowcrate.Plugin.Graph.layer_node import LayerNode
from qflowcrate.Plugin.Graph.process_node import ProcessNode


class ConnectionArrow(QGraphicsLineItem):
    """Directional arrow connecting nodes"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, start_node, end_node, deletable=True):
        """Initialize a ConnectionArrow between two nodes.

        :param start_node: Starting node for the connection
        :type start_node: LayerNode or ProcessNode
        :param end_node: Ending node for the connection
        :type end_node: LayerNode or ProcessNode
        :param deletable: Whether the arrow can be deleted by clicking
        :type deletable: bool
        """
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.arrowhead = None  # Will hold the arrowhead polygon
        self.deletable = deletable

        # Set visual properties
        self.setPen(QPen(Qt.black, 2))

        # Register with nodes
        if isinstance(start_node, LayerNode):
            start_node.connections.append(self)
        elif isinstance(start_node, ProcessNode):
            start_node.add_output_arrow(self)

        if isinstance(end_node, LayerNode):
            end_node.connections.append(self)
        elif isinstance(end_node, ProcessNode):
            end_node.add_input_arrow(self)

        # Create initial position and arrowhead
        self.update_position()

        # Add to scene immediately if nodes are already in scene
        if self.start_node.scene() and self.end_node.scene():
            scene = self.start_node.scene()
            scene.addItem(self)
            if self.arrowhead:
                scene.addItem(self.arrowhead)

        self.setToolTip("Double click to delete connection" if self.deletable else "")

    # ============================================================================
    # POSITION CALCULATION
    # ============================================================================

    def update_position(self):
        """Update arrow position and arrowhead based on node positions"""
        start_center = self.start_node.sceneBoundingRect().center()
        end_center = self.end_node.sceneBoundingRect().center()

        # Calculate connection points on node boundaries
        start_rect = self.start_node.boundingRect()
        end_rect = self.end_node.boundingRect()

        # Get direction vector
        dx = end_center.x() - start_center.x()
        dy = end_center.y() - start_center.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            # Normalize direction
            dx /= length
            dy /= length

            if isinstance(self.start_node, LayerNode):  # Rectangle
                start_edge = self._get_rect_edge_point(start_center, start_rect, dx, dy)
            else:  # Ellipse
                start_edge = self._get_ellipse_edge_point(
                    start_center, start_rect, dx, dy
                )

            if isinstance(self.end_node, LayerNode):  # Rectangle
                end_edge = self._get_rect_edge_point(end_center, end_rect, -dx, -dy)
            else:  # Ellipse
                end_edge = self._get_ellipse_edge_point(end_center, end_rect, -dx, -dy)

            # Set line position
            self.setLine(start_edge.x(), start_edge.y(), end_edge.x(), end_edge.y())

            # Create arrowhead
            self._create_arrowhead(end_edge, dx, dy)

    def _get_rect_edge_point(self, center, rect, dx, dy):
        """Get edge point on rectangle.

        :param center: Center point of the rectangle
        :type center: QPointF
        :param rect: Rectangle bounds
        :type rect: QRectF
        :param dx: X component of direction vector
        :type dx: float
        :param dy: Y component of direction vector
        :type dy: float
        :return: Point on rectangle edge
        :rtype: QPointF
        """
        half_width = rect.width() / 2
        half_height = rect.height() / 2

        # Determine which edge to intersect
        if abs(dx) / half_width > abs(dy) / half_height:
            # Intersect left or right edge
            edge_x = half_width if dx > 0 else -half_width
            edge_y = edge_x * dy / dx if dx != 0 else 0
            edge_y = max(-half_height, min(half_height, edge_y))
        else:
            # Intersect top or bottom edge
            edge_y = half_height if dy > 0 else -half_height
            edge_x = edge_y * dx / dy if dy != 0 else 0
            edge_x = max(-half_width, min(half_width, edge_x))

        return QPointF(center.x() + edge_x, center.y() + edge_y)

    def _get_ellipse_edge_point(self, center, rect, dx, dy):
        """Get edge point on ellipse.

        :param center: Center point of the ellipse
        :type center: QPointF
        :param rect: Ellipse bounds
        :type rect: QRectF
        :param dx: X component of direction vector
        :type dx: float
        :param dy: Y component of direction vector
        :type dy: float
        :return: Point on ellipse edge
        :rtype: QPointF
        """
        a = rect.width() / 2  # Semi-major axis
        b = rect.height() / 2  # Semi-minor axis

        # Parametric form: x = a*cos(t), y = b*sin(t)
        # Find t where direction matches (dx, dy)
        angle = math.atan2(dy, dx)
        edge_x = a * math.cos(angle)
        edge_y = b * math.sin(angle)

        return QPointF(center.x() + edge_x, center.y() + edge_y)

    # ============================================================================
    # ARROWHEAD CREATION
    # ============================================================================

    def _create_arrowhead(self, tip_point, dx, dy):
        """Create arrowhead at tip point.

        :param tip_point: Point where arrowhead should be placed
        :type tip_point: QPointF
        :param dx: X component of direction vector
        :type dx: float
        :param dy: Y component of direction vector
        :type dy: float
        """
        # Remove old arrowhead
        if self.arrowhead and self.arrowhead.scene():
            self.arrowhead.scene().removeItem(self.arrowhead)

        arrowhead_size = 15

        # Calculate arrowhead points
        perp_x = -dy
        perp_y = dx

        p1 = QPointF(
            tip_point.x() - arrowhead_size * dx + arrowhead_size / 2 * perp_x,
            tip_point.y() - arrowhead_size * dy + arrowhead_size / 2 * perp_y,
        )
        p2 = QPointF(
            tip_point.x() - arrowhead_size * dx - arrowhead_size / 2 * perp_x,
            tip_point.y() - arrowhead_size * dy - arrowhead_size / 2 * perp_y,
        )
        p3 = tip_point

        polygon = QPolygonF([p1, p2, p3])

        self.arrowhead = QGraphicsPolygonItem(polygon)
        self.arrowhead.setBrush(QBrush(Qt.black))
        self.arrowhead.setPen(QPen(Qt.black))

        if self.scene():
            self.scene().addItem(self.arrowhead)

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def mousePressEvent(self, event):  # noqa: N802
        """Delete arrow on click if deletable.

        :param event: Mouse press event
        :type event: QMouseEvent
        """
        if event.button() == Qt.LeftButton and self.deletable:
            self.remove_arrow()

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def remove_arrow(self):
        """Remove arrow and unregister from nodes"""
        # Remove arrowhead
        if self.arrowhead and self.arrowhead.scene():
            self.arrowhead.scene().removeItem(self.arrowhead)

        # Unregister from start node
        if isinstance(self.start_node, LayerNode):
            if self in self.start_node.connections:
                self.start_node.connections.remove(self)
        elif isinstance(self.start_node, ProcessNode):
            if self in self.start_node.output_arrows:
                self.start_node.remove_output_arrow(self)

        # Unregister from end node
        if isinstance(self.end_node, LayerNode):
            if self in self.end_node.connections:
                self.end_node.connections.remove(self)
        elif isinstance(self.end_node, ProcessNode):
            if self in self.end_node.input_arrows:
                self.end_node.remove_input_arrow(self)

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)
