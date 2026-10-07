"""Presentation of existing journal system fields; no derived game mechanics."""
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QPalette
from PySide6.QtWidgets import QWidget, QLabel, QFrame, QGridLayout, QHBoxLayout, QVBoxLayout
from cmdrhelper.i18n import tr
from cmdrhelper.powerplay import number, system_status

STAGES = ('unoccupied', 'exploited', 'fortified', 'stronghold')


def label(text='', style=''):
    widget=QLabel(text,objectName=style)
    widget.setTextFormat(Qt.PlainText)
    widget.setWordWrap(True)
    widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return widget


class ContestLine(QWidget):
    """A relative visual comparison, with exact numbers in adjacent labels."""
    def __init__(self):
        super().__init__()
        self.balance=None
        self.setFixedHeight(self.fontMetrics().height()+4)
        self.setToolTip(tr('pp2.system.contest_help'))
        self.setAccessibleName(tr('pp2.system.contest'))

    def set_values(self, reinforcement, undermining):
        valid=all(number(v) is not None and v>=0 for v in (reinforcement,undermining))
        if valid:
            total=reinforcement+undermining
            self.balance=(reinforcement-undermining)/total if total else 0
        else:
            self.balance=None
        self.setAccessibleDescription(tr('pp2.system.contest_help' if valid else 'pp2.system.missing'))
        self.update()

    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        margin=8;left=margin;right=max(left,self.width()-margin);middle=self.height()/2
        pen=QPen(self.palette().color(QPalette.Mid),2)
        if self.balance is None:pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(left,middle),QPointF(right,middle))
        for x,direction in ((left,1),(right,-1)):
            painter.drawLine(QPointF(x,middle),QPointF(x+direction*4,middle-4))
            painter.drawLine(QPointF(x,middle),QPointF(x+direction*4,middle+4))
        if self.balance is not None:
            position=(left+right)/2+self.balance*(right-left)/2
            painter.setBrush(self.palette().color(QPalette.WindowText))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(position,middle),3.5,3.5)


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
        layout.addWidget(label(tr('pp2.system.contest'),'muted'))
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
        layout.addLayout(contest)
        self.contest=ContestLine();layout.addWidget(self.contest)
        self.metrics=label()
        layout.addWidget(self.metrics)
        stages=QHBoxLayout();stages.setSpacing(4)
        self.stages={}
        for key in STAGES:
            stage=label('', 'muted');stage.setAlignment(Qt.AlignCenter)
            stage.setToolTip(tr('pp2.system.stage_help',status=tr('pp2.status.'+key)))
            self.stages[key]=stage;stages.addWidget(stage,1)
        layout.addLayout(stages)

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
        for key,stage in self.stages.items():
            active=key==status
            stage.setText(tr('pp2.status.'+key)+'\n'+('▲' if active else ' '))
            self.style(stage,'sectionTitle' if active else 'muted')
        reinforcement=system.get('PowerplayStateReinforcement')
        undermining=system.get('PowerplayStateUndermining')
        self.strengths['reinforcement'].setText(fmt(reinforcement))
        self.strengths['undermining'].setText(fmt(undermining))
        self.contest.set_values(reinforcement,undermining)
        metrics=[]
        if status in ('exploited','fortified','stronghold'):
            value=system.get('PowerplayStateControlProgress')
            if number(value) is not None:
                metrics.append(tr('pp2.metric.control')+': '+fmt(value))
        elif status=='unoccupied':
            conflicts=system.get('PowerplayConflictProgress')
            for entry in conflicts if isinstance(conflicts,list) else []:
                if isinstance(entry,dict) and isinstance(entry.get('Power'),str) and number(entry.get('ConflictProgress')) is not None:
                    metrics.append(tr('pp2.metric.conflict',power=entry['Power'])+': '+fmt(entry['ConflictProgress']))
        self.metrics.setText(' · '.join(metrics));self.metrics.setVisible(bool(metrics))
        self.metrics.setToolTip(self.metrics.text() if status=='unoccupied' else
            tr('pp2.system.control_help')+'\nPowerplayStateControlProgress: '+str(system.get('PowerplayStateControlProgress',unknown)))
