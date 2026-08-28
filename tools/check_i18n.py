#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import string
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = PROJECT_ROOT / "cmdrhelper" / "i18n"

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "venv",
    ".venv",
    "build",
    "dist",
}

REFERENCE_LANGUAGE = "en"


def load_translation_file(path: Path) -> tuple[dict[str, str], list[str]]:
    """Liest TRANSLATIONS sicher per AST und erkennt doppelte Dictionary-Keys."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    translations: dict[str, str] | None = None
    duplicate_keys: list[str] = []

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        if not any(isinstance(target, ast.Name) and target.id == "TRANSLATIONS" for target in node.targets):
            continue

        if not isinstance(node.value, ast.Dict):
            raise ValueError(f"{path}: TRANSLATIONS ist kein Dictionary.")

        seen: set[str] = set()

        for key_node in node.value.keys:
            if key_node is None:
                continue
            try:
                key = ast.literal_eval(key_node)
            except Exception:
                continue
            if isinstance(key, str):
                if key in seen:
                    duplicate_keys.append(key)
                seen.add(key)

        value = ast.literal_eval(node.value)
        if not isinstance(value, dict):
            raise ValueError(f"{path}: TRANSLATIONS ist kein Dictionary.")
        translations = value
        break

    if translations is None:
        raise ValueError(f"{path}: Kein TRANSLATIONS-Dictionary gefunden.")

    bad_entries = [
        key for key, value in translations.items()
        if not isinstance(key, str) or not isinstance(value, str)
    ]
    if bad_entries:
        raise ValueError(
            f"{path}: Nicht unterstützte Einträge in TRANSLATIONS: {bad_entries[:5]}"
        )

    return translations, duplicate_keys


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
            is_tr = isinstance(func, ast.Name) and func.id == "tr"

            if not is_tr:
                continue

            if not node.args:
                dynamic_calls.append((str(path.relative_to(PROJECT_ROOT)), node.lineno))
                continue

            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                keys.add(first.value)
            else:
                dynamic_calls.append((str(path.relative_to(PROJECT_ROOT)), node.lineno))

    return keys, dynamic_calls


def placeholders(text: str) -> set[str]:
    result: set[str] = set()

    try:
        parsed = string.Formatter().parse(text)
    except ValueError:
        return {"<UNGÜLTIGES FORMAT>"}

    for _, field_name, _, _ in parsed:
        if not field_name:
            continue

        # Beispiel: {value:.1f}, {obj.name}, {items[0]}
        clean = re.split(r"[.\[]", field_name, maxsplit=1)[0]
        result.add(clean)

    return result


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

    # 2. Fehlende/zusätzliche Keys gegenüber Englisch
    mismatch_found = False
    for code, (path, translations, _) in languages.items():
        lang_keys = set(translations)
        missing = sorted(ref_keys - lang_keys)
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
            if key not in translations
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
            expected = placeholders(reference[key])
            actual = placeholders(translations[key])

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
        f"✓ i18n: {len(ref_keys)} Keys vollständig in "
        f"{len(languages)} Sprachen"
    )
    print("✓ Platzhalter stimmen überein")
    print("✓ Keine doppelten Keys gefunden")
    print("=" * 68)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
