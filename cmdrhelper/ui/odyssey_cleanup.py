"""Commander-local display preferences; never mutates Odyssey inventories."""
import json
from urllib.parse import quote

from PySide6.QtCore import QCollator, QLocale, Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
                              QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
                              QVBoxLayout)

from cmdrhelper.i18n import get_language, tr
from cmdrhelper.odyssey_catalog import all_materials, localized_name


# Exactly the 81 entries supplied in odyssey_aufraeumliste.txt.txt (2026-10-12).
# Matched by English name AND catalog category; use only Frontier symbols at runtime.
DEFAULT_SYMBOLS = frozenset({
    'accidentlogs',  # Accident Logs
    'axcombatlogs',  # AX Combat Logs
    'biologicalweapondata',  # Biological Weapon Data
    'blacklistdata',  # Blacklist Data
    'campaignplans',  # Campaign Plans
    'censusdata',  # Census Data
    'chemicalweapondata',  # Chemical Weapon Data
    'conflicthistory',  # Conflict History
    'criminalrecords',  # Criminal Records
    'cropyieldanalysis',  # Crop Yield Analysis
    'dutyrota',  # Duty Rota
    'employeedirectory',  # Employee Directory
    'employeeexpenses',  # Employee Expenses
    'employmenthistory',  # Employment History
    'enhancedinterrogationrecordings',  # Enhanced Interrogation Recordings
    'explorationjournals',  # Exploration Journals
    'factiondonatorlist',  # Faction Donator List
    'factionnews',  # Faction News
    'geologicaldata',  # Geological Data
    'hydroponicdata',  # Hydroponic Data
    'incidentlogs',  # Incident Logs
    'influenceprojections',  # Influence Projections
    'internalcorrespondence',  # Internal Correspondence
    'interrogationrecordings',  # Interrogation Recordings
    'interviewrecordings',  # Interview Recordings
    'jobapplications',  # Job Applications
    'kompromat',  # Kompromat
    'literaryfiction',  # Literary Fiction
    'meetingminutes',  # Meeting Minutes
    'networkaccesshistory',  # Network Access History
    'networksecurityprotocols',  # Network Security Protocols
    'nextofkinrecords',  # Next of Kin Records
    'patienthistory',  # Patient History
    'payrollinformation',  # Payroll Information
    'personallogs',  # Personal Logs
    'photoalbums',  # Photo Albums
    'plantgrowthcharts',  # Plant Growth Charts
    'politicalaffiliations',  # Political Affiliations
    'prisonerlogs',  # Prisoner Logs
    'propaganda',  # Propaganda
    'purchaserecords',  # Purchase Records
    'purchaserequests',  # Purchase Requests
    'residentialdirectory',  # Residential Directory
    'salesrecords',  # Sales Records
    'seedgeneaology',  # Seed Geneaology
    'shareholderinformation',  # Shareholder Information
    'slushfundlogs',  # Slush Fund Logs
    'spyware',  # Spyware
    'taxrecords',  # Tax Records
    'travelpermits',  # Travel Permits
    'agriculturalprocesssample',  # Agricultural Process Sample
    'biochemicalagent',  # Biochemical Agent
    'buildingschematic',  # Building Schematic
    'californium',  # Californium
    'castfossil',  # Cast Fossil
    'chemicalprocesssample',  # Chemical Process Sample
    'chemicalsample',  # Chemical Sample
    'compactlibrary',  # Compact Library
    'sabotagedcomponent',  # Contaminated Spire Refinery Compound
    'deepmantlesample',  # Deep Mantle Sample
    'degradedpowerregulator',  # Degraded Power Regulator
    'hush',  # Hush
    'inertiacanister',  # Inertia Canister
    'infinity',  # Infinity
    'inorganiccontaminant',  # Inorganic Contaminant
    'insight',  # Insight
    'insightdatabank',  # Insight Data Bank
    'lazarus',  # Lazarus
    'microbialinhibitor',  # Microbial Inhibitor
    'mutageniccatalyst',  # Mutagenic Catalyst
    'nutritionalconcentrate',  # Nutritional Concentrate
    'personalcomputer',  # Personal Computer
    'personaldocuments',  # Personal Documents
    'petrifiedfossil',  # Petrified Fossil
    'pyrolyticcatalyst',  # Pyrolytic Catalyst
    'refinementprocesssample',  # Refinement Process Sample
    'shipschematic',  # Ship Schematic
    'biomechanicalcomponent',  # Spire Refinery Compound
    'syntheticgenome',  # Synthetic Genome
    'syntheticpathogen',  # Synthetic Pathogen
    'trueformfossil',  # True Form Fossil
})
KNOWN_SYMBOLS = frozenset(m.symbol for m in all_materials())
GROUPS = ("Items", "Data", "Chemicals", "Circuits", "Tech", "Consumables")


