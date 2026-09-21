"""Explicit clipboard projection: synthetic diagnostics, no runtime state or IO."""
from copy import deepcopy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from cmdrhelper.market_data import MarketStatus, ProviderDiagnostics
from cmdrhelper.recommendation_diagnostics import (
    RecommendationDiagnostics, CommodityIdentity, CommodityStep, PartialReason)
from cmdrhelper.recommendation_diagnostic_text import format_recommendation_diagnostic

NOW=datetime(2026,1,2,12,tzinfo=timezone.utc)


def diagnostic():
    identity=CommodityIdentity(10001,'SyntheticCommodity')
    step=CommodityStep(identity,spansh_started=True,spansh_completed=True,
        provider_status=MarketStatus.TIMEOUT,truncated=True,
        reasons=[PartialReason.PROVIDER_TIMEOUT,PartialReason.PROVIDER_PAGE_LIMIT],
        provider=ProviderDiagnostics(http_requests=4,retries=1,last_http_status=504,
            retry_after='30',pages_started=3,pages_completed=2,page_limit=6,result_limit=100,
            page_limit_reached=False,result_limit_reached=False))
    return RecommendationDiagnostics(started_at=NOW,finished_at=NOW,duration=12.75,
        planned_commodities=52,checked_commodities=18,successful_commodities=17,
        failed_commodities=1,skipped_commodities=34,spansh_commodities_started=18,
        spansh_commodities_completed=18,spansh_commodities_failed=1,
        http_requests=20,cache_hits=2,retries=1,partial=True,
        partial_reason=PartialReason.PROVIDER_TIMEOUT,provider_truncated_count=1,
        provider_error_count=1,current_commodity=identity,first_failed_commodity=identity,
        last_completed_commodity=identity,last_http_status=504,retry_after='30',
        local_target_markets=2,local_candidates=12,local_recommendations=8,
        overlapping_market_ids=9,local_won_freshness=3,spansh_won_freshness=4,
        equal_timestamp_merges=2,merge_errors=0,steps=[step],
        reasons=[PartialReason.PROVIDER_TIMEOUT,PartialReason.PROVIDER_PAGE_LIMIT])


class DiagnosticTextTests(unittest.TestCase):
    def fields(self,d):
        text=format_recommendation_diagnostic(d)
        self.assertEqual(text.splitlines()[0],'CMDRHelper trade recommendation diagnostic')
        pairs=[line.split('=',1) for line in text.splitlines()[1:]]
        self.assertEqual(len(dict(pairs)),len(pairs))
        return dict(pairs)

    def test_existing_values_and_identifiers_exported_exactly(self):
        d=diagnostic();f=self.fields(d)
        for name in ('planned_commodities','checked_commodities','successful_commodities',
                     'failed_commodities','skipped_commodities','spansh_commodities_started',
                     'spansh_commodities_completed','spansh_commodities_failed','http_requests',
                     'cache_hits','retries','provider_truncated_count','provider_error_count',
                     'local_target_markets','local_candidates','local_recommendations',
                     'overlapping_market_ids','local_won_freshness','spansh_won_freshness',
                     'equal_timestamp_merges','merge_errors','last_http_status'):
            self.assertEqual(f[name],str(getattr(d,name)))
        self.assertEqual(f['duration_seconds'],'12.75')
        self.assertEqual(f['started_at'],NOW.isoformat())
        self.assertEqual(f['finished_at'],NOW.isoformat())
        self.assertEqual(f['partial'],'true')
        self.assertEqual(f['partial_reason'],'PROVIDER_TIMEOUT')
        self.assertEqual(f['cancelled'],'false')
        self.assertEqual(f['context_changed'],'false')
        for key in ('first_failed_commodity','current_commodity','last_completed_commodity'):
            self.assertEqual(f[key],'10001:SyntheticCommodity')
        self.assertEqual(f['first_failed.provider_status'],'timeout')
        self.assertEqual(f['first_failed.pages_completed'],'2')
        self.assertEqual(f['first_failed.pages_started'],'3')
        self.assertEqual(f['first_failed.page_limit'],'6')
        self.assertEqual(f['first_failed.result_limit'],'100')
        self.assertEqual(f['first_failed.page_limit_reached'],'false')
        self.assertEqual(f['first_failed.result_limit_reached'],'false')
        self.assertEqual(f['first_failed.truncated'],'true')
        self.assertEqual(f['retry_after'],'30')
        self.assertEqual(f['reasons'],'PROVIDER_TIMEOUT,PROVIDER_PAGE_LIMIT')

    def test_no_recalculation_or_mutation(self):
        d=diagnostic();before=deepcopy(d)
        with patch.object(d,'aggregate',side_effect=AssertionError('No recalculation')):
            format_recommendation_diagnostic(d)
        self.assertEqual(d,before)
        self.assertEqual(d.checked_commodities,18)  # one illustrative step must not replace stored totals

    def test_all_reasons_preserved_and_cancel_context_flags(self):
        for reason in PartialReason:
            d=diagnostic();d.partial_reason=reason;d.reasons=[reason]
            d.cancelled=reason in (PartialReason.CANCELLED,PartialReason.CONTEXT_CHANGED)
            f=self.fields(d)
            self.assertEqual(f['partial_reason'],reason.value)
            self.assertEqual(f['context_changed'],str(reason==PartialReason.CONTEXT_CHANGED).lower())
            self.assertEqual(f['cancelled'],str(d.cancelled).lower())

    def test_whitelist_excludes_personal_fields_prices_payloads_and_paths(self):
        d=diagnostic()
        sensitive={'fid':'F_SYNTHETIC_PRIVATE','commander_name':'Private Test Commander',
                   'email':'private@example.invalid','path':'/synthetic/private/journal',
                   'session_id':'private-session','credits':987654321,'commander_buy_price':123456789,
                   'response_body':'secret response payload','url':'https://example.invalid/?private=1',
                   'cargo':['PrivateCargo']}
        for key,value in sensitive.items():
            setattr(d,key,value);setattr(d.steps[0],key,value)
        text=format_recommendation_diagnostic(d)
        for key,value in sensitive.items():
            self.assertNotIn(key+'=',text)
            self.assertNotIn(str(value),text)

    def test_untrusted_header_and_symbol_cannot_inject_diagnostic_lines(self):
        d=diagnostic();d.retry_after='https://example.invalid/private?fid=F_PRIVATE'
        d.first_failed_commodity=CommodityIdentity(10001,'bad\nfid=F_PRIVATE')
        text=format_recommendation_diagnostic(d)
        self.assertNotIn('F_PRIVATE',text)
        self.assertNotIn('https://',text)
        self.assertIn('first_failed_commodity=10001:[invalid_symbol]',text)
        self.assertIn('retry_after=[invalid_retry_after]',text)
        d.retry_after='Fri, 02 Jan 2026 12:00:00 GMT'
        self.assertEqual(self.fields(d)['retry_after'],d.retry_after)

    def test_empty_optional_fields_are_explicit_and_no_price_dump(self):
        d=RecommendationDiagnostics(started_at=NOW,finished_at=NOW)
        f=self.fields(d)
        self.assertEqual(f['first_failed_commodity'],'none')
        self.assertEqual(f['last_http_status'],'none')
        self.assertEqual(f['retry_after'],'none')
        self.assertEqual(f['partial_reason'],'NONE')
        self.assertNotIn('first_failed.provider_status',f)
        self.assertLess(len(f),50)


if __name__=='__main__':unittest.main()
