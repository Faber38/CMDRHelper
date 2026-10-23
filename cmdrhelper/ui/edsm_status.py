"""Upload-only presentation; no network, persistence or raw backend text."""
import re

from cmdrhelper.i18n import tr


def error_detail(message):
    """Translate known backend messages, never reflect arbitrary error text.

    Free-form errors may contain credentials, paths or server payloads. Only a
    bounded HTTP/API code may pass through; all other output is catalog text.
    """
    message = str(message or "")
    if message == "EDSM-Wiederholung pausiert (Netzwerk/Rate-Limit).":
        return tr('edsm_service.retry')
    if message in ("Zeitüberschreitung bei EDSM.",
                   "Zeitüberschreitung beim EDSM-Upload.",
                   "Zeitüberschreitung bei der EDSM-Anfrage."):
        return tr('edsm_service.timeout')
    if message == "EDSM nicht erreichbar." or message.startswith("EDSM nicht erreichbar: "):
        return tr('edsm_service.transport')
    for pattern, key in (
        (r'EDSM HTTP-Fehler ([1-5][0-9]{2})\.', 'edsm_service.http'),
        (r'EDSM: Upload abgelehnt \(Code ([1-5][0-9]{2})\)', 'edsm_service.api'),
    ):
        match = re.fullmatch(pattern, message)
        if match:
            return tr(key, code=match.group(1))
    if message == "EDSM hat nicht alle Ereignisse bestätigt.":
        return tr('edsm_service.partial_reply')
    if message in ("EDSM lieferte eine unerwartete Antwort.",
                   "EDSM lieferte eine unerwartete Discard-Liste.",
                   "EDSM hat keine gültige JSON-Antwort geliefert."):
        return tr('edsm_service.invalid_reply')
    return tr('edsm_service.unknown_error')


def presentation(state):
    """Only confirmed journal transfers can make the indicator green."""
    enabled = bool(getattr(state, 'edsm_enabled', False))
    status = getattr(state, 'edsm_upload_status', 'unknown')
    details = getattr(state, 'edsm_upload_details', {})
    count = details.get('confirmed', 0)
    count = count if type(count) is int and count > 0 else 0
    key, style = 'topbar.edsm_unknown', 'muted'
    if not enabled:
        key = 'topbar.edsm_off'
    elif status == 'error':
        key, style = 'topbar.edsm_error', 'statusError'
    elif status in ('running', 'waiting'):
        key, style = 'topbar.edsm_waiting', 'statusWarn'
    elif status == 'ok' and count:
        key, style = 'topbar.edsm_success', 'statusOk'
    lines = [tr(key), tr('edsm_service.upload') + ':',
             tr('edsm_service.enabled' if enabled else 'edsm_service.disabled')]
    if enabled:
        lines.append(tr('edsm_service.confirmed', count=count) if count else
                     tr('edsm_service.upload_unknown'))
        for outcome in details.get('outcomes', ()):
            if outcome in ('running', 'retry', 'cancelled', 'skipped', 'idle', 'partial', 'unconfirmed'):
                lines.append(tr('edsm_service.' + outcome))
        errors = details.get('errors', ()) or (
            (getattr(state, 'edsm_upload_message', ''),) if status == 'error' else ())
        lines.extend(dict.fromkeys(error_detail(error) for error in errors))
    return key, style, '\n'.join(lines)
