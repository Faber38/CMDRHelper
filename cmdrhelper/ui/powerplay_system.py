"""Journal CP values with an explicitly approximate system-control diagram."""
import math
from PySide6.QtCore import QEvent, Qt, QPointF, QRectF, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QPalette, QColor, QPolygonF
from PySide6.QtWidgets import QWidget, QLabel, QFrame, QGridLayout, QHBoxLayout, QVBoxLayout, QProgressBar, QSizePolicy, QToolTip
from cmdrhelper.i18n import tr
from cmdrhelper.powerplay import number, system_status
from cmdrhelper.ui.powerplay_portraits import PowerPortrait, portrait_key

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
    names = {}
    def participant(power):
        key = portrait_key(power)
        names.setdefault(key, power.strip())
        return participants.setdefault(key, set())
    powers = system.get('Powers')
    for power in powers if isinstance(powers, list) else []:
        if isinstance(power, str) and power.strip():
            participant(power)
    conflicts = system.get('PowerplayConflictProgress')
    for entry in conflicts if isinstance(conflicts, list) else []:
        if not isinstance(entry, dict):
            continue
        power = entry.get('Power')
        if not isinstance(power, str) or not power.strip():
            continue
        values = participant(power)
        value = entry.get('ConflictProgress')
        if nonnegative(value):
            values.add(value)
    rows = [(names[power], next(iter(values)) if len(values) == 1 else None)
            for power, values in participants.items()]
    return sorted(rows, key=lambda row: (row[1] is None, -(row[1] or 0), row[0].casefold(), row[0]))


# Empirical Unoccupied conversion, not an authoritative game threshold.
CONFLICT_CP_FACTOR = 120000
# Provisional display scale and CP boundaries, not confirmed official game thresholds.
CONFLICT_BAR_MAX_CP = 180000
CONFLICT_BOUNDARY_CP = 36000
CONFLICT_MINIMUM_CP = 120000
CONFLICT_COLORS = {'aisling_duval': '#00b9ef', 'nakato_kaine': '#a6ff00'}

# Both markers use the same provisional CP scale as the bar.
CONFLICT_MARKERS = (('boundary', CONFLICT_BOUNDARY_CP / CONFLICT_BAR_MAX_CP, '⚔'),
                    ('minimum', CONFLICT_MINIMUM_CP / CONFLICT_BAR_MAX_CP, '☆'))


def conflict_marker_x(width, fraction):
    return max(0., min(max(0, width - 1), fraction * max(0, width - 1)))


class ConflictProgressBar(QProgressBar):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # The existing bar background is dark in both application themes.
        painter.setPen(QPen(QColor('white'), 1.5, Qt.DashLine))
        for _, fraction, _ in CONFLICT_MARKERS:
            x = conflict_marker_x(self.width(), fraction)
            painter.drawLine(QPointF(x, 1), QPointF(x, self.height() - 2))

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            for key, fraction, _ in CONFLICT_MARKERS:
                if abs(event.pos().x() - conflict_marker_x(self.width(), fraction)) <= 7:
                    QToolTip.showText(event.globalPos(), tr('pp2.conflict.' + key + '_help'), self)
                    return True
        return super().event(event)


class ConflictMarkers(QWidget):
    """One caption row below the bar; narrow rows retain symbols and tooltips."""
    def __init__(self):
        super().__init__()
        self.symbols, self.captions = [], []
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.setToolTip(tr('pp2.conflict.threshold_help'))
        self.setAccessibleDescription(self.toolTip())
        for key, _, symbol in CONFLICT_MARKERS:
            caption = tr('pp2.conflict.' + key)
            tooltip = tr('pp2.conflict.' + key + '_help')
            icon = QLabel(symbol, self)
            text = QLabel(caption, self)
            for widget in (icon, text):
                widget.setAlignment(Qt.AlignCenter)
                widget.setToolTip(tooltip)
                widget.setAccessibleName(caption)
                widget.setAccessibleDescription(tooltip)
            self.symbols.append(icon)
            self.captions.append(text)
        self._place()

    def _place(self):
        width = self.width()
        xs = [conflict_marker_x(width, fraction) for _, fraction, _ in CONFLICT_MARKERS]
        # Separate text slots, so long translations never collide.
        split = round(sum(xs) / 2)
        slots = ((0, split), (split, width - split))
        height = max(15, self.fontMetrics().height() + 2)
        self.compact = any(text.sizeHint().width() + 8 > span
                           for text, (_, span) in zip(self.captions, slots))
        self.setFixedHeight(height if self.compact else height * 2)
        for icon, text, x, (left, span) in zip(self.symbols, self.captions, xs, slots):
            icon_width = min(15, max(0, width))
            icon.setGeometry(max(0, min(width - icon_width, round(x - icon_width / 2))),
                             0, icon_width, height)
            text_width = min(span, text.sizeHint().width() + 8)
            text_left = max(left, min(left + span - text_width, round(x - text_width / 2)))
            text.setGeometry(text_left, height, text_width, height)
            text.setVisible(not self.compact)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange) and hasattr(self, 'captions'):
            self._place()


