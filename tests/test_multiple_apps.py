from prometheus_client import CollectorRegistry, Counter
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator, metrics


class DummyHandler(RequestHandler):
    def get(self):
        self.write("dummy")


class MultipleAppsCustomRegistryTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry1 = CollectorRegistry(auto_describe=True)
        self.registry2 = CollectorRegistry(auto_describe=True)
        self.app1 = Application([(r"/dummy", DummyHandler)])
        self.app2 = Application([(r"/dummy", DummyHandler)])

        Instrumentator(registry=self.registry1).instrument(self.app1).expose(self.app1)
        Instrumentator(registry=self.registry2).instrument(self.app2).expose(self.app2)
        Counter("app1_only", "Only in app1.", registry=self.registry1).inc()
        return self.app1

    def test_custom_registries_do_not_share_metrics(self):
        assert self.fetch("/dummy").code == 200

        assert (
            self.registry1.get_sample_value(
                "http_requests_total",
                {"handler": "/dummy", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry2.get_sample_value(
                "http_requests_total",
                {"handler": "/dummy", "method": "GET", "status": "2xx"},
            )
            is None
        )
        assert self.registry1.get_sample_value("app1_only_total") == 1
        assert self.registry2.get_sample_value("app1_only_total") is None


def test_multiple_apps_can_use_default_registry_without_duplicate_errors():
    app1 = Application([(r"/dummy", DummyHandler)])
    app2 = Application([(r"/dummy", DummyHandler)])

    Instrumentator().instrument(app1).expose(app1)
    Instrumentator().instrument(app2).expose(app2)


class FullDefaultMetricsTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/dummy", DummyHandler)])
        Instrumentator(registry=self.registry).add(
            metrics.default(registry=self.registry)
        ).instrument(app)
        return app

    def test_default_metric_closure_records_core_samples(self):
        assert self.fetch("/dummy").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"method": "GET", "status": "2xx", "handler": "/dummy"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_request_size_bytes_count", {"handler": "/dummy"}
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_response_size_bytes_count", {"handler": "/dummy"}
            )
            == 1
        )
        assert (
            self.registry.get_sample_value("http_request_duration_highr_seconds_count")
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_request_duration_seconds_count",
                {"method": "GET", "handler": "/dummy"},
            )
            == 1
        )


def test_multiple_apps_can_add_full_metric_set_without_duplicate_errors():
    app1 = Application([(r"/dummy", DummyHandler)])
    app2 = Application([(r"/dummy", DummyHandler)])

    Instrumentator().add(
        metrics.request_size(),
        metrics.requests(),
        metrics.combined_size(),
        metrics.response_size(),
        metrics.latency(),
        metrics.default(),
    ).instrument(app1).expose(app1)

    Instrumentator().add(
        metrics.request_size(),
        metrics.requests(),
        metrics.combined_size(),
        metrics.response_size(),
        metrics.latency(),
        metrics.default(),
    ).instrument(app2).expose(app2)
