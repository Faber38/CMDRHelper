"""Price-free recommendation diagnostics, entirely synthetic and offline."""
from dataclasses import asdict, replace
from datetime import timedelta
import io
import json
from threading import Event
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from cmdrhelper.commodity_master import all_commodities
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, ProviderDiagnostics
from cmdrhelper.recommendation_diagnostics import (
    PartialReason, RecommendationDiagnostics, RecommendationCancellation)
from cmdrhelper.spansh_market import SpanshMarketProvider
from cmdrhelper.trade_recommendations import search_recommendations
from cmdrhelper.ui.recommendations_view import diagnostic_reason_text, RecommendationWorker
from cmdrhelper.i18n import get_language, set_language, tr, _TRANSLATIONS
from test_trade_recommendations import item, market, offer, Provider, BEER, GOLD, NOW


class RunDiagnosticsTests(unittest.TestCase):
    def run_search(self, *, count=1, provider=None, locals=None, **kwargs):
        definitions = [BEER] + [c for c in all_commodities() if c != BEER][:count-1]
        args = dict(origin=market(rows=[item(c) for c in definitions]),
                    local_markets=[market(mid=2)] if locals is None else locals,
                    distances={2: 5}, free=280, margin=10,
                    query=MarketSearch('', 'Fixture System'), provider=provider or Provider(),
                    clock=lambda: NOW, progress=lambda result: None)
        args.update(kwargs)
        return search_recommendations(**args)

    def test_complete_52_with_immutable_progress_snapshots(self):
        updates = []
        result = self.run_search(count=52, progress=updates.append)
        d = result.diagnostics
        self.assertEqual((d.planned_commodities, d.checked_commodities, d.successful_commodities), (52,52,52))
        self.assertEqual((d.failed_commodities,d.skipped_commodities), (0,0))
        self.assertEqual((d.spansh_commodities_started,d.spansh_commodities_completed), (52,52))
        self.assertEqual(d.partial_reason, PartialReason.NONE)
        self.assertFalse(d.partial)
        self.assertLessEqual(d.started_at,d.finished_at)
        self.assertGreaterEqual(d.duration,0)
        self.assertEqual(updates[0].diagnostics.spansh_commodities_started,0)
        self.assertEqual(updates[0].diagnostics.local_commodities_completed,52)
        self.assertEqual(updates[18].diagnostics.checked_commodities,18)
        self.assertTrue(all(s.search_started and s.local_completed for s in d.steps))
        self.assertEqual(d.last_completed_commodity,d.steps[-1].commodity)

    def test_zero_spansh_after_local_evaluation(self):
        token=RecommendationCancellation()
        result=self.run_search(count=52,cancel=token,
                              progress=lambda r: token.request(PartialReason.CANCELLED))
        d=result.diagnostics
        self.assertEqual((d.planned_commodities,d.local_commodities_completed), (52,52))
        self.assertEqual((d.spansh_commodities_started,d.spansh_commodities_completed,
                          d.http_requests,d.cache_hits), (0,0,0,0))
        self.assertEqual(d.skipped_commodities,52)
        self.assertTrue(d.cancelled)
        self.assertEqual(d.partial_reason,PartialReason.CANCELLED)

    def test_partial_18_of_52_retains_local_rows_and_exact_step(self):
        class FailsAt18(Provider):
            def search_sell(self,q,*,cancel):
                self.queries.append(q)
                return MarketSearchResult(MarketStatus.TIMEOUT if len(self.queries)==18
                                          else MarketStatus.NO_RESULTS,
                                          diagnostics=ProviderDiagnostics(http_requests=1))
        result=self.run_search(count=52,provider=FailsAt18())
        d=result.diagnostics
        self.assertEqual((d.planned_commodities,d.checked_commodities,d.successful_commodities,
                          d.failed_commodities,d.skipped_commodities),(52,18,17,1,34))
        self.assertEqual((d.spansh_commodities_started,d.spansh_commodities_completed,
                          d.spansh_commodities_failed,d.http_requests),(18,18,1,18))
        self.assertEqual(d.partial_reason,PartialReason.PROVIDER_TIMEOUT)
        self.assertEqual(d.first_failed_commodity,d.steps[17].commodity)
        self.assertEqual(d.steps[17].provider_status,MarketStatus.TIMEOUT)
        self.assertEqual(d.current_commodity,d.last_completed_commodity)
        self.assertEqual(len(result.rows),1)
        self.assertEqual(result.rows[0].destination.provider,'local_elite')
        self.assertEqual(d.local_recommendations,1)
        self.assertEqual(d.local_commodities_completed,52)

    def test_all_structured_provider_reasons_and_ui_text(self):
        cases=((MarketStatus.NETWORK_ERROR,PartialReason.PROVIDER_NETWORK,'network'),
               (MarketStatus.TIMEOUT,PartialReason.PROVIDER_TIMEOUT,'timeout'),
               (MarketStatus.HTTP_ERROR,PartialReason.PROVIDER_HTTP,'http'),
               (MarketStatus.RATE_LIMIT,PartialReason.PROVIDER_RATE_LIMIT,'rate_limit'),
               (MarketStatus.INVALID_JSON,PartialReason.PROVIDER_INVALID_RESPONSE,'invalid_response'),
               (MarketStatus.INVALID_RESPONSE,PartialReason.PROVIDER_INVALID_RESPONSE,'invalid_response'),
               (MarketStatus.UNKNOWN_SYSTEM,PartialReason.PROVIDER_UNKNOWN_SYSTEM,'unknown_system'),
               (MarketStatus.UNKNOWN_COMMODITY,PartialReason.COMMODITY_ERROR,'commodity'))
        for status,reason,key in cases:
            with self.subTest(status=status):
                result=self.run_search(provider=Provider({BEER.frontier_id:MarketSearchResult(status)}))
                d=result.diagnostics
                self.assertTrue(d.partial)
                self.assertEqual(d.partial_reason,reason)
                self.assertEqual(d.first_failed_commodity.symbol,BEER.symbol)
                self.assertEqual(d.provider_error_count,1)
                self.assertEqual(d.failed_commodities,1)
                self.assertEqual(diagnostic_reason_text(reason),tr('recommend.reason_'+key))

    def test_truncation_page_and_result_limits(self):
        cases=((ProviderDiagnostics(),PartialReason.PROVIDER_TRUNCATED),
               (ProviderDiagnostics(page_limit_reached=True),PartialReason.PROVIDER_PAGE_LIMIT),
               (ProviderDiagnostics(result_limit_reached=True),PartialReason.PROVIDER_RESULT_LIMIT))
        for stats,reason in cases:
            result=self.run_search(provider=Provider({BEER.frontier_id:
                MarketSearchResult(MarketStatus.OK,(offer(),),truncated=True,diagnostics=stats)}))
            d=result.diagnostics
            self.assertEqual(d.partial_reason,reason)
            self.assertEqual(d.provider_truncated_count,1)
            self.assertEqual(d.successful_commodities,0)  # completed, but not fully checked
            self.assertEqual(d.provider_error_count,0)
            self.assertEqual(diagnostic_reason_text(reason),tr('recommend.reason_limit'))
            self.assertTrue(result.rows)

    def test_unknown_commodity_no_http_and_unexpected_commodity_exception(self):
        unknown=dict(item(),commodity_id=199999999,symbol='FutureSynthetic')
        p=Provider()
        d=self.run_search(origin=market(rows=[unknown]),provider=p).diagnostics
        self.assertEqual(d.partial_reason,PartialReason.COMMODITY_ERROR)
        self.assertFalse(p.queries)
        self.assertEqual((d.checked_commodities,d.failed_commodities,d.spansh_commodities_started),(1,1,0))
        d=self.run_search(provider=Provider({BEER.frontier_id:ValueError('synthetic')})).diagnostics
        self.assertEqual(d.partial_reason,PartialReason.COMMODITY_ERROR)
        self.assertEqual(d.steps[0].provider_status,MarketStatus.INVALID_RESPONSE)

    def test_http_cache_retry_counts_are_independent(self):
        p=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.NO_RESULTS,from_cache=True,
                    diagnostics=ProviderDiagnostics(cache_hits=1)),
                    GOLD.frontier_id:MarketSearchResult(MarketStatus.NO_RESULTS,
                    diagnostics=ProviderDiagnostics(http_requests=3,retries=1,last_http_status=200))})
        d=self.run_search(origin=market(rows=[item(),item(GOLD)]),provider=p).diagnostics
        self.assertEqual((d.http_requests,d.cache_hits,d.retries,d.last_http_status),(3,1,1,200))

    def test_merge_counts_not_repeated_by_progress_and_no_partial(self):
        for local_age,remote_age,counters,source in ((0,1,(1,0,0),'local_elite'),
                   (1,0,(0,1,0),'spansh'),(0,0,(0,0,1),'local_elite')):
            with self.subTest(source=source,counters=counters):
                local=market(mid=2,stamp=NOW-timedelta(hours=local_age))
                p=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,
                    (offer(stamp=NOW-timedelta(hours=remote_age)),))})
                r=self.run_search(locals=[market(),local],provider=p)
                d=r.diagnostics
                self.assertEqual(d.overlapping_market_ids,1)
                self.assertEqual((d.local_won_freshness,d.spansh_won_freshness,
                                  d.equal_timestamp_merges),counters)
                self.assertEqual((d.local_target_markets,d.local_combinations_checked,
                                  d.local_candidates),(1,1,1))
                self.assertEqual(r.rows[0].destination.provider,source)
                self.assertFalse(d.partial)
                self.assertEqual(d.partial_reason,PartialReason.NONE)
                self.assertEqual(d.merge_errors,0)

    def test_invalid_local_targets_excluded_from_counts(self):
        targets=[market(),market(mid=2),market(mid=3,fid='F_SYNTHETIC_OTHER'),
                 market(mid=4,stamp=NOW-timedelta(days=1)),market(mid=5,source='spansh')]
        d=self.run_search(locals=targets).diagnostics
        self.assertEqual((d.local_target_markets,d.local_combinations_checked),(1,1))
        empty=self.run_search(origin=market(rows=[]),locals=targets).diagnostics
        self.assertEqual((empty.local_target_markets,empty.planned_commodities),(1,0))

    def test_cancelled_and_context_changed_not_provider_failure(self):
        for reason in (PartialReason.CANCELLED,PartialReason.CONTEXT_CHANGED):
            token=RecommendationCancellation()
            def cancel_after_first(r):
                if r.checked==1: token.request(reason)
            d=self.run_search(count=2,cancel=token,progress=cancel_after_first).diagnostics
            self.assertEqual(d.partial_reason,reason)
            self.assertTrue(d.cancelled)
            self.assertEqual(d.provider_error_count,0)
            self.assertNotIn('Community',diagnostic_reason_text(reason))

    def test_origin_expiration_context_reason(self):
        d=self.run_search(origin=market(stamp=NOW-timedelta(days=1))).diagnostics
        self.assertEqual(d.partial_reason,PartialReason.CONTEXT_CHANGED)
        self.assertEqual(d.spansh_commodities_started,0)

    def test_diagnostics_contain_no_prices_fid_market_lists_or_payloads(self):
        data=asdict(self.run_search().diagnostics)
        text=repr(data)
        for forbidden in ('commander_buy_price','commander_sell_price','fid','Fixture Port','response_body'):
            self.assertNotIn(forbidden,text)

    def test_all_reasons_translated_in_twelve_languages(self):
        previous=get_language()
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                for reason in PartialReason:
                    self.assertNotIn('recommend.',diagnostic_reason_text(reason))
                for key in ('complete','partial_counts','diagnostic_details'):
                    self.assertIn('recommend.'+key,_TRANSLATIONS[lang])
                text=tr('recommend.partial_counts',checked=18,total=52,
                        reason=diagnostic_reason_text(PartialReason.PROVIDER_TIMEOUT))
                self.assertIn('18',text);self.assertIn('52',text)
        finally:set_language(previous)

    def test_merge_failure_captured_by_existing_worker_guard(self):
        worker=RecommendationWorker(market(),[market(mid=2)],{2:5},280,10,
                                    MarketSearch('', 'Fixture System'),Provider(),lambda:NOW)
        results=[]
        worker.signals.finished.connect(results.append)
        with patch('cmdrhelper.trade_recommendations.merge_destinations',side_effect=ValueError('synthetic')):
            worker.run()
        self.assertEqual(len(results),1)
        d=results[0].diagnostics
        self.assertEqual(d.merge_errors,1)
        self.assertEqual(d.partial_reason,PartialReason.OTHER)
        self.assertIsNotNone(d.first_failed_commodity)
        self.assertEqual(d.spansh_commodities_started,0)


