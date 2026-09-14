"""The application's single rotating logger and conservative privacy boundary."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import traceback
from urllib.parse import urlsplit, urlunsplit

LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 4
PRIVACY_MARKER = '[privacy-v1]'
REDACTED = '[redacted]'
_SECRET = re.compile(r'(?i)(authorization|password|passwd|secret|token|api[_-]?key|fid|commander|latitude|longitude|note|description|inventory|cargo|journal|favorite|screenshot)')


def sanitize(value):
    """Structured input is redacted by key; free text is a defensive fallback.

    Never use this to authorize arbitrary user content for logging. Log arguments
    and exception messages are omitted separately, including unlabelled secrets.
    """
    if isinstance(value, dict):
        return {str(k): REDACTED if _SECRET.search(str(k)) else sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(('{', '[')):
        import json
        try:
            json.loads(value)
            return "[structured payload omitted]"
        except ValueError:
            pass
    if re.match(r'^(?:[A-Za-z]:[\\/]|/|\\\\)', value):
        return '[path]'
    def url(match):
        try:
            parts = urlsplit(match.group())
            # Paths, credentials, query values AND fragment can all carry tokens.
            return urlunsplit((parts.scheme, parts.hostname or '', '/[redacted]', '', ''))
        except ValueError:
            return REDACTED
    value = re.sub(r'https?://[^\s<>]+', url, value)
    value = re.sub(r'(?i)\b(?:Bearer|Basic)\s+[^\s,;]+', REDACTED, value)
    value = re.sub(r'(?i)\b(?:authorization|password|passwd|secret|[\w-]*token|api[_-]?key|fid|commander(?:name)?|latitude|longitude|note)\s*[=:]\s*[^\r\n]+', REDACTED, value)
    value = re.sub(r'\bF\d{4,}\b', REDACTED, value)
    value = re.sub(r'(?:[A-Za-z]:[\\/]|/|\\\\)[^\s<>]*', '[path]', value)
    return value.replace('\r', ' ').replace('\n', ' ')


# Only explicitly named technical fields can bypass argument suppression.
_FIELDS = {'version', 'os', 'python', 'qt', 'pyside', 'architecture', 'pid',
           'count', 'files', 'events', 'images', 'missing', 'fields', 'remaining',
           'success', 'restored', 'phase', 'mode', 'field', 'python_type',
           'value_class', 'outside_sqlite_int64', 'retry_seconds'}


def _technical_fields(fields):
    safe = {}
    versions = {'version', 'python', 'qt', 'pyside'}
    enums = {
        'field': {'mission_id'},
        'python_type': {'int'},
        'value_class': {'unsigned_64', 'above_unsigned_64', 'below_signed_64'},
        'os': {'Linux', 'Windows', 'Darwin'},
        'architecture': {'x86_64', 'AMD64', 'arm64', 'aarch64', 'i386', 'i686', 'x86', 'armv7l'},
        'phase': {'rollback', 'failure', 'aborted', 'restart', 'backup', 'installation',
                  'extract', 'verification', 'started', 'cleanup', 'progress'},
        'mode': {'venv', 'python'},
    }
    for key, value in fields.items():
        if key not in _FIELDS:
            continue
        if key == 'outside_sqlite_int64':
            if type(value) is bool:
                safe[key] = value
            continue
        if key == 'retry_seconds':
            if type(value) is int and 0 <= value <= 60:
                safe[key] = value
            continue
        if key in versions and isinstance(value, str) and re.fullmatch(r'\d+(?:\.\d+){1,3}(?:[ab]\d+|rc\d+)?', value):
            safe[key] = value
        elif key in enums and isinstance(value, str) and value in enums[key]:
            safe[key] = value
        elif key not in versions and key not in enums and type(value) in (int, bool):
            safe[key] = value
    return safe


def log_event(logger, event, **fields):
    logger.info(event, extra={'diagnostic_fields': _technical_fields(fields)})


class PrivacyFormatter(logging.Formatter):
    def format(self, record):
        # Work on a copy; do not change records seen by other logging handlers.
        copy = logging.makeLogRecord(record.__dict__.copy())
        if not record.name.startswith('cmdrhelper'):
            message = 'External library event (details omitted)'
        elif record.args:
            args = ({key: REDACTED for key in record.args} if isinstance(record.args, dict)
                    else tuple(REDACTED for _ in record.args))
            try:
                message = record.msg % args
            except (TypeError, ValueError, KeyError):
                message = 'Application event (arguments omitted)'
        else:
            message = str(record.msg)
        copy.msg = sanitize(message)[:4096]
        fields = getattr(record, 'diagnostic_fields', {})
        if isinstance(fields, dict):
            # Revalidate, even when a caller supplies logging.extra directly.
            approved = _technical_fields(fields)
            copy.msg += ''.join(f' {k}={v}' for k, v in sorted(approved.items()))
        copy.args = ()
        copy.exc_info = copy.exc_text = copy.stack_info = None
        copy.threadName = 'main' if record.threadName == 'MainThread' else 'worker'
        copy.name = record.name if re.fullmatch(r'cmdrhelper(?:\.[a-z_]+)*', record.name) else 'external'
        text = super().format(copy)
        if record.exc_info:
            # All frames and chained exception types, but never source lines,
            # local variables or exception strings (which may contain payloads).
            seen = set()
            def frames(error, tb):
                if error is None or id(error) in seen:
                    return []
                seen.add(id(error))
                chain = error.__cause__ or (None if error.__suppress_context__ else error.__context__)
                lines = frames(chain, chain.__traceback__) if chain else []
                lines.append(PRIVACY_MARKER + ' Traceback (most recent call last):')
                for frame in traceback.extract_tb(tb):
                    lines.append(f'{PRIVACY_MARKER}   {Path(frame.filename).name}:{frame.lineno} in {frame.name}')
                codes = []
                import sqlite3
                if isinstance(error, sqlite3.Error):
                    code = getattr(error, 'sqlite_errorname', '')
                    if isinstance(code, str) and re.fullmatch(r'SQLITE_[A-Z_]+', code):
                        codes.append(code)
                if isinstance(error, OSError) and type(error.errno) is int:
                    codes.append(f'errno={error.errno}')
                from urllib.error import HTTPError
                if isinstance(error, HTTPError) and type(error.code) is int:
                    codes.append(f'HTTP={error.code}')
                lines.append(f'{PRIVACY_MARKER} {type(error).__name__}: [exception message omitted] ' + ' '.join(codes))
                return lines
            text += '\n' + '\n'.join(frames(record.exc_info[1], record.exc_info[2]))
        return text


class PrivacyRotatingFileHandler(RotatingFileHandler):
    def handleError(self, record):
        # logging's default error handler prints the original message/arguments,
        # which would bypass redaction precisely when the disk is full.
        import sys
        try:
            sys.stderr.write('CMDRHelper: log file unavailable\n')
        except Exception:
            pass


def log_folder() -> Path:
    folder = Path(__file__).resolve().parent.parent / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def configure_logging(level=logging.INFO) -> Path:
    import threading
    def thread_error(args):
        if args.exc_type is SystemExit:
            return
        logging.getLogger(__name__).critical('Unhandled background thread exception',
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = thread_error
    log_file = log_folder() / 'cmdrhelper.log'
    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers:
        if getattr(handler, '_cmdrhelper_file_handler', False):
            return Path(handler.baseFilename)
    handler = PrivacyRotatingFileHandler(log_file, maxBytes=LOG_MAX_BYTES,
                                  backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
    handler._cmdrhelper_file_handler = True
    handler.setLevel(level)
    handler.setFormatter(PrivacyFormatter(
        '%(asctime)s %(levelname)-8s [privacy-v1] [%(threadName)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
    root.addHandler(handler)
    return log_file


def logged_operation(event):
    """Log operation boundaries and tracebacks, never arguments or result payloads."""
    from functools import wraps
    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            name = function.__module__
            if name == '__main__':
                name = 'cmdrhelper.' + Path(function.__code__.co_filename).stem
            logger = logging.getLogger(name)
            log_event(logger, event + ' started')
            try:
                result = function(*args, **kwargs)
            except Exception:
                logger.exception(event + ' failed')
                raise
            counts = result if isinstance(result, dict) else {}
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                counts = result[1]
            fields = {key: counts[key] for key in ('count', 'images', 'missing', 'fields', 'remaining')
                      if type(counts.get(key)) is int}
            if 'ok' in counts:
                fields['success'] = counts['ok'] is True
            log_event(logger, event + ' finished', **fields)
            return result
        return run
    return decorate
