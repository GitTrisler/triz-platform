"""
TRIZ Project Hub — relationship graph.

The concept doc's soul made visible: the object you're looking at sits at the
center, everything it co-occurs with orbits it, edge weight = how many sheets
they share, node color = object type. Click any node and the graph re-centers
there — you traverse the plant, not the folders.

First-degree ring from db.related_objects(); each first-degree node also pulls
its own strongest relations as small satellites, so the view reads as a
constellation rather than a hub-and-spoke. Nodes ease outward from the center
on load (400 ms, OutCubic); hover brightens a node's edge and shows the
co-occurrence count.
"""

from __future__ import annotations

import math

from PySide6.QtCore import (QEasingCurve, QPointF, QRectF, Qt,
                            QVariantAnimation, Signal)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsObject,
                               QGraphicsPathItem, QGraphicsScene,
                               QGraphicsSimpleTextItem, QGraphicsView)

from .theme import MONO, PALETTE, TYPE_COLORS

SCENE = QRectF(-250, -195, 500, 390)
R_FIRST = 118
R_SAT = 178


def _type_color(obj_type: str) -> QColor:
    return QColor(TYPE_COLORS.get(obj_type, PALETTE["muted"]))


class _Node(QGraphicsObject):
    """A plant object: ring in its type color, mono tag label beneath."""

    def __init__(self, graph, tag: str, obj_type: str, radius: float,
                 strength: int = 0, satellite: bool = False):
        super().__init__()
        self.graph = graph
        self.tag = tag
        self.color = _type_color(obj_type)
        self.r = radius
        self.satellite = satellite
        self.edge = None  # set by the graph after edges exist
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setZValue(2)
        if strength:
            self.setToolTip(f"{tag} — shares {strength} sheet"
                            f"{'s' if strength != 1 else ''} with the center object")

        self.label = QGraphicsSimpleTextItem(self._elide(tag), self)
        f = QFont("Cascadia Code")
        f.setStyleHint(QFont.Monospace)
        f.setPointSizeF(6.5 if satellite else 8)
        f.setWeight(QFont.DemiBold)
        self.label.setFont(f)
        self.label.setBrush(QBrush(QColor(
            PALETTE["faint"] if satellite else PALETTE["secondary"])))
        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, radius + 4)
        if satellite:
            self.label.setVisible(False)  # appears on hover — keeps the field calm

    @staticmethod
    def _elide(tag: str, n: int = 12) -> str:
        return tag if len(tag) <= n else tag[: n - 1] + "…"

    def boundingRect(self) -> QRectF:
        m = self.r + 22
        return QRectF(-m, -m, 2 * m, 2 * m)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        ring = QColor(self.color)
        fill = QColor(PALETTE["surface2"])
        if self.satellite:
            ring.setAlpha(150)
        p.setBrush(QBrush(fill))
        p.setPen(QPen(ring, 1.4 if self.satellite else 2.0))
        p.drawEllipse(QPointF(0, 0), self.r, self.r)
        dot = QColor(self.color)
        dot.setAlpha(220)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(dot))
        d = 2.2 if self.satellite else 3.2
        p.drawEllipse(QPointF(0, 0), d, d)

    def hoverEnterEvent(self, e):
        self.setScale(1.18)
        if self.satellite:
            self.label.setVisible(True)
        if self.edge is not None:
            self.edge.set_hot(True)

    def hoverLeaveEvent(self, e):
        self.setScale(1.0)
        if self.satellite:
            self.label.setVisible(False)
        if self.edge is not None:
            self.edge.set_hot(False)

    def mousePressEvent(self, e):
        self.graph.open_object.emit(self.tag)


class _CenterNode(QGraphicsObject):
    """The object in focus: accent halo, tag inside a larger ring."""

    def __init__(self, tag: str, obj_type: str):
        super().__init__()
        self.tag = tag
        self.color = _type_color(obj_type)
        self.r = 24
        self.setZValue(3)
        self.label = QGraphicsSimpleTextItem(tag, self)
        f = QFont("Cascadia Code")
        f.setStyleHint(QFont.Monospace)
        f.setPointSizeF(9)
        f.setWeight(QFont.Bold)
        self.label.setFont(f)
        self.label.setBrush(QBrush(QColor(PALETTE["text"])))
        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, self.r + 6)

    def boundingRect(self) -> QRectF:
        m = self.r + 14
        return QRectF(-m, -m, 2 * m, 2 * m)

    def paint(self, p: QPainter, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        halo = QColor(self.color)
        halo.setAlpha(26)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(0, 0), self.r + 11, self.r + 11)
        p.setBrush(QBrush(QColor(PALETTE["surface3"])))
        p.setPen(QPen(QColor(self.color), 2.4))
        p.drawEllipse(QPointF(0, 0), self.r, self.r)
        dot = QColor(self.color)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(dot))
        p.drawEllipse(QPointF(0, 0), 4.2, 4.2)


