"""Journal CP values with an explicitly approximate system-control diagram."""
from PySide6.QtCore import Qt, QPointF, QRectF, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QPalette, QColor, QPolygonF
from PySide6.QtWidgets import QWidget, QLabel, QFrame, QGridLayout, QHBoxLayout, QVBoxLayout, QProgressBar, QSizePolicy
from cmdrhelper.i18n import tr
from cmdrhelper.powerplay import number, system_status
from cmdrhelper.ui.powerplay_portraits import PowerPortrait

STAGES = ('unoccupied', 'exploited', 'fortified', 'stronghold')


def label(text='', style=''):
    widget=QLabel(text,objectName=style)
    widget.setTextFormat(Qt.PlainText)
    widget.setWordWrap(True)
    widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return widget


# Visual calibration only, NOT confirmed game thresholds or CP conversion rules.
# The Fortified approximation deliberately does not simulate unreported maluses.
VISUAL_CP_SPANS = {'exploited': 350000, 'fortified': 650000, 'stronghold': 1000000}
STAGE_COLORS = ('#646464', '#b24242', '#519e53', '#985cb7')


def nonnegative(value):
    return number(value) is not None and value >= 0


def marker_positions(status, progress, reinforcement, undermining):
    """Return approximate positions on [0, 1]; None means no evidence to draw.

    Yellow: (stage index + P) / 4, clipped to the complete bar.
    White: (stage index + clamp(P - (R-U)/visual_span, 0, 1)) / 4.
    Without a usable baseline, place white at the known stage's midpoint.
    Unoccupied has no compatible ControlProgress: never invent a yellow marker.
    """
    if status not in STAGES:
        return None, None
    index = STAGES.index(status)
    white = (index + .5) / 4
    if status == 'unoccupied' or number(progress) is None:
        return white, None
    # Preserve raw progress for the baseline; clamp the resulting positions.
    p = progress
    yellow = max(0., min(1., (index + p) / 4))
    if nonnegative(reinforcement) and nonnegative(undermining):
        baseline = p - (reinforcement - undermining) / VISUAL_CP_SPANS[status]
        white = (index + max(0., min(1., baseline))) / 4
    return white, yellow


