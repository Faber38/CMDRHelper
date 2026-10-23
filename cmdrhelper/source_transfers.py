"""Immutable source/FID-bound service jobs. No UI-selected identity is consulted."""
from pathlib import Path
from .edsm_uploader import EDSMJournalUploader
from .inara_uploader import BATCH_SIZE, upload_batch, InaraUploadError
from .journal_reader import classify_journal_file


def transfer(database, source, sessions, configs, settings, *, is_current, legacy_folder, source_folders,
             edsm_status=None):
    def notify(fid, result):
        if edsm_status is not None:
            try:
                edsm_status(fid, dict(result))
            except Exception:
                pass  # Optional UI observation cannot change service behavior.
    confirmed = {row['fid_seen'] for row in sessions
                 if row.get('attribution_status') == 'identified' and row.get('fid_seen')}
    results = {}
    for fid in confirmed:
        if not is_current():
            break
        edsm, inara = configs.get(fid, ({}, {}))
        def authorized(service, config):
            prefix = f'{service}/commanders/{fid}'
            enabled = str(settings.value(prefix+'/enabled', 'false')).lower() in ('1', 'true', 'yes', 'on')
            return (is_current() and enabled and config.get('enabled')
                    and settings.value(prefix+'/api_key', '') == config.get('api_key'))
        if edsm.get('enabled') and edsm.get('api_key') and edsm.get('commander'):
            uploader = EDSMJournalUploader(edsm['commander'], edsm['api_key'],
                settings=settings, fid=fid, source_id=source.id, is_current=lambda: authorized('edsm', edsm),
                legacy_folder=legacy_folder, source_folders=source_folders,
                on_upload_start=lambda fid=fid: notify(fid, {'running': True}))
            try:
                results[(fid, 'edsm')] = uploader.process_folder(Path(source.path))
            except Exception:
                notify(fid, {'error': 'EDSM-Upload fehlgeschlagen.',
                             'upload_attempted': uploader._upload_attempted})
                raise
            notify(fid, results[(fid, 'edsm')])
        if not inara.get('api_key') or not authorized('inara', inara):
            continue
        owners = {r['commander_id'] for r in sessions if r.get('fid_seen') == fid
                  and r.get('attribution_status') == 'identified'}
        if len(owners) != 1:
            continue
        cid = next(iter(owners))
        rows = database.inara_pending(cid, limit=BATCH_SIZE, journal_folder=source.path)
        eligible = []
        for row in rows:
            path = Path(row['journal_file'])
            if path.parent.resolve() != Path(source.path).resolve():
                continue
            proof = classify_journal_file(path)
            if proof['attribution_status'] == 'identified' and proof['fid_seen'] == fid:
                eligible.append(row)
        if not eligible or not authorized('inara', inara):
            continue
        database.validate_inara_request(cid, fid, eligible)
        retry = 0
        try:
            sent, errors = upload_batch(inara['api_key'], inara.get('commander') or '', fid, eligible)
        except InaraUploadError as exc:
            sent, errors = [], {r['id']: str(exc) for r in eligible}
            retry = exc.retry_seconds or 0
        # An in-flight acknowledgement remains bound to the original owner and
        # exact rows, even if the displayed commander changes meanwhile.
        database.update_inara_outbox(sent, errors, commander_id=cid, fid=fid, expected_rows=eligible,
                                    retry_seconds=retry)
        results[(fid, 'inara')] = (sent, errors)
    return results
