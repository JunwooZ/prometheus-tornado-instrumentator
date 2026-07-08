import os
from http import HTTPStatus

from prometheus_client import CollectorRegistry
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, ExpectLog, gen_test
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator, metrics


class HelloHandler(RequestHandler):
    def get(self):
        self.write("hello")


class OtherHandler(RequestHandler):
    def get(self):
        self.write("other")


class MethodHandler(RequestHandler):
    def get(self):
        self.write("get")

    def post(self):
        self.write("post")

    def put(self):
        self.write("put")


class CreatedHandler(RequestHandler):
    def post(self):
        self.set_status(201)
        self.write("created")


class AcceptedEnumHandler(RequestHandler):
    def get(self):
        self.set_status(HTTPStatus.ACCEPTED)
        self.write("accepted")


class NoContentHandler(RequestHandler):
    def delete(self):
        self.set_status(204)
        self.finish()


class ErrorHandler(RequestHandler):
    def get(self):
        self.set_status(404)
        self.write("missing")


class RuntimeErrorHandler(RequestHandler):
    def get(self):
        raise RuntimeError("boom")


class ItemHandler(RequestHandler):
    def get(self, item_id):
        self.write(f"item:{item_id}")


class IgnoreHandler(RequestHandler):
    def get(self):
        self.write("ignore")


class BodyHandler(RequestHandler):
    def get(self):
        self.write("123456789")


class JsonBodyHandler(RequestHandler):
    def get(self):
        self.write({"ok": True})


class LargeBodyHandler(RequestHandler):
    def get(self):
        self.write("x" * 20_000)


class EmptyBodyHandler(RequestHandler):
    def get(self):
        self.set_status(200)
        self.finish()


class StreamingBodyHandler(RequestHandler):
    async def get(self):
        for index in range(5):
            self.write(f"{index}xxx")
            await self.flush()
            await gen.sleep(0.01)


class LargeStreamingBodyHandler(RequestHandler):
    async def get(self):
        for index in range(20):
            self.write(f"{index:02d}" + ("x" * 1_000))
            await self.flush()


class ExplicitInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler), (r"/missing", ErrorHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.requests(registry=self.registry)
        ).instrument(app)
        return app

    def test_request_counter_observes_real_tornado_requests(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/missing").code == 404

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/missing", "method": "GET", "status": "4xx"},
            )
            == 1
        )


class DifferentPathsInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application(
            [
                (r"/hello", HelloHandler),
                (r"/other", OtherHandler),
            ]
        )
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_different_paths_are_counted_separately(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/other").code == 200
        assert self.fetch("/other").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/other", "method": "GET", "status": "2xx"},
            )
            == 2
        )


class HttpMethodsInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/method", MethodHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_http_methods_are_counted_separately(self):
        assert self.fetch("/method").code == 200
        assert self.fetch("/method", method="POST", body=b"").code == 200
        assert self.fetch("/method", method="PUT", body=b"").code == 200

        for method in ("GET", "POST", "PUT"):
            assert (
                self.registry.get_sample_value(
                    "http_requests_total",
                    {"handler": "/method", "method": method, "status": "2xx"},
                )
                == 1
            )


class StatusCodesInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application(
            [
                (r"/created", CreatedHandler),
                (r"/empty", NoContentHandler),
                (r"/missing", ErrorHandler),
            ]
        )
        Instrumentator(
            registry=self.registry,
            should_group_status_codes=False,
        ).instrument(app)
        return app

    def test_status_codes_are_observed_without_grouping(self):
        assert self.fetch("/created", method="POST", body=b"").code == 201
        assert self.fetch("/empty", method="DELETE").code == 204
        assert self.fetch("/missing", raise_error=False).code == 404

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/created", "method": "POST", "status": "201"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/empty", "method": "DELETE", "status": "204"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/missing", "method": "GET", "status": "404"},
            )
            == 1
        )


class GroupedStatusCodeWithEnumerationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/accepted", AcceptedEnumHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_grouped_status_codes_with_enumeration(self):
        assert self.fetch("/accepted").code == 202

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/accepted", "method": "GET", "status": "2xx"},
            )
            == 1
        )


class DefaultInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_instrument_adds_default_metrics_when_none_are_added(self):
        assert self.fetch("/hello").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_count",
                {"handler": "/hello", "method": "GET"},
            )
            == 1
        )


class DefaultInstrumentationNamespaceTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(registry=self.registry).instrument(
            app,
            metric_namespace="namespace",
            metric_subsystem="example",
        )
        return app

    def test_default_metrics_can_use_namespace_and_subsystem(self):
        assert self.fetch("/hello").code == 200

        assert (
            self.registry.get_sample_value(
                "namespace_example_http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "namespace_example_http_request_duration_seconds_count",
                {"handler": "/hello", "method": "GET"},
            )
            == 1
        )


class DefaultInstrumentationHighrFilterTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/missing", ErrorHandler)])
        Instrumentator(registry=self.registry).instrument(
            app,
            should_only_respect_2xx_for_highr=True,
        )
        return app

    def test_instrument_passes_high_resolution_2xx_filter_to_default_metrics(self):
        assert self.fetch("/missing", raise_error=False).code == 404

        assert (
            self.registry.get_sample_value("http_request_duration_highr_seconds_count")
            == 0
        )
        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_count",
                {"method": "GET", "handler": "/missing"},
            )
            == 1
        )


class DefaultInstrumentationExcludeStreamingDurationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/stream", StreamingBodyHandler)])
        Instrumentator(
            registry=self.registry,
            should_exclude_streaming_duration=True,
        ).instrument(app)
        return app

    def test_constructor_streaming_duration_flag_reaches_default_metrics(self):
        assert self.fetch("/stream").code == 200

        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_sum",
                {"method": "GET", "handler": "/stream"},
            )
            < 0.03
        )


class CustomMetricNameTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.latency(metric_name="tornado_latency", registry=self.registry)
        ).instrument(app).expose(app)
        return app

    def test_custom_metric_name_is_used(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics").code == 200

        assert (
            self.registry.get_sample_value(
                "tornado_latency_count",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_count",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            is None
        )


class CustomLatencyBucketTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.latency(
                buckets=(1, 2, 3),
                should_include_handler=False,
                should_include_method=False,
                should_include_status=False,
                registry=self.registry,
            )
        ).instrument(app)
        return app

    def test_latency_buckets_can_omit_explicit_infinity(self):
        assert self.fetch("/hello").code == 200

        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_bucket", {"le": "+Inf"}
            )
            == 1
        )


class RoundedLatencyTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed = []

        def observe(info):
            self.observed.append(
                (info.modified_duration, info.modified_duration_without_streaming)
            )

        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            should_round_latency_decimals=True,
            round_latency_decimals=3,
        ).add(observe).instrument(app)
        return app

    def test_observation_info_durations_are_rounded(self):
        assert self.fetch("/hello").code == 200

        duration, duration_without_streaming = self.observed[0]
        assert duration == round(duration, 3)
        assert duration_without_streaming == round(duration_without_streaming, 3)


class EnvVarDisabledInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        self._old_enabled = os.environ.pop("PROM_TORNADO_TEST_ENABLED", None)
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            registry=self.registry,
            should_respect_env_var=True,
            env_var_name="PROM_TORNADO_TEST_ENABLED",
        ).instrument(app).expose(app)
        return app

    def tearDown(self):
        if self._old_enabled is not None:
            os.environ["PROM_TORNADO_TEST_ENABLED"] = self._old_enabled
        else:
            os.environ.pop("PROM_TORNADO_TEST_ENABLED", None)
        super().tearDown()

    def test_instrument_and_expose_are_disabled_when_env_var_is_absent(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics", raise_error=False).code == 404

        assert self.registry.get_sample_value("http_requests_total") is None


class EnvVarEnabledInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        self._old_enabled = os.environ.get("PROM_TORNADO_TEST_ENABLED")
        os.environ["PROM_TORNADO_TEST_ENABLED"] = "true"
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            registry=self.registry,
            should_respect_env_var=True,
            env_var_name="PROM_TORNADO_TEST_ENABLED",
        ).instrument(app).expose(app)
        return app

    def tearDown(self):
        if self._old_enabled is not None:
            os.environ["PROM_TORNADO_TEST_ENABLED"] = self._old_enabled
        else:
            os.environ.pop("PROM_TORNADO_TEST_ENABLED", None)
        super().tearDown()

    def test_instrument_and_expose_are_enabled_when_env_var_exists(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )


class EnvVarFalseInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        self._old_enabled = os.environ.get("PROM_TORNADO_TEST_ENABLED")
        os.environ["PROM_TORNADO_TEST_ENABLED"] = "false"
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            registry=self.registry,
            should_respect_env_var=True,
            env_var_name="PROM_TORNADO_TEST_ENABLED",
        ).instrument(app).expose(app)
        return app

    def tearDown(self):
        if self._old_enabled is not None:
            os.environ["PROM_TORNADO_TEST_ENABLED"] = self._old_enabled
        else:
            os.environ.pop("PROM_TORNADO_TEST_ENABLED", None)
        super().tearDown()

    def test_instrument_and_expose_are_disabled_when_env_var_is_false(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics", raise_error=False).code == 404

        assert self.registry.get_sample_value("http_requests_total") is None


class UngroupedStatusCodeTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/missing", ErrorHandler)])
        Instrumentator(
            registry=self.registry,
            should_group_status_codes=False,
        ).instrument(app)
        return app

    def test_status_code_can_be_observed_without_grouping(self):
        assert self.fetch("/missing").code == 404

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/missing", "method": "GET", "status": "404"},
            )
            == 1
        )


class CustomInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed = []

        def observe(info):
            self.observed.append(
                (info.method, info.modified_handler, info.modified_status)
            )

        app = Application([(r"/hello", HelloHandler)])
        Instrumentator().add(observe).instrument(app)
        return app

    def test_sync_instrumentation_receives_observation_info(self):
        assert self.fetch("/hello").code == 200

        assert self.observed == [("GET", "/hello", "2xx")]


class AsyncCustomInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed = []

        async def observe(info):
            await gen.sleep(0)
            self.observed.append(
                (info.method, info.modified_handler, info.modified_status)
            )

        app = Application([(r"/hello", HelloHandler)])
        Instrumentator().add(observe).instrument(app)
        return app

    @gen_test
    async def test_async_instrumentation_receives_observation_info(self):
        response = await self.http_client.fetch(self.get_url("/hello"))
        await gen.sleep(0)
        await gen.sleep(0)

        assert response.code == 200
        assert self.observed == [("GET", "/hello", "2xx")]


class AsyncCustomInstrumentationErrorTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed = []

        async def observe(info):
            await gen.sleep(0)
            self.observed.append(info.modified_handler)
            raise RuntimeError("async instrumentation failed")

        app = Application([(r"/hello", HelloHandler)])
        Instrumentator().add(observe).instrument(app)
        return app

    @gen_test
    async def test_async_instrumentation_error_does_not_change_response(self):
        with ExpectLog("tornado.application", "Exception in callback"):
            response = await self.http_client.fetch(self.get_url("/hello"))
            await gen.sleep(0)
            await gen.sleep(0)

        assert response.code == 200
        assert self.observed == ["/hello"]


class ParameterizedRouteLabelTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/items/([0-9]+)", ItemHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_parameterized_route_uses_pattern_not_raw_path(self):
        assert self.fetch("/items/123").code == 200
        assert self.fetch("/items/456").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/items/%s", "method": "GET", "status": "2xx"},
            )
            == 2
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/items/123", "method": "GET", "status": "2xx"},
            )
            is None
        )


class ExcludedHandlersTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler), (r"/ignore", IgnoreHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=["/ignore"],
        ).instrument(app)
        return app

    def test_excluded_handler_is_not_instrumented(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/ignore").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/ignore", "method": "GET", "status": "2xx"},
            )
            is None
        )


class RegexExcludedHandlersTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler), (r"/internal/status", IgnoreHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=[r"/internal/.*"],
        ).instrument(app)
        return app

    def test_regex_excluded_handler_is_not_instrumented(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/internal/status").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/internal/status", "method": "GET", "status": "2xx"},
            )
            is None
        )


class SearchRegexExcludedHandlersTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler), (r"/internal/status", IgnoreHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=["internal"],
        ).instrument(app)
        return app

    def test_regex_excluded_handler_uses_search_semantics(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/internal/status").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/internal/status", "method": "GET", "status": "2xx"},
            )
            is None
        )


def test_excluded_handlers_empty_list_is_preserved():
    instrumentator = Instrumentator(excluded_handlers=[])

    assert instrumentator.excluded_handlers == []
    assert isinstance(instrumentator.excluded_handlers, list)


class MetricsEndpointExclusionTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=["/metrics"],
        ).instrument(app).expose(app)
        return app

    def test_metrics_endpoint_can_be_excluded_from_instrumentation(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/metrics", "method": "GET", "status": "2xx"},
            )
            is None
        )


class MetricsEndpointExclusionAfterExposeTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=["/metrics"],
        ).expose(app).instrument(app)
        return app

    def test_metrics_endpoint_is_excluded_when_exposed_before_instrument(self):
        assert self.fetch("/hello").code == 200
        assert self.fetch("/metrics").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/hello", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/metrics", "method": "GET", "status": "2xx"},
            )
            is None
        )


class NotFoundRouteTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/hello", HelloHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_unmatched_route_returns_404_without_recording_raw_path(self):
        response = self.fetch("/does-not-exist", raise_error=False)

        assert response.code == 404
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/does-not-exist", "method": "GET", "status": "4xx"},
            )
            is None
        )


class ResponseBodyDefaultTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed_bodies = []

        def observe(info):
            self.observed_bodies.append(info.response.body)

        app = Application([(r"/body", BodyHandler)])
        Instrumentator().add(observe).instrument(app)
        return app

    def test_response_body_is_empty_by_default(self):
        response = self.fetch("/body")

        assert response.code == 200
        assert response.body == b"123456789"
        assert self.observed_bodies == [b""]


class ResponseBodyCaptureTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed_bodies = []

        def observe(info):
            self.observed_bodies.append(info.response.body)

        app = Application(
            [
                (r"/body", BodyHandler),
                (r"/json-body", JsonBodyHandler),
                (r"/large-body", LargeBodyHandler),
                (r"/empty", EmptyBodyHandler),
            ]
        )
        Instrumentator(body_handlers=[r"/.*"]).add(observe).instrument(app)
        return app

    def test_body_handlers_enable_response_body_capture(self):
        response = self.fetch("/body")

        assert response.code == 200
        assert response.body == b"123456789"
        assert self.observed_bodies == [b"123456789"]

    def test_json_response_body_is_captured_after_tornado_serialization(self):
        response = self.fetch("/json-body")

        assert response.code == 200
        assert response.headers["Content-Type"].startswith("application/json")
        assert response.body == b'{"ok": true}'
        assert self.observed_bodies == [b'{"ok": true}']

    def test_large_response_body_is_captured(self):
        response = self.fetch("/large-body")

        assert response.code == 200
        assert response.body == b"x" * 20_000
        assert self.observed_bodies == [b"x" * 20_000]

    def test_empty_response_body_is_captured_as_empty(self):
        response = self.fetch("/empty")

        assert response.code == 200
        assert self.observed_bodies == [b""]


class SearchRegexResponseBodyCaptureTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed_bodies = []

        def observe(info):
            self.observed_bodies.append(info.response.body)

        app = Application([(r"/json-body", JsonBodyHandler)])
        Instrumentator(body_handlers=["json"]).add(observe).instrument(app)
        return app

    def test_body_handlers_use_search_semantics(self):
        response = self.fetch("/json-body")

        assert response.code == 200
        assert self.observed_bodies == [b'{"ok": true}']


class StreamingBodyCaptureTest(AsyncHTTPTestCase):
    def get_app(self):
        self.observed = []

        def observe(info):
            self.observed.append(
                (
                    info.response.body,
                    info.modified_duration_without_streaming,
                    info.modified_duration,
                )
            )

        app = Application(
            [
                (r"/stream", StreamingBodyHandler),
                (r"/large-stream", LargeStreamingBodyHandler),
            ]
        )
        Instrumentator(body_handlers=[r"/.*stream"]).add(observe).instrument(app)
        return app

    def test_streamed_response_body_is_captured(self):
        response = self.fetch("/stream")

        assert response.code == 200
        assert response.body == b"0xxx1xxx2xxx3xxx4xxx"
        assert self.observed[0][0] == b"0xxx1xxx2xxx3xxx4xxx"

    def test_large_streamed_response_body_is_captured(self):
        response = self.fetch("/large-stream")
        expected = b"".join(
            f"{index:02d}".encode() + (b"x" * 1_000)
            for index in range(20)
        )

        assert response.code == 200
        assert response.body == expected
        assert self.observed[0][0] == expected

    def test_duration_without_streaming_is_less_than_full_duration(self):
        response = self.fetch("/stream")

        assert response.code == 200
        assert self.observed[0][1] < self.observed[0][2]


class ResponseSizeInstrumentationTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/body", BodyHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.response_size(registry=self.registry)
        ).instrument(app)
        return app

    def test_response_size_observes_written_body_length(self):
        response = self.fetch("/body")

        assert response.code == 200
        assert response.body == b"123456789"
        assert (
            self.registry.get_sample_value(
                "http_response_size_bytes_sum",
                {"handler": "/body", "method": "GET", "status": "2xx"},
            )
            == 9
        )


class RuntimeErrorResponseSizeTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/runtime-error", RuntimeErrorHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.response_size(registry=self.registry)
        ).instrument(app)
        return app

    def test_response_size_records_5xx_for_runtime_error(self):
        response = self.fetch("/runtime-error", raise_error=False)

        assert response.code == 500
        assert (
            self.registry.get_sample_value(
                "http_response_size_bytes_count",
                {
                    "handler": "/runtime-error",
                    "method": "GET",
                    "status": "5xx",
                },
            )
            == 1
        )


class RuntimeErrorCombinedSizeTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/runtime-error", RuntimeErrorHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.combined_size(registry=self.registry)
        ).instrument(app)
        return app

    def test_combined_size_records_5xx_for_runtime_error(self):
        response = self.fetch("/runtime-error", raise_error=False)

        assert response.code == 500
        assert (
            self.registry.get_sample_value(
                "http_combined_size_bytes_count",
                {
                    "handler": "/runtime-error",
                    "method": "GET",
                    "status": "5xx",
                },
            )
            == 1
        )


class RuntimeErrorDefaultMetricsTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/runtime-error", RuntimeErrorHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.default(registry=self.registry)
        ).instrument(app)
        return app

    def test_default_metrics_record_5xx_for_runtime_error(self):
        response = self.fetch("/runtime-error", raise_error=False)

        assert response.code == 500
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {
                    "handler": "/runtime-error",
                    "method": "GET",
                    "status": "5xx",
                },
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_request_size_bytes_count",
                {"handler": "/runtime-error"},
            )
            == 1
        )