class TransportDiagnosticsTests(unittest.TestCase):
    def make_provider(self, answers, **options):
        self.requests=[];self.waits=[];self.seconds=1000
        def opener(request,*,timeout):
            self.requests.append((request.method,timeout))
            answer=answers.pop(0)
            if isinstance(answer,Exception):raise answer
            response=io.BytesIO(answer if isinstance(answer,bytes) else json.dumps(answer).encode())
            response.status=200
            return response
        def sleep(seconds):
            self.waits.append(seconds);self.seconds+=seconds
        return SpanshMarketProvider(opener=opener,clock=lambda:self.seconds,utcnow=lambda:NOW,
                                    sleep=sleep,**options)

    def query(self,**changes):
        return MarketSearch('Beer','Fixture System',include_fleet_carriers=True,**changes)

    def response(self,rows=None,count=None):
        rows=rows or []
        return dict(reference=dict(name='Fixture System'),results=rows,
                    count=len(rows) if count is None else count)

    def station(self,mid):
        return dict(name='Synthetic Port',market_id=mid,system_name='Synthetic Target',system_id64=200,
                    type='Coriolis',distance=5,distance_to_arrival=200,has_large_pad=True,
                    market_updated_at=NOW.isoformat(),market=[dict(commodity='Beer',buy_price=0,
                    sell_price=11500,supply=0,demand=190)])

    def test_actual_requests_cache_hit_and_unchanged_spacing(self):
        p=self.make_provider([self.response(),self.response()])
        first=p.search_sell(self.query()); cached=p.search_sell(self.query())
        another=p.search_sell(self.query(radius_ly=50))
        self.assertEqual((first.diagnostics.http_requests,first.diagnostics.cache_hits),(1,0))
        self.assertEqual((cached.diagnostics.http_requests,cached.diagnostics.cache_hits),(0,1))
        self.assertEqual(another.diagnostics.http_requests,1)
        self.assertEqual(self.requests,[('POST',10),('POST',10)])
        self.assertEqual(self.waits,[1])
        self.assertEqual(first.diagnostics.last_http_status,200)

    def test_retries_and_errors_preserve_counts_and_page_attempts(self):
        cases=[(TimeoutError(),MarketStatus.TIMEOUT),(URLError('synthetic'),MarketStatus.NETWORK_ERROR)]
        for error,status in cases:
            p=self.make_provider([error,error])
            result=p.search_sell(self.query())
            self.assertEqual(result.status,status)
            d=result.diagnostics
            self.assertEqual((d.http_requests,d.retries,d.pages_started,d.pages_completed),(2,1,1,0))
            self.assertEqual(self.waits,[2])

    def test_http_status_retry_after_rate_limit_and_no_extra_request(self):
        error=HTTPError('https://example.invalid',429,'synthetic',{'Retry-After':'120'},io.BytesIO(b'{}'))
        p=self.make_provider([error])
        first=p.search_sell(self.query()); second=p.search_sell(self.query(radius_ly=50))
        self.assertEqual(first.status,MarketStatus.RATE_LIMIT)
        self.assertEqual((first.diagnostics.http_requests,first.diagnostics.retries,
                          first.diagnostics.last_http_status,first.diagnostics.retry_after),(1,0,429,'120'))
        self.assertEqual(second.diagnostics.http_requests,0)
        self.assertEqual(second.status,MarketStatus.RATE_LIMIT)
        self.assertEqual(len(self.requests),1)

    def test_http_invalid_json_invalid_schema_unknown_system(self):
        cases=[(HTTPError('https://example.invalid',403,'synthetic',{},io.BytesIO(b'{}')),MarketStatus.HTTP_ERROR),
               (b'not-json',MarketStatus.INVALID_JSON),([],MarketStatus.INVALID_RESPONSE),
               ({'reference':None},MarketStatus.UNKNOWN_SYSTEM)]
        for answer,status in cases:
            p=self.make_provider([answer])
            result=p.search_sell(self.query())
            self.assertEqual(result.status,status)
            self.assertEqual(result.diagnostics.http_requests,1)
            self.assertEqual(result.diagnostics.pages_completed,0)

    def test_page_and_result_limit_counters_and_cached_truncation(self):
        p=self.make_provider([self.response([self.station(mid)],count=4) for mid in (2,3,4)],
                             page_size=1,max_pages=3)
        r=p.search_sell(self.query())
        self.assertTrue(r.truncated)
        self.assertTrue(r.diagnostics.page_limit_reached)
        self.assertEqual((r.diagnostics.page_limit,r.diagnostics.pages_completed),(3,3))
        cached=p.search_sell(self.query())
        self.assertTrue(cached.diagnostics.page_limit_reached)
        self.assertEqual((cached.diagnostics.http_requests,cached.diagnostics.pages_completed),(0,0))
        p=self.make_provider([self.response([self.station(2),self.station(3)])])
        r=p.search_sell(self.query(limit=1))
        self.assertTrue(r.truncated)
        self.assertTrue(r.diagnostics.result_limit_reached)
        self.assertFalse(r.diagnostics.page_limit_reached)
        self.assertEqual(r.diagnostics.result_limit,1)
        self.assertEqual(len(r.offers),1)

    def test_metadata_requests_and_failure_before_first_market_page(self):
        p=self.make_provider([{'values':['Coriolis','Fleet Carrier']},self.response()])
        r=p.search_sell(replace(self.query(),include_fleet_carriers=False))
        self.assertEqual(r.diagnostics.http_requests,2)
        self.assertEqual([method for method,_ in self.requests],['GET','POST'])
        self.assertEqual(r.diagnostics.pages_completed,1)
        p=self.make_provider([TimeoutError(),TimeoutError()])
        r=p.search_sell(replace(self.query(),include_fleet_carriers=False))
        self.assertEqual(r.status,MarketStatus.TIMEOUT)
        self.assertEqual((r.diagnostics.http_requests,r.diagnostics.retries,r.diagnostics.pages_started),(2,1,0))

    def test_shared_provider_keeps_waiting_worker_counters_separate(self):
        from threading import Thread
        entered=Event();release=Event();results={}
        p=self.make_provider([self.response()])
        opener=p.opener
        def blocked(request,**kwargs):
            entered.set();release.wait(2)
            return opener(request,**kwargs)
        p.opener=blocked
        first=Thread(target=lambda:results.update(first=p.search_sell(self.query())))
        token=Event()
        second=Thread(target=lambda:results.update(second=p.search_sell(self.query(),cancel=token)))
        first.start()
        try:
            self.assertTrue(entered.wait(1))
            second.start();token.set();second.join(1)
            self.assertFalse(second.is_alive())
            self.assertEqual(results['second'].status,MarketStatus.CANCELLED)
            self.assertEqual(results['second'].diagnostics.http_requests,0)
        finally:
            release.set();first.join(2)
        self.assertEqual(results['first'].diagnostics.http_requests,1)

    def test_unexpected_failure_counters_survive_exception(self):
        p=self.make_provider([ValueError('synthetic')])
        with self.assertRaises(ValueError) as error:p.search_sell(self.query())
        self.assertEqual(error.exception.market_diagnostics.http_requests,1)


if __name__=='__main__':unittest.main()
