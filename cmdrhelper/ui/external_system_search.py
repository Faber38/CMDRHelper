"""Explicit, asynchronous external search; windows never follow live game state."""
import json
from copy import deepcopy
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot, Qt, QEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel
from cmdrhelper.external_system import search_system
from cmdrhelper.i18n import tr
from .system_overview import SystemOverviewDialog
from .body_detail_window import BodyDetailWindow


def source_text(source):
    return str(source).replace('Local', tr('external.local'))


def label(text):
    widget = QLabel(text)
    widget.setTextFormat(Qt.PlainText)
    widget.setWordWrap(True)
    return widget


class ExternalBodyDetail(BodyDetailWindow):
    def __init__(self, body, parent=None):
        super().__init__(body, parent, planning=True)
        self.setWindowFlags((self.windowFlags() | Qt.WindowMinMaxButtonsHint) & ~Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # External strings must not become rich text.
        for widget in self.findChildren(QLabel):
            widget.setTextFormat(Qt.PlainText)

    def _source_text(self):
        return tr('external.source', source=source_text(self.body.get('source','')))

    def _add_explorer_rows(self, form):
        observations = self.body.get('observations') or []
        shown = False
        for item in observations:
            facts = []
            if item.get('scanned'):
                facts.append(tr('external.scanned'))
            if item.get('self_mapped'):
                facts.append(tr('external.mapped'))
            if facts:
                name = item.get('current_name') or str(item['commander_id'])
                self._add_row(form, f"{name} (#{item['commander_id']})", ' · '.join(facts) + '\n' + (item.get('last_seen') or ''))
                shown = True
        if not shown:
            self._add_row(form, tr('external.observations'), tr('common.unknown'))
        for item in self.body.get('mining_findings') or []:
            quantity = str(item['quantity']) + (' t' if item['kind']=='surface_mining_commodities' else '')
            self._add_row(form, tr('body_detail.own_mining_findings'),
                          f"{item.get('current_name') or item['commander_id']}: {item.get('display_name') or item['frontier_name']} · {quantity}")

    def _add_body_rows(self, form):
        fields = [('planet_class','body_detail.body_type',''), ('landable','body_detail.landable',''),
                  ('atmosphere','body_detail.atmosphere',''), ('gravity_g','body_detail.gravity',' g'),
                  ('surface_temperature','external.temperature',' K'), ('volcanism','external.volcanism',''),
                  ('geological_signals','body_detail.geo_signals',''),
                  ('planetary_mining_signals','body_detail.planetary_mining_signals','')]
        for key,title,unit in fields:
            value = self.body.get(key)
            if key == 'planet_class' and not value:
                value = self.body.get('star_type') or self.body.get('body_type')
            if value is None or value == '':
                rendered = tr('common.unknown')
            elif type(value) is bool:
                rendered = self._yes_no(value)
            elif isinstance(value,(int,float)):
                rendered = f'{value:.6g}' + unit
            else:
                rendered = str(value)
            source = self.body.get('provenance',{}).get(key)
            if source:
                rendered += '\n' + source_text(source)
            self._add_row(form, tr(title), rendered)
        for key, alternatives in self.body.get('conflicts',{}).items():
            titles = dict((k,t) for k,t,_ in fields)
            title = tr(titles[key]) if key in titles else tr('external.hierarchy') if 'parent' in key else tr('external.conflicts')
            material = key.removeprefix('materials.') if key.startswith('materials.') else None
            if material:
                title = tr('body_detail.surface_materials') + ' · ' + self._material_name(material)
            chosen_source = self.body.get('material_sources',{}).get(material) if material else self.body.get('provenance',{}).get(key)
            chosen_value = self.body.get('materials',{}).get(material) if material else self.body.get(key)
            primary = next((r for r in self.body['source_records'] if r.get('source') == chosen_source), {})
            values = [dict(source=chosen_source or '',value=chosen_value,unit=self.body.get('material_units',{}).get(material),updated_at=primary.get('updated_at'))] + alternatives
            self._add_row(form, tr('external.conflicts') + ' · ' + title, '\n'.join(
                f"{source_text(v['source'])} · {v.get('updated_at') or tr('common.unknown')}: "
                + (tr('external.units') if material and v.get('unit') != 'percent'
                   else json.dumps(v['value'],ensure_ascii=False) + (' %' if material else '')) for v in values))
        for entry in self.body.get('geology') or []:
            self._add_row(form, tr('body_detail.found_geo_types'),
                          f"{entry.get('current_name') or entry['commander_id']}: {entry.get('name') or entry.get('raw_name')}")
        self._add_row(form, '', tr('external.notice'))

    def _add_material_rows(self, form):
        materials = self.body.get('materials') or {}
        if not materials:
            self._add_row(form, '', tr('common.unknown'))
            return
        unknown_units = False
        for material, amount in sorted(materials.items()):
            unit = self.body.get('material_units',{}).get(material, self.body.get('material_unit'))
            source = self.body.get('material_sources',{}).get(material, self.body.get('provenance',{}).get('materials',''))
            if unit == 'percent':
                value = f'{amount:.2f} %'
            else:
                value = '—'
                unknown_units = True
            self._add_row(form, self._material_name(material), value + ' · ' + source_text(source))
        if unknown_units:
            self._add_row(form, '', tr('external.units'))


class ExternalSystemWindow(SystemOverviewDialog):
    def __init__(self, model, parent=None, *, light=False):
        self.model = deepcopy(model)
        self.details = []
        super().__init__(model['system'], model['bodies'], self.open_body, parent,
                         light=light, system_address=model['system_address'], stations=model['stations'])
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.spansh_button.hide()
        self.spansh_status.hide()
        for widget in self.findChildren(QLabel):
            widget.setTextFormat(Qt.PlainText)
        info = tr('external.source', source=source_text(model['sources']))
        info += f" · {len(model['bodies'])} / {model.get('body_count') if model.get('body_count') is not None else '?'}"
        if model.get('partial') or model.get('warning'):
            info += '\n' + tr('external.partial')
        if model.get('source_updated_at'):
            info += '\n' + model['source_updated_at']
        self.layout().insertWidget(1,label(info))
        self.layout().insertWidget(2,label('✓ ' + tr('body_detail.landable') + ' · ' + tr('external.notice')))
        if not model.get('edsm_used'):
            self.layout().insertWidget(3,label(tr('external.edsm_skip')))

    def open_body(self, body):
        window = ExternalBodyDetail(body,self)
        self.details.append(window)
        window.destroyed.connect(lambda: self.details.remove(window) if window in self.details else None)
        window.show()

    def closeEvent(self, event):
        for window in list(self.details):
            window.close()
        super().closeEvent(event)


class SearchSignals(QObject):
    finished = Signal(int, object, str)


class SearchWorker(QRunnable):
    def __init__(self, token, state, name, database_path, provider):
        super().__init__()
        # The pool owns the runnable until run() returns. The GUI may receive
        # finished before that return, so it must never delete the worker.
        self.setAutoDelete(True)
        self.signals = SearchSignals()
        self.token,self.state,self.name,self.path,self.provider = token,state,name,database_path,provider

    def run(self):
        model,error = None,''
        try:
            try:
                if self.state['token'] == self.token:
                    model = self.provider(self.name,self.path)
            except Exception as exc:
                error = getattr(exc,'code','network_error')
            self.signals.finished.emit(self.token,model,error)
        finally:
            # This QObject belongs to the GUI thread, independently of the
            # runnable. Queued delivery carries the result, not the worker.
            # Cleanup must also work when the receiver has been destroyed.
            self.signals.deleteLater()


class ExternalSystemSearch(QWidget):
    def __init__(self, owner, database_path, *, provider=search_system, pool=None):
        super().__init__(owner)
        self.owner,self.database_path,self.provider = owner,database_path,provider
        self.pool = pool or QThreadPool.globalInstance()
        self.request_state = {'token':0}
        self.workers,self.windows = {},[]
        self.pending_name = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(3)
        self.heading = label(tr('external.title'))
        self.heading.setObjectName('sectionTitle')
        root.addWidget(self.heading)
        row = QHBoxLayout()
        self.edit = QLineEdit()
        caption = label(tr('external.search'))
        caption.setBuddy(self.edit)
        row.addWidget(caption)
        row.addWidget(self.edit,1)
        self.button = QPushButton(tr('external.go'))
        row.addWidget(self.button)
        root.addLayout(row)
        self.status = label('')
        self.status.hide()
        root.addWidget(self.status)
        self.button.clicked.connect(self.start_search)
        self.edit.returnPressed.connect(self.start_search)
        state, workers = self.request_state, self.workers
        def discard_pending():
            state.update(token=-1)
            workers.clear()  # Running jobs remain owned by the threadpool.
        self.destroyed.connect(discard_pending)
        self.owner.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self.owner and event.type() == QEvent.Close:
            # Keep tokens monotonic if the owner is subsequently shown again.
            self.request_state['token'] += 1
            self.workers.clear()
            self.pending_name = None
        return super().eventFilter(watched, event)

    def start_search(self):
        name = self.edit.text().strip()
        if not name or (self.pending_name == name.casefold() and self.request_state['token'] in self.workers):
            return
        self.pending_name = name.casefold()
        self.request_state['token'] += 1
        token = self.request_state['token']
        worker = SearchWorker(token,self.request_state,name,self.database_path,self.provider)
        self.workers[token] = worker
        worker.signals.finished.connect(self.finished)
        self.status.setText(tr('external.loading'))
        self.status.show()
        self.pool.start(worker)

    @Slot(int,object,str)
    def finished(self, token, model, error):
        self.workers.pop(token,None)
        if token != self.request_state['token']:
            return
        self.pending_name = None
        if error or model is None:
            self.status.setText(tr('external.unknown' if error=='system_unknown' else 'external.error'))
            return
        self.status.hide()
        window = ExternalSystemWindow(model,self.owner,light=getattr(self.owner,'ui_theme','dark')=='light')
        self.windows.append(window)
        window.destroyed.connect(lambda: self.windows.remove(window) if window in self.windows else None)
        window.show()

    def set_light_mode(self, light):
        for window in self.windows:
            window.set_light_mode(light)
