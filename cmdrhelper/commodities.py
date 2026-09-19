"""Shared Frontier commodity token normalization and display localization.

Journal-localized labels take precedence; untranslated commodities retain their
readable token. The catalog uses the application's normal twelve-language i18n.
"""
from cmdrhelper.i18n import tr


def commodity_key(value):
    value = str(value or '').strip().strip('$').rstrip(';')
    if value.lower().endswith('_name'):
        value = value[:-5]
    return value.replace('_', '').replace(' ', '').casefold()


def commodity_name(value, localized=''):
    if localized:
        return localized
    key = 'commodity.' + commodity_key(value)
    translated = tr(key)
    if translated != key:
        return translated
    raw = str(value or '').strip().lstrip('$').rstrip(';')
    if raw.lower().endswith('_name'):
        raw = raw[:-5]
    return raw.replace('_', ' ')
