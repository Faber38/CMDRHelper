#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import string
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = PROJECT_ROOT / "cmdrhelper" / "i18n"

sys.path.insert(0, str(PROJECT_ROOT))
from cmdrhelper.material_catalog import ENGLISH_FALLBACK_KEYS


def intentional_english_fallback(key, reference):
    """Only the validated new material keys may deliberately lack translations."""
    return key in ENGLISH_FALLBACK_KEYS and bool(reference.get(key, "").strip())


EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "venv",
    ".venv",
    "build",
    "dist",
    "release",
    "backup",
    "backups",
}

REFERENCE_LANGUAGE = "en"


def load_translation_file(path: Path) -> tuple[dict[str, str], list[str]]:
    """Evaluate the catalog's small declarative AST, never execute Python code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    translations = {}
    seen = set()
    duplicates = []
    initialized = False

    def value(node, local=None):
        local = local or {}
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(value(item, local) for item in node.elts)
        if isinstance(node, ast.Name):
            if node.id == "TRANSLATIONS":
                return translations
            if node.id in local:
                return local[node.id]
        if isinstance(node, ast.Subscript):
            return value(node.value, local)[value(node.slice, local)]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return value(node.left, local) + value(node.right, local)
        if isinstance(node, ast.GeneratorExp) and len(node.generators) == 1:
            generator = node.generators[0]
            if isinstance(generator.target, ast.Name) and not generator.ifs and not generator.is_async:
                return tuple(value(node.elt, dict(local, **{generator.target.id: item}))
                             for item in value(generator.iter, local))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "join" and len(node.args) == 1 and not node.keywords):
            separator = value(node.func.value, local)
            if isinstance(separator, str):
                return separator.join(value(node.args[0], local))
        raise ValueError(f"{path}:{node.lineno}: unsupported catalog expression")

    def define(key, text):
        if not isinstance(key, str) or not isinstance(text, str):
            raise ValueError(f"{path}: catalog keys and values must be strings")
        if key in seen:
            duplicates.append(key)
        seen.add(key)
        translations[key] = text

    def entries(node):
        if not isinstance(node, ast.Dict):
            raise ValueError(f"{path}:{node.lineno}: expected a literal dictionary")
        # Keep entries separate: literal_eval(dict) would lose duplicate keys.
        result = []
        for key, text in zip(node.keys, node.values):
            if key is None:
                raise ValueError(f"{path}:{node.lineno}: dictionary unpacking is unsupported")
            result.append((value(key), value(text)))
        return result

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # Module docstring.
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "TRANSLATIONS":
                items = entries(node.value)
                translations.clear()
                for key, text in items:
                    define(key, text)
                initialized = True
                continue
            if (initialized and isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name) and target.value.id == "TRANSLATIONS"):
                define(value(target.slice), value(node.value))
                continue
        if initialized and isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if (isinstance(call.func, ast.Attribute) and call.func.attr == "update"
                    and isinstance(call.func.value, ast.Name) and call.func.value.id == "TRANSLATIONS"
                    and len(call.args) == 1 and not call.keywords):
                for key, text in entries(call.args[0]):
                    define(key, text)
                continue
        raise ValueError(f"{path}:{node.lineno}: unsupported catalog statement")
    if not initialized:
        raise ValueError(f"{path}: Kein TRANSLATIONS-Dictionary gefunden.")
    return translations, duplicates


def discover_languages() -> dict[str, tuple[Path, dict[str, str], list[str]]]:
    languages: dict[str, tuple[Path, dict[str, str], list[str]]] = {}

    if not I18N_DIR.is_dir():
        raise FileNotFoundError(f"Sprachordner nicht gefunden: {I18N_DIR}")

    for path in sorted(I18N_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue

        try:
            translations, duplicates = load_translation_file(path)
        except ValueError:
            # Hilfs-/sonstige Python-Dateien im i18n-Ordner ignorieren,
            # solange sie kein TRANSLATIONS-Dictionary enthalten.
            source = path.read_text(encoding="utf-8", errors="replace")
            if "TRANSLATIONS" not in source:
                continue
            raise

        languages[path.stem] = (path, translations, duplicates)

    return languages


def iter_project_python_files():
    for path in PROJECT_ROOT.rglob("*.py"):
        rel = path.relative_to(PROJECT_ROOT)

        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue

        # Die Sprachdateien selbst enthalten keine verwendeten UI-Keys.
        if path.parent == I18N_DIR and path.name != "__init__.py":
            continue

        yield path


def find_used_translation_keys() -> tuple[set[str], list[tuple[str, int]]]:
    """
    Findet tr("literal.key") im Projekt.

    Dynamische Aufrufe wie tr(variable) können nicht zuverlässig geprüft werden
    und werden separat gemeldet.
    """
    keys: set[str] = set()
    dynamic_calls: list[tuple[str, int]] = []

    for path in iter_project_python_files():
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            print(f"[i18n] WARNUNG: {path}: konnte nicht analysiert werden: {exc}")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func
            is_tr = isinstance(func, ast.Name) and func.id in ("tr", "tr_for_language")

            if not is_tr:
                continue

            position = 1 if func.id == "tr_for_language" else 0
            if len(node.args) <= position:
                dynamic_calls.append((str(path.relative_to(PROJECT_ROOT)), node.lineno))
                continue

            first = node.args[position]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                keys.add(first.value)
            else:
                dynamic_calls.append((str(path.relative_to(PROJECT_ROOT)), node.lineno))

    return keys, dynamic_calls


def format_fields(text: str) -> tuple[tuple[str, str, str], ...]:
    """Validate keyword-format syntax and retain specs, conversions and repeats."""
    import _string
    fields = []

    def parse(template, depth=0):
        if depth > 1:
            raise ValueError("Format specification nesting is too deep")
        for _, field, spec, conversion in string.Formatter().parse(template):
            if field is None:
                continue
            root, access = _string.formatter_field_name_split(field)
            list(access)  # Validate attribute/index syntax, including lazy errors.
            if not isinstance(root, str) or not root.isidentifier():
                raise ValueError("Only named keyword fields are supported")
            if conversion not in (None, "s", "r", "a"):
                raise ValueError("Invalid format conversion")
            fields.append((field, spec, conversion or ""))
            if "{" in spec or "}" in spec:
                parse(spec, depth + 1)
            # Validate the format grammar with representative builtin values.
            # Argument types are checked at their call sites, not guessed here.
            probe = "".join(literal + ("1" if name is not None else "")
                            for literal, name, _, _ in string.Formatter().parse(spec))
            # !s/!r/!a convert to strings before the specification is applied.
            for sample in (("text",) if conversion else (0, 0.0, "text")):
                try:
                    format(sample, probe)
                    break
                except (ValueError, TypeError):
                    pass
            else:
                raise ValueError("Invalid format specification: " + spec)
    parse(text)
    return tuple(sorted(fields))


def placeholders(text: str) -> set[str]:
    """Compatibility API for callers interested only in argument names."""
    return {re.split(r"[.\[]", field, maxsplit=1)[0]
            for field, _, _ in format_fields(text)}


def main() -> int:
    print()
    print("=" * 68)
    print(" CMDRHelper – i18n-Prüfung")
    print("=" * 68)

    try:
        languages = discover_languages()
    except Exception as exc:
        print(f"✗ Sprachdateien konnten nicht geprüft werden: {exc}")
        print("=" * 68)
        return 1

    if not languages:
        print("✗ Keine Sprachdateien gefunden.")
        print("=" * 68)
        return 1

    if REFERENCE_LANGUAGE not in languages:
        print(f"✗ Referenzsprache '{REFERENCE_LANGUAGE}.py' wurde nicht gefunden.")
        print("=" * 68)
        return 1

    ref_path, reference, _ = languages[REFERENCE_LANGUAGE]
    ref_keys = set(reference)

    used_keys, dynamic_calls = find_used_translation_keys()

    problems = 0

    print(
        f"Sprachen: {len(languages)}  |  "
        f"Referenz: {ref_path.name} ({len(reference)} Keys)  |  "
        f"verwendete tr()-Keys: {len(used_keys)}"
    )
    print()

    # 1. Doppelte Keys
    duplicate_found = False
    for code, (path, translations, duplicates) in languages.items():
        if not duplicates:
            continue
        if not duplicate_found:
            print("DOPPELTE KEYS")
            duplicate_found = True
        print(f"  ✗ {path.name}:")
        for key in sorted(set(duplicates)):
            print(f"      {key}")
            problems += 1

    if duplicate_found:
        print()

    for code, (path, translations, _) in languages.items():
        for key, text in translations.items():
            if not text.strip():
                print(f"✗ {path.name}: leerer Text: {key}")
                problems += 1
            try:
                format_fields(text)
            except ValueError as exc:
                print(f"✗ {path.name}: ungültiges Format: {key}: {exc}")
                problems += 1

    # 2. Fehlende/zusätzliche Keys gegenüber Englisch
    mismatch_found = False
    for code, (path, translations, _) in languages.items():
        lang_keys = set(translations)
        fallback = {key for key in ref_keys - lang_keys
                    if intentional_english_fallback(key, reference)}
        if fallback:
            print(f"  {path.name}: {len(fallback)} Materialnamen mit englischem Fallback")
        missing = sorted(ref_keys - lang_keys - fallback)
        extra = sorted(lang_keys - ref_keys)

        if not missing and not extra:
            continue

        if not mismatch_found:
            print("KEY-ABWEICHUNGEN GEGENÜBER ENGLISCH")
            mismatch_found = True

        print(f"  {path.name}:")

        for key in missing:
            print(f"      ✗ fehlt: {key}")
            problems += 1

        for key in extra:
            print(f"      ! nur hier vorhanden: {key}")
            problems += 1

    if mismatch_found:
        print()

    # 3. Im Quellcode verwendete Keys, die in Sprachdateien fehlen
    missing_used_found = False
    for key in sorted(used_keys):
        missing_in = [
            code for code, (_, translations, _) in languages.items()
            if key not in translations and not intentional_english_fallback(key, reference)
        ]

        if not missing_in:
            continue

        if not missing_used_found:
            print("IM PROGRAMM VERWENDETE KEYS MIT FEHLENDEN ÜBERSETZUNGEN")
            missing_used_found = True

        print(f"  ✗ {key}")
        print(f"      fehlt in: {', '.join(missing_in)}")
        problems += len(missing_in)

    if missing_used_found:
        print()

    # 4. Platzhalter vergleichen
    placeholder_found = False
    for code, (path, translations, _) in languages.items():
        if code == REFERENCE_LANGUAGE:
            continue

        common_keys = ref_keys & set(translations)

        for key in sorted(common_keys):
            try:
                expected = format_fields(reference[key])
                actual = format_fields(translations[key])
            except ValueError:
                continue  # Already reported during the per-catalog validation.

            if expected == actual:
                continue

            if not placeholder_found:
                print("PLATZHALTER-ABWEICHUNGEN")
                placeholder_found = True

            print(f"  ✗ {path.name}: {key}")
            print(f"      Englisch: {sorted(expected)}")
            print(f"      {code}: {sorted(actual)}")
            problems += 1

    if placeholder_found:
        print()

    # 5. Dynamische tr()-Aufrufe sind kein Fehler, aber Hinweis
    if dynamic_calls:
        print("HINWEIS: DYNAMISCHE tr()-AUFRUFE")
        print("  Diese Aufrufe können nicht automatisch auf konkrete Keys geprüft werden:")
        for filename, lineno in dynamic_calls[:20]:
            print(f"      {filename}:{lineno}")
        if len(dynamic_calls) > 20:
            print(f"      … und {len(dynamic_calls) - 20} weitere")
        print()

    if problems:
        print(f"✗ i18n-Prüfung: {problems} Problem(e) gefunden.")
        print("  CMDRHelper kann trotzdem gestartet werden.")
        print("=" * 68)
        print()
        return 1

    print(
        f"✓ i18n: {len(ref_keys)} Referenz-Keys in {len(languages)} Sprachen geprüft "
        "(einschließlich ausgewiesener englischer Material-Fallbacks)"
    )
    print("✓ Platzhalter stimmen überein")
    print("✓ Keine doppelten Keys gefunden")
    print("=" * 68)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