class SystemControlBar(QWidget):
    """Responsive painted bar, markers, wrapped captions and compact legend."""
    text_flags = Qt.AlignLeft | Qt.AlignTop | Qt.TextWrapAnywhere

    def __init__(self):
        super().__init__()
        self.white_position = self.yellow_position = None
        self.stage_names = []
        self.legend_names = []
        self.set_values('', None, None, None)

    def set_values(self, status, progress, reinforcement, undermining):
        self.white_position, self.yellow_position = marker_positions(
            status, progress, reinforcement, undermining)
        self.stage_names = [tr('pp2.status.' + stage) for stage in STAGES]
        self.legend_names = [tr('pp2.system.status_marker'), tr('pp2.system.cycle_marker')]
        self.setToolTip(tr('pp2.system.approximation'))
        self.setAccessibleName(tr('pp2.system.contest'))
        self.setAccessibleDescription(' · '.join(self.stage_names + self.legend_names)
                                      + '. ' + self.toolTip())
        self.setFixedHeight(self.content_height(self.width()))
        self.update()

    def text_height(self, text, width):
        return self.fontMetrics().boundingRect(
            QRect(0, 0, max(1, int(width)), 10000), self.text_flags, text).height()

    def geometry_for_width(self, width):
        margin = min(12., max(0., width / 8))
        span = max(0., width - 2 * margin)
        return margin, span, span / 4

    def content_height(self, width):
        _, span, segment = self.geometry_for_width(width)
        captions = max((self.text_height(t, segment - 4) for t in self.stage_names), default=0)
        legends = sum(max(18, self.text_height(t, span - 24)) for t in self.legend_names)
        return 48 + captions + 8 + legends + 8

    def sizeHint(self):
        return QSize(420, self.content_height(420))

    def minimumSizeHint(self):
        return QSize(0, self.content_height(self.width()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setFixedHeight(self.content_height(event.size().width()))

    @staticmethod
    def triangle(painter, x, y, radius, yellow=False):
        # White filled/down; yellow outlined/up, as in the game's legend.
        points = ([(x, y), (x-radius, y+12), (x+radius, y+12)] if yellow else
                  [(x-radius, y), (x+radius, y), (x, y+12)])
        polygon = QPolygonF([QPointF(px, py) for px, py in points])
        painter.setPen(QPen(QColor('#303030'), 3))
        painter.setBrush(Qt.NoBrush if yellow else QColor('white'))
        painter.drawPolygon(polygon)
        painter.setPen(QPen(QColor('#ffbf00') if yellow else QColor('white'), 1.5))
        painter.drawPolygon(polygon)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRect(self.rect())
        left, span, segment = self.geometry_for_width(self.width())
        if span < 4:
            return
        radius = min(7., max(0., left - 2))
        caption_height = max(self.text_height(t, segment - 4) for t in self.stage_names)
        for index, color in enumerate(STAGE_COLORS):
            painter.fillRect(QRectF(left + index * segment, 19, segment, 18), QColor(color))
        white, yellow = self.white_position, self.yellow_position
        if white is not None and yellow is not None and white != yellow:
            start = left + span * min(white, yellow)
            end = left + span * max(white, yellow)
            tint = QColor(255, 0, 0, 128) if white > yellow else QColor(0, 128, 255, 128)
            painter.save()
            painter.setClipRect(QRectF(left, 19, span, 18), Qt.IntersectClip)
            painter.fillRect(QRectF(start, 19, end - start, 18), tint)
            painter.restore()
        # Boundaries and markers remain above the translucent interval.
        for index, text in enumerate(self.stage_names):
            x = left + index * segment
            painter.setPen(QPen(self.palette().color(QPalette.Mid), 1))
            painter.drawLine(QPointF(x, 19), QPointF(x, 43 + caption_height))
            painter.setPen(self.palette().color(QPalette.WindowText))
            painter.drawText(QRectF(x+2, 46, max(1., segment-4), caption_height),
                             self.text_flags, text)
        if self.white_position is not None:
            self.triangle(painter, left + span*self.white_position, 5, radius)
        if self.yellow_position is not None:
            self.triangle(painter, left + span*self.yellow_position, 29, radius, True)
        y = 54 + caption_height
        for index, text in enumerate(self.legend_names):
            height = max(18, self.text_height(text, span-24))
            self.triangle(painter, left+8, y+2, radius, bool(index))
            painter.setPen(self.palette().color(QPalette.WindowText))
            painter.drawText(QRectF(left+24, y, max(1., span-24), height), self.text_flags, text)
            y += height


def conflict_participants(system):
    """Union of journal participants; contradictory duplicate values stay unknown."""
    participants = {}
    powers = system.get('Powers')
    for power in powers if isinstance(powers, list) else []:
        if isinstance(power, str) and power.strip():
            participants.setdefault(power.strip(), set())
    conflicts = system.get('PowerplayConflictProgress')
    for entry in conflicts if isinstance(conflicts, list) else []:
        if not isinstance(entry, dict):
            continue
        power = entry.get('Power')
        if not isinstance(power, str) or not power.strip():
            continue
        values = participants.setdefault(power.strip(), set())
        value = entry.get('ConflictProgress')
        if nonnegative(value):
            values.add(value)
    rows = [(power, next(iter(values)) if len(values) == 1 else None)
            for power, values in participants.items()]
    return sorted(rows, key=lambda row: (row[1] is None, -(row[1] or 0), row[0].casefold(), row[0]))


class ConflictRow(QWidget):
    def __init__(self, power, progress, scale, fmt):
        super().__init__()
        self.power, self.progress = power, progress
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.portrait = PowerPortrait()
        self.portrait.setFixedSize(42, 56)
        self.portrait.set_power(power)
        layout.addWidget(self.portrait, 0, Qt.AlignTop)
        details = QGridLayout()
        details.setContentsMargins(0, 0, 0, 0)
        details.setHorizontalSpacing(8)
        details.setVerticalSpacing(2)
        self.name = label(power)
        self.cp = label(tr('pp2.conflict.cp_unavailable'), 'muted')
        self.cp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value = label(tr('pp2.conflict.progress') + ': ' +
                           (fmt(progress) if progress is not None else tr('pp2.unknown')))
        for text in (self.name, self.cp, self.value):
            # Let wrapped labels shrink below the longest translated word.
            policy = text.sizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Ignored)
            text.setSizePolicy(policy)
        self.bar = QProgressBar()
        self.bar.setRange(0, 10000)
        self.bar.setValue(round(progress / scale * 10000) if progress is not None and scale else 0)
        # Only these two colors are evidenced by the supplied game screenshot.
        # Other powers use the approved neutral theme color.
        self.power_color = {'Aisling Duval': '#00b9ef', 'Nakato Kaine': '#a6ff00'}.get(power)
        self.bar.setStyleSheet('QProgressBar::chunk { background-color: ' +
                              (self.power_color or 'palette(mid)') + '; }')
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setToolTip(tr('pp2.conflict.relative_help'))
        self.bar.setAccessibleName(tr('pp2.metric.conflict', power=power))
        self.bar.setAccessibleDescription(self.value.text() + '. ' + self.bar.toolTip())
        details.addWidget(self.name, 0, 0)
        details.addWidget(self.cp, 0, 1)
        details.addWidget(self.value, 1, 0, 1, 2)
        details.addWidget(self.bar, 2, 0, 1, 2)
        details.setColumnStretch(0, 1)
        details.setColumnStretch(1, 1)
        layout.addLayout(details, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep all wrapped lines visible in the surrounding scroll area.
        self.layout().activate()
        for text in (self.name, self.cp, self.value):
            text.setMinimumHeight(text.heightForWidth(text.width()))


class SystemPresentation(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(6)
        self.labels={key:label('', 'cardValue' if key=='system_name' else '')
                     for key in ('system_name','owner','relationship','status')}
        head=QHBoxLayout()
        head.addWidget(self.labels['system_name'],1)
        self.labels['status'].setFrameShape(QFrame.StyledPanel)
        self.labels['status'].setMargin(4)
        head.addWidget(self.labels['status'])
        layout.addLayout(head)
        owner=QHBoxLayout()
        owner.addWidget(self.labels['owner'])
        owner.addWidget(label('·','muted'))
        owner.addWidget(self.labels['relationship'])
        owner.addStretch()
        layout.addLayout(owner)
        self.controlled = QWidget()
        controlled_layout = QVBoxLayout(self.controlled)
        controlled_layout.setContentsMargins(0, 0, 0, 0)
        controlled_layout.setSpacing(6)
        layout.addWidget(self.controlled)
        heading = label(tr('pp2.system.contest') + ' ≈', 'muted')
        heading.setToolTip(tr('pp2.system.approximation'))
        controlled_layout.addWidget(heading)
        contest=QGridLayout()
        self.strengths={key:label('', 'cardValue') for key in ('undermining','reinforcement')}
        for col,key in enumerate(('undermining','reinforcement')):
            caption=label(tr('pp2.system.'+key),'muted')
            tooltip=tr('pp2.system.'+key+'_help')
            caption.setToolTip(tooltip);self.strengths[key].setToolTip(tooltip)
            caption.setAlignment(Qt.AlignLeft if col==0 else Qt.AlignRight)
            self.strengths[key].setAlignment(Qt.AlignLeft if col==0 else Qt.AlignRight)
            contest.addWidget(caption,0,col);contest.addWidget(self.strengths[key],1,col)
            contest.setColumnStretch(col,1)
        controlled_layout.addLayout(contest)
        self.control_bar=SystemControlBar();controlled_layout.addWidget(self.control_bar)
        self.metrics=label()
        layout.addWidget(self.metrics)
        self.conflicts = QWidget()
        self.conflict_layout = QVBoxLayout(self.conflicts)
        self.conflict_layout.setContentsMargins(0, 0, 0, 0)
        self.conflict_layout.setSpacing(8)
        self.conflict_rows = []
        layout.addWidget(self.conflicts)

    @staticmethod
    def style(widget,name):
        if widget.objectName()!=name:
            widget.setObjectName(name)
            widget.style().unpolish(widget);widget.style().polish(widget)

    def render(self,system,name,relationship,fmt):
        unknown=tr('pp2.unknown')
        status=system_status(system.get('PowerplayState'))
        self.labels['system_name'].setText(name or unknown)
        self.labels['owner'].setText(system.get('ControllingPower') or (tr('pp2.unoccupied') if status=='unoccupied' else unknown))
        self.labels['relationship'].setText(tr('pp2.relationship.'+relationship))
        caption=tr('pp2.status.'+status) if status in STAGES else unknown
        self.labels['status'].setText(caption)
        self.labels['status'].setToolTip(tr('pp2.system.stage_help',status=caption)+'\n'+str(system.get('PowerplayState') or unknown))
        self.style(self.labels['status'],'sectionTitle' if status in STAGES else 'muted')
        reinforcement=system.get('PowerplayStateReinforcement')
        undermining=system.get('PowerplayStateUndermining')
        for key, value in (('reinforcement', reinforcement), ('undermining', undermining)):
            self.strengths[key].setText(fmt(value) + ' CP' if nonnegative(value) else unknown)
        self.control_bar.set_values(status, system.get('PowerplayStateControlProgress'),
                                    reinforcement, undermining)
        metrics=[]
        if status in ('exploited','fortified','stronghold'):
            value=system.get('PowerplayStateControlProgress')
            if number(value) is not None:
                metrics.append(tr('pp2.metric.control')+': '+fmt(value))
        self.controlled.setVisible(status != 'unoccupied')
        self.conflicts.setVisible(status == 'unoccupied')
        while self.conflict_layout.count():
            item = self.conflict_layout.takeAt(0)
            item.widget().hide()
            item.widget().deleteLater()
        self.conflict_rows = []
        if status == 'unoccupied':
            participants = conflict_participants(system)
            scale = max((value for _, value in participants if value is not None), default=0)
            for power, value in participants:
                row = ConflictRow(power, value, scale, fmt)
                self.conflict_layout.addWidget(row)
                self.conflict_rows.append(row)
            if not participants:
                self.conflict_layout.addWidget(label(tr('pp2.no_data'), 'muted'))
        self.metrics.setText(' · '.join(metrics));self.metrics.setVisible(bool(metrics))
        self.metrics.setToolTip(self.metrics.text() if status=='unoccupied' else
            tr('pp2.system.control_help')+'\nPowerplayStateControlProgress: '+str(system.get('PowerplayStateControlProgress',unknown)))