def approximate_conflict_cp(progress):
    if not nonnegative(progress):
        return None
    value = progress * CONFLICT_CP_FACTOR
    # Keep Qt's localized integer formatting within its supported range.
    if not math.isfinite(value) or value > 2**63 - 1:
        return None
    return round(value)


class ConflictRow(QFrame):
    def __init__(self, power, progress, fmt, *, present=True):
        super().__init__()
        self.setObjectName('pp2ConflictRow')
        self.power = power
        self.progress = progress if nonnegative(progress) else None
        self.present = present
        self.power_color = CONFLICT_COLORS.get(portrait_key(power))
        self.setStyleSheet('QFrame#pp2ConflictRow { border: 1px solid palette(mid); border-radius: 4px; }'
                           'QFrame#pp2ConflictRow QLabel { font-size: 10px; }')
        layout = QGridLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setHorizontalSpacing(9)
        layout.setVerticalSpacing(6)
        self.portrait = PowerPortrait()
        self.portrait.setFixedSize(45, 60)
        self.portrait.set_power(power)
        layout.addWidget(self.portrait, 0, 0, 2, 1, Qt.AlignTop)
        self.header = QWidget()
        self.header_layout = QGridLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setHorizontalSpacing(6)
        self.header_layout.setVerticalSpacing(3)
        self.name = label(power)
        self.name.setStyleSheet('font-weight: 600;' +
                               (' color: ' + self.power_color +
                                '; background-color: #101820; padding: 2px; border-radius: 3px;'
                                if self.power_color else ''))
        self.cp_value = approximate_conflict_cp(self.progress) if present else None
        self.cp = label('≈ ' + fmt(self.cp_value) + ' CP' if self.cp_value is not None
                        else tr('pp2.conflict.cp_unavailable'))
        self.cp.setStyleSheet('font-weight: 600;')
        self.cp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value = label((tr('pp2.conflict.progress') + ': ' +
                            (fmt(self.progress) if self.progress is not None else tr('pp2.unknown')))
                           if present else tr('pp2.conflict.no_presence'), 'muted')
        self.thresholds = ConflictMarkers()
        for text in (self.name, self.cp, self.value):
            policy = text.sizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Ignored)
            text.setSizePolicy(policy)
        raw = repr(self.progress) if self.progress is not None else tr('pp2.unknown')
        help_text = tr('pp2.conflict.cp_help', raw=raw)
        self.cp.setToolTip(help_text)
        self.value.setToolTip(help_text if present else tr('pp2.conflict.no_presence'))
        self.bar = ConflictProgressBar()
        self.bar.setRange(0, 10000)
        # Provisional 0–180,000 CP scale; the CP conversion remains unchanged.
        self.bar.setValue(
            round(min(1., self.progress / (CONFLICT_BAR_MAX_CP / CONFLICT_CP_FACTOR)) * 10000)
            if self.progress is not None else 0)
        self.bar.setStyleSheet(
            'QProgressBar { background-color: #101820; border: 1px solid #687581; border-radius: 3px; }'
            'QProgressBar::chunk { background-color: ' +
            (self.power_color or 'palette(mid)') + '; }')
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(18)
        self.bar.setToolTip(help_text)
        self.bar.setAccessibleName(tr('pp2.metric.conflict', power=power))
        self.bar.setAccessibleDescription(self.value.text() + '. ' + self.bar.toolTip())
        self.header_layout.addWidget(self.name, 0, 0)
        self.header_layout.addWidget(self.cp, 1, 0)
        self.header_layout.setColumnStretch(0, 1)
        self._wide_header = False
        layout.addWidget(self.header, 0, 1)
        if present:
            layout.addWidget(self.bar, 1, 1)
            layout.addWidget(self.thresholds, 2, 1)
            layout.addWidget(self.value, 3, 0, 1, 2)
        else:
            self.cp.hide()
            self.bar.hide()
            self.thresholds.hide()
            layout.addWidget(self.value, 1, 1)
        layout.setColumnStretch(1, 1)

    def set_secondary(self, secondary):
        # Preserve readable text while making the trailing participants smaller.
        self.portrait.setFixedSize(36 if secondary else 45, 48 if secondary else 60)
        margin = 5 if secondary else 7
        self.layout().setContentsMargins(margin, margin, margin, margin)
        self.layout().setVerticalSpacing(4 if secondary else 6)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        wide = self.header.width() >= self.name.sizeHint().width() + self.cp.sizeHint().width() + 12
        if wide != self._wide_header:
            self._wide_header = wide
            self.header_layout.removeWidget(self.cp)
            self.header_layout.addWidget(self.cp, 0 if wide else 1, 1 if wide else 0)
            self.header_layout.setColumnStretch(1, 1 if wide else 0)
        # Keep all wrapped lines visible in the surrounding scroll area.
        self.layout().activate()
        self.header_layout.activate()
        for text in (self.name, self.cp, self.value):
            text.setMinimumHeight(0)
            text.setMinimumHeight(max(0, text.heightForWidth(text.width())))
        self.updateGeometry()


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
        self.conflict_columns = QHBoxLayout(self.conflicts)
        self.conflict_columns.setContentsMargins(0, 0, 0, 0)
        self.conflict_columns.setSpacing(9)
        self.conflict_left = QWidget()
        self.conflict_right = QWidget()
        self.conflict_layout = QVBoxLayout(self.conflict_left)
        self.secondary_layout = QVBoxLayout(self.conflict_right)
        for column in (self.conflict_layout, self.secondary_layout):
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(6)
            column.setAlignment(Qt.AlignTop)
        self.conflict_columns.addWidget(self.conflict_left, 1)
        self.conflict_columns.addWidget(self.conflict_right, 1)
        self.conflict_right.hide()
        self.conflict_two_columns = False
        self.conflict_rows = []
        self.own_power_row = None
        layout.addWidget(self.conflicts)

    @staticmethod
    def style(widget,name):
        if widget.objectName()!=name:
            widget.setObjectName(name)
            widget.style().unpolish(widget);widget.style().polish(widget)

    def render(self,system,name,relationship,fmt,own_power=''):
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
        for column in (self.conflict_layout, self.secondary_layout):
            while column.count():
                item = column.takeAt(0)
                item.widget().hide()
                item.widget().deleteLater()
        self.conflict_rows = []
        self.own_power_row = None
        if status == 'unoccupied':
            participants = conflict_participants(system)
            for power, value in participants:
                row = ConflictRow(power, value, fmt)
                self.conflict_layout.addWidget(row)
                self.conflict_rows.append(row)
            if not participants:
                self.conflict_layout.addWidget(label(tr('pp2.no_data'), 'muted'))
            if (isinstance(own_power, str) and own_power.strip()
                    and portrait_key(own_power) not in {portrait_key(p) for p, _ in participants}):
                self.conflict_layout.addWidget(label(tr('pp2.conflict.own_power'), 'sectionTitle'))
                self.own_power_row = ConflictRow(own_power.strip(), None, fmt, present=False)
                self.conflict_layout.addWidget(self.own_power_row)
        self.metrics.setText(' · '.join(metrics));self.metrics.setVisible(bool(metrics))
        self.metrics.setToolTip(self.metrics.text() if status=='unoccupied' else
            tr('pp2.system.control_help')+'\nPowerplayStateControlProgress: '+str(system.get('PowerplayStateControlProgress',unknown)))

    def arrange_conflicts(self, wide):
        """Move the existing rows only; keep own-power information after the leaders."""
        wide = wide and len(self.conflict_rows) >= 3
        arrangement = (wide, tuple(self.conflict_rows))
        if getattr(self, '_conflict_arrangement', None) == arrangement:
            return
        self._conflict_arrangement = arrangement
        self.conflict_two_columns = wide
        for index, row in enumerate(self.conflict_rows):
            self.conflict_layout.removeWidget(row)
            self.secondary_layout.removeWidget(row)
            secondary = wide and index >= 2
            row.set_secondary(secondary)
            if secondary:
                self.secondary_layout.addWidget(row)
            else:
                self.conflict_layout.insertWidget(index, row)
            row.show()
        self.conflict_right.setVisible(wide)