def selection_key(commander_id, fid):
    if isinstance(fid, str) and fid.strip():
        identity = "fid/" + quote(fid.strip(), safe="")
    elif isinstance(commander_id, int) and commander_id > 0:
        identity = "commander/" + str(commander_id)
    else:
        return None
    return "materials/odyssey/cleanup/" + identity


def load_selection(settings, key):
    fallback = DEFAULT_SYMBOLS
    if key is None or not settings.contains(key):
        return fallback
    try:
        symbols = json.loads(settings.value(key))
        if isinstance(symbols, list) and all(isinstance(s, str) for s in symbols):
            return frozenset(symbols) & KNOWN_SYMBOLS
    except (TypeError, ValueError):
        pass
    return fallback


def save_selection(settings, key, symbols):
    if key is None:
        raise ValueError("A commander identity is required")
    settings.setValue(key, json.dumps(sorted(set(symbols) & KNOWN_SYMBOLS)))
    settings.sync()
    if settings.status() != settings.Status.NoError:
        raise OSError("Could not save cleanup selection")


class OdysseyCleanupDialog(QDialog):
    """Edits a private draft. Only the owning view persists accepted changes."""

    def __init__(self, selected, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("odyssey.cleanup.manage"))
        self.resize(600, 650)
        layout = QVBoxLayout(self)
        hint = QLabel(tr("odyssey.cleanup.personal"))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("materials.search"))
        self.search.setAccessibleName(tr("materials.search"))
        controls.addWidget(self.search, 1)
        self.filter = QComboBox()
        for key in ("all", "marked", "unmarked"):
            self.filter.addItem(tr("materials.all" if key == "all" else "odyssey.cleanup." + key), key)
        self.filter.setAccessibleName(tr("materials.filter"))
        controls.addWidget(self.filter)
        layout.addLayout(controls)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        layout.addWidget(self.tree, 1)
        self.items, self.groups, self.search_names = {}, {}, {}
        collator = QCollator(QLocale(get_language()))
        for group in GROUPS:
            key = ("odyssey." + group.lower() if group in ("Items", "Data", "Consumables")
                   else "odyssey.cleanup." + group.lower())
            parent_item = QTreeWidgetItem(self.tree, [tr(key)])
            self.groups[group] = parent_item
            materials = [m for m in all_materials() if (m.subgroup or m.category) == group]
            for material in sorted(materials, key=lambda m: collator.sortKey(localized_name(m.symbol))):
                name = localized_name(material.symbol)
                item = QTreeWidgetItem(parent_item, [name])
                item.setData(0, Qt.ItemDataRole.UserRole, material.symbol)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked if material.symbol in selected else Qt.CheckState.Unchecked)
                item.setToolTip(0, material.name_en)
                self.items[material.symbol] = item
                self.search_names[material.symbol] = (name + "\n" + material.name_en).casefold()
            parent_item.setExpanded(True)
        self.count = QLabel()
        layout.addWidget(self.count)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton(tr("odyssey.cleanup.reset"))
        self.reset_button.clicked.connect(self.restore_defaults)
        buttons.addWidget(self.reset_button)
        buttons.addStretch()
        self.cancel_button = QPushButton(tr("planet_nav.cancel"))
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.save_button = QPushButton(tr("favorites.save"))
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.accept)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)
        self.search.textChanged.connect(self.refresh)
        self.filter.currentIndexChanged.connect(self.refresh)
        self.tree.itemChanged.connect(self.refresh)
        self.refresh()

    def selected_symbols(self):
        return frozenset(symbol for symbol, item in self.items.items()
                         if item.checkState(0) == Qt.CheckState.Checked)

    def refresh(self, *_):
        selected = self.selected_symbols()
        query, mode = self.search.text().strip().casefold(), self.filter.currentData()
        for symbol, item in self.items.items():
            item.setHidden((bool(query) and query not in self.search_names[symbol])
                           or (mode == "marked" and symbol not in selected)
                           or (mode == "unmarked" and symbol in selected))
        for group in self.groups.values():
            group.setHidden(all(group.child(i).isHidden() for i in range(group.childCount())))
        self.count.setText(tr("odyssey.cleanup.count", count=len(selected), total=len(self.items)))

    def restore_defaults(self):
        confirmation = QMessageBox(QMessageBox.Icon.Question, tr("odyssey.cleanup.reset"),
                                   tr("odyssey.cleanup.confirm"),
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        confirmation.button(QMessageBox.StandardButton.Yes).setText(tr("common.yes"))
        confirmation.button(QMessageBox.StandardButton.No).setText(tr("common.no"))
        confirmation.setDefaultButton(QMessageBox.StandardButton.No)
        answer = confirmation.exec()
        confirmation.deleteLater()
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.tree.blockSignals(True)
        try:
            for symbol, item in self.items.items():
                item.setCheckState(0, Qt.CheckState.Checked if symbol in DEFAULT_SYMBOLS else Qt.CheckState.Unchecked)
        finally:
            self.tree.blockSignals(False)
        self.refresh()