class _Edge(QGraphicsPathItem):
    """Curved connector; width and alpha carry co-occurrence strength."""

    def __init__(self, src_item, dst_item, color: QColor, strength_norm: float,
                 satellite: bool = False):
        super().__init__()
        self.src_item = src_item
        self.dst_item = dst_item
        self.setZValue(1)
        c = QColor(color)
        self._alpha = 46 if satellite else int(60 + 70 * strength_norm)
        c.setAlpha(self._alpha)
        w = 1.0 if satellite else 1.0 + 2.6 * strength_norm
        self._pen = QPen(c, w, Qt.SolidLine, Qt.RoundCap)
        self.setPen(self._pen)

    def set_hot(self, hot: bool):
        c = QColor(self._pen.color())
        c.setAlpha(min(235, self._alpha + 130) if hot else self._alpha)
        pen = QPen(self._pen)
        pen.setColor(c)
        pen.setWidthF(self._pen.widthF() + (0.8 if hot else 0.0))
        self.setPen(pen)

    def sync(self):
        a = self.src_item.pos()
        b = self.dst_item.pos()
        path = QPainterPath(a)
        mid = (a + b) / 2
        # gentle bow perpendicular to the chord — reads organic, not spoked
        dx, dy = b.x() - a.x(), b.y() - a.y()
        dist = math.hypot(dx, dy) or 1.0
        bow = min(14.0, dist * 0.08)
        ctrl = QPointF(mid.x() - dy / dist * bow, mid.y() + dx / dist * bow)
        path.quadTo(ctrl, b)
        self.setPath(path)


class RelationGraph(QGraphicsView):
    open_object = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(SCENE, self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setStyleSheet("background: transparent; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(320)
        self._anim = None
        self._animated: list[tuple[object, QPointF]] = []
        self._edges: list[_Edge] = []
        self._nodes: list[_Node] = []

    # ------------------------------------------------------------ population
    def node_count(self) -> int:
        return len(self._nodes)

    def show_relations(self, db, tag: str):
        self._scene.clear()
        self._edges, self._nodes, self._animated = [], [], []
        obj = db.object_by_tag(tag)
        if not obj:
            return
        center = _CenterNode(obj["tag"], obj["type"])
        self._scene.addItem(center)

        related = db.related_objects(obj["id"], limit=10)
        if not related:
            hint = QGraphicsSimpleTextItem(
                "No co-occurrence data — this tag appears alone")
            f = QFont("Segoe UI")
            f.setPointSizeF(9)
            hint.setFont(f)
            hint.setBrush(QBrush(QColor(PALETTE["muted"])))
            br = hint.boundingRect()
            hint.setPos(-br.width() / 2, 46)
            self._scene.addItem(hint)
            return

        max_s = max(r["strength"] for r in related) or 1
        seen = {obj["tag"]} | {r["tag"] for r in related}
        n = len(related)
        for i, r in enumerate(related):
            ang = math.radians(-90 + i * (360 / n))
            target = QPointF(R_FIRST * math.cos(ang), R_FIRST * math.sin(ang))
            node = _Node(self, r["tag"], r["type"], 12,
                         strength=r["strength"])
            self._scene.addItem(node)
            node.setPos(0, 0)
            edge = _Edge(center, node, _type_color(r["type"]),
                         r["strength"] / max_s)
            node.edge = edge
            self._scene.addItem(edge)
            self._edges.append(edge)
            self._nodes.append(node)
            self._animated.append((node, target))

            # satellites: this node's own strongest neighbours, not already shown
            row = db.object_by_tag(r["tag"])
            if row:
                sats = [s for s in db.related_objects(row["id"], limit=4)
                        if s["tag"] not in seen][:2]
                spread = math.radians(15)
                for k, s in enumerate(sats):
                    seen.add(s["tag"])
                    sang = ang + (spread if k == 0 else -spread)
                    starget = QPointF(R_SAT * math.cos(sang),
                                      R_SAT * math.sin(sang))
                    sat = _Node(self, s["tag"], s["type"], 7,
                                strength=s["strength"], satellite=True)
                    self._scene.addItem(sat)
                    sat.setPos(target)
                    sedge = _Edge(node, sat, _type_color(s["type"]), 0.0,
                                  satellite=True)
                    sat.edge = sedge
                    self._scene.addItem(sedge)
                    self._edges.append(sedge)
                    self._nodes.append(sat)
                    self._animated.append((sat, starget))

        self._sync_edges()
        self._play_intro()

    # -------------------------------------------------------------- animation
    def _play_intro(self):
        if self._anim:
            self._anim.stop()
        starts = [(item, item.pos()) for item, _ in self._animated]
        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(420)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def tick(t):
            for (item, target), (_, start) in zip(self._animated, starts):
                item.setPos(start + (target - start) * t)
            self._sync_edges()

        anim.valueChanged.connect(tick)
        anim.start()
        self._anim = anim

    def _sync_edges(self):
        for e in self._edges:
            e.sync()

    # ---------------------------------------------------------------- sizing
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(SCENE, Qt.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        self.fitInView(SCENE, Qt.KeepAspectRatio)
