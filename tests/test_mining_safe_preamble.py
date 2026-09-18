"""Only proven harmless, closed intermediate journals preserve carrier continuity."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper.mining_carrier import CarrierLedger, read_carrier_feed
from cmdrhelper.mining_inventory import MiningInventory


class SafePreambleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name) / f'Journal.2026-09-15T{time}.01.log'
                      for time in ('154054', '160454', '160656')]
        self.sessions = []
        self.write(0, [{'event': 'Commander', 'FID': 'F1'}])
        self.write(1, [{'event': 'Fileheader'}, {'event': 'Friends'}, {'event': 'Friends'}])
        self.write(2, [{'event': 'Commander', 'FID': 'F1'}])
        for i, p in enumerate(self.paths):
            self.sessions.append(dict(journal_file=str(p), commander_id=None if i == 1 else 1,
                fid_seen=None if i == 1 else 'F1', attribution_status='unknown' if i == 1 else 'identified',
                file_size=p.stat().st_size, modified_ns=p.stat().st_mtime_ns))
        self.ledger = dict(version=1, fid='F1', carrier_id=123,
            anchor=CarrierLedger._anchor(read_carrier_feed(self.paths[0], 'F1')),
            context=[123, False], records={'gold': dict(count=None, resume_count=17,
                last_confirmed=999, status='inconsistent', confirmed_at='2026-09-14T00:00:00Z')})

    def write(self, i, events):
        self.paths[i].write_text(''.join(json.dumps(e)+'\n' for e in events))
        if self.sessions:
            self.sessions[i].update(file_size=self.paths[i].stat().st_size,
                                    modified_ns=self.paths[i].stat().st_mtime_ns)

    def result(self):
        before = deepcopy(self.ledger)
        result = CarrierLedger(None).advance(self.ledger, read_carrier_feed(self.paths[2], 'F1'),
                                             sessions=self.sessions)
        self.assertEqual(self.ledger, before)
        return result

    def rejected(self):
        result = self.result()
        self.assertIsNone(result['records']['gold']['count'])
        self.assertEqual(result['records']['gold']['status'], 'inconsistent')
        self.assertEqual(result['anchor'], self.ledger['anchor'])

    def test_allowed_preambles_resume_existing_balance_not_last_confirmed(self):
        for events in ([{'event': 'Fileheader'}],
                       [{'event': 'Fileheader'}, {'event': 'Friends'}, {'event': 'Friends'}]):
            self.write(1, events)
            result = self.result()
            self.assertEqual(result['records']['gold']['count'], 17)
            self.assertEqual(result['records']['gold']['status'], 'tracked')
            self.assertNotIn('resume_count', result['records']['gold'])

    def test_every_non_whitelisted_event_is_rejected(self):
        for event in ['NewUnknownEvent', 'Commander', 'LoadGame', 'Cargo', 'CargoTransfer',
                      'CarrierTransfer', 'Docked', 'Undocked', 'Location', 'FSDJump', 'Loadout',
                      'ShipyardSwap', 'CarrierStats', 'Materials', 'ShipLocker']:
            with self.subTest(event=event):
                self.write(1, [{'event': 'Fileheader'}, {'event': event}])
                self.rejected()

    def test_foreign_or_partially_attributed_files_rejected(self):
        original = deepcopy(self.sessions[1])
        for changes in [dict(fid_seen='F2'), dict(commander_id=2), dict(commander_name_seen='Other'),
                        dict(attribution_status='identified'), dict(attribution_status='conflict')]:
            with self.subTest(changes=changes):
                self.sessions[1] = {**original, **changes}
                self.rejected()

    def test_corrupt_truncated_empty_and_non_object_files_rejected(self):
        for raw in [b'', b'{"event":"Fileheader"}', b'{"event":"Fileheader"}\n{bad}\n',
                    b'{"event":"Fileheader"}\n{', b'[]\n', b'null\n', b'\xff\n']:
            with self.subTest(raw=raw):
                self.paths[1].write_bytes(raw)
                st = self.paths[1].stat()
                self.sessions[1].update(file_size=st.st_size, modified_ns=st.st_mtime_ns)
                self.rejected()

    def test_file_changed_since_index_is_rejected(self):
        with self.paths[1].open('a') as f:
            f.write('{"event":"Friends"}\n')
        self.rejected()

    def test_file_growing_during_read_is_rejected(self):
        original = Path.read_bytes
        def growing(path):
            raw = original(path)
            if path == self.paths[1]:
                with path.open('ab') as f:
                    f.write(b'{"event":"Friends"}\n')
            return raw
        with patch.object(Path, 'read_bytes', growing):
            self.rejected()

    def test_missing_file_and_missing_index_evidence_rejected(self):
        self.sessions[1].pop('modified_ns')
        self.rejected()
        self.paths[1].unlink()
        self.rejected()

    def test_anchor_hash_still_checked(self):
        self.ledger['anchor']['digest'] = 'bad'
        self.rejected()

    def test_live_unknown_file_is_not_exempted(self):
        self.sessions[2].update(fid_seen=None, commander_id=None, attribution_status='unknown')
        self.rejected()

    def test_transfer_after_preamble_and_srv_independence(self):
        self.write(2, [{'event': 'Commander', 'FID': 'F1'},
                       {'event': 'CargoTransfer', 'CarrierID': 123,
                        'Transfers': [{'Type': 'gold', 'Count': 3, 'Direction': 'tocarrier'}]}])
        result = self.result()
        self.assertEqual(result['records']['gold']['count'], 20)
        inventory = MiningInventory(1, 'F1', ship={}, srv=None)
        CarrierLedger(None).attach(inventory, result)
        self.assertEqual(inventory.stock('gold'), (None, 0, 20, None))

    def test_no_resume_count_never_promotes_last_confirmed(self):
        self.ledger['records']['gold'].pop('resume_count')
        self.assertIsNone(self.result()['records']['gold']['count'])
