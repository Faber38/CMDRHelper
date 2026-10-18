"""Journal source configuration. Paths are provenance, never commander identity."""
from dataclasses import asdict, dataclass, field, replace
import json
from pathlib import Path
import uuid


KEY = 'journal_sources/v1'


def canonical(path):
    return str(Path(path).expanduser().resolve())


@dataclass
class JournalSource:
    id: str
    name: str
    path: str
    canonical_path: str
    enabled: bool = True
    origin: str = 'manual'
    # Observations are deliberately not restored as current identity proof.
    status: str = 'unknown'
    identities: list = field(default_factory=list)

    def config(self):
        value = asdict(self)
        value.pop('status')
        value.pop('identities')
        return value


def discover(home=None):
    """Bounded prefix discovery; never recurse through Wine symlink trees."""
    from .journal_reader import default_journal_paths
    home = Path(home) if home is not None else Path.home()
    candidates = [(p, 'Steam') for p in default_journal_paths()]
    bases = [home / 'Games/Heroic/Prefixes', home / '.config/heroic/Prefixes']
    for base in bases:
        if not base.is_dir():
            continue
        # Heroic uses both Prefixes/<game> and Prefixes/default/<game>.
        prefixes = list(base.iterdir())
        default = base / 'default'
        if default.is_dir():
            prefixes += list(default.iterdir())
        for prefix in prefixes:
            for users in (prefix / 'drive_c/users', prefix / 'pfx/drive_c/users'):
                if not users.is_dir():
                    continue
                for user in users.iterdir():
                    candidates.append((user / 'Saved Games/Frontier Developments/Elite Dangerous', 'Heroic / Epic'))
    found = {}
    for path, name in candidates:
        try:
            # A prefix directory alone is not evidence of a journal source.
            if path.is_dir() and any(path.glob('Journal.*.log')):
                found.setdefault(canonical(path), (str(path), name))
        except OSError:
            continue
    return list(found.values())


class SourceRegistry:
    def __init__(self, settings, candidates=()):
        self.settings = settings
        self.sources = []
        raw = settings.value(KEY, None)
        if raw is not None:
            rows = json.loads(str(raw))
            if not isinstance(rows, list):
                raise ValueError('Invalid journal source configuration')
            for row in rows:
                source = JournalSource(**row)
                if not source.id or not source.path or source.origin not in ('manual', 'automatic'):
                    raise ValueError('Invalid journal source configuration')
                if any(s.id == source.id for s in self.sources):
                    raise ValueError('Duplicate journal source ID')
                source.canonical_path = canonical(source.path)
                if any(s.canonical_path == source.canonical_path for s in self.sources):
                    raise ValueError('Duplicate journal source alias')
                self.sources.append(source)
        else:
            legacy = settings.value('journal_folder', '')
            if legacy:
                self.add(str(legacy), Path(str(legacy)).name, save=False)
            self.merge(candidates, save=False)
            self.save()

    def save(self):
        self.settings.setValue(KEY, json.dumps([s.config() for s in self.sources]))
        self.settings.sync()

    def add(self, path, name='', *, origin='manual', save=True):
        normalized = canonical(path)
        for source in self.sources:
            if canonical(source.path) == normalized:
                return source
        # Preserve the original spelling for existing database path keys.
        source = JournalSource(uuid.uuid4().hex, name or Path(path).name,
                               str(Path(path).expanduser().absolute()), normalized, origin=origin)
        self.sources.append(source)
        if save:
            self.save()
        return source

    def merge(self, candidates, *, save=True):
        for path, name in candidates:
            self.add(path, name, origin='automatic', save=False)
        if save:
            self.save()

    def update(self, source_id, *, name=None, path=None, enabled=None):
        original = self.get(source_id)
        source = replace(original, identities=list(original.identities))
        if path is not None:
            normalized = canonical(path)
            if any(s.id != source_id and canonical(s.path) == normalized for s in self.sources):
                raise ValueError('Duplicate journal source alias')
            if normalized != source.canonical_path:
                # Stable configuration identity; historical file keys remain
                # unchanged and upload positions also include the full path.
                source.path = str(Path(path).expanduser().absolute())
                source.canonical_path = normalized
                source.identities = []
                source.status = 'unknown'
        if name is not None:
            source.name = str(name)
        if enabled is not None:
            source.enabled = bool(enabled)
        self.sources[self.sources.index(original)] = source
        self.save()
        return source

    def remove(self, source_id):
        self.sources = [s for s in self.sources if s.id != source_id]
        self.save()

    def get(self, source_id):
        return next(s for s in self.sources if s.id == source_id)

    def enabled(self):
        seen = set()
        result = []
        for source in self.sources:
            source.canonical_path = canonical(source.path)
            if not source.enabled:
                source.status = 'disabled'
            elif source.canonical_path in seen:
                source.status = 'duplicate'
            else:
                seen.add(source.canonical_path)
                result.append(source)
        return result
