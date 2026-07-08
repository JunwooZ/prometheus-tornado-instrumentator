from prometheus_client import CollectorRegistry, Counter
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator


class RootHandler(RequestHandler):
    def get(self):
        self.write("ok")


class MetricsExposeTest(AsyncHTTPTestCase):
    def get_app(self):
        registry = CollectorRegistry()
        Counter("demo_total", "Demo counter.", registry=registry).inc()
        app = Application([(r"/", RootHandler)])
        Instrumentator(registry=registry).expose(app)
        return app

    def test_expose_default_metrics_endpoint(self):
        response = self.fetch("/metrics")

        assert response.code == 200
        assert b"demo_total 1.0" in response.body
        assert "text/plain" in response.headers["Content-Type"]


class CustomMetricsPathTest(AsyncHTTPTestCase):
    def get_app(self):
        registry = CollectorRegistry()
        Counter("custom_demo_total", "Demo counter.", registry=registry).inc()
        app = Application([(r"/", RootHandler)])
        Instrumentator(registry=registry).expose(app, endpoint="/custom-metrics")
        return app

    def test_expose_custom_metrics_endpoint(self):
        response = self.fetch("/custom-metrics")

        assert response.code == 200
        assert b"custom_demo_total 1.0" in response.body


class UpstreamExposeSignatureOptionsTest(AsyncHTTPTestCase):
    def get_app(self):
        registry = CollectorRegistry()
        Counter("signature_demo_total", "Demo counter.", registry=registry).inc()
        app = Application([(r"/", RootHandler)])
        Instrumentator(registry=registry).expose(
            app,
            endpoint="/metrics",
            include_in_schema=False,
            tags=["metrics"],
            name="prometheus_metrics",
        )
        return app

    def test_expose_accepts_upstream_fastapi_options_as_noops(self):
        response = self.fetch("/metrics")

        assert response.code == 200
        assert b"signature_demo_total 1.0" in response.body


class MetricsGzipTest(AsyncHTTPTestCase):
    def get_app(self):
        registry = CollectorRegistry()
        Counter("gzip_demo_total", "Demo counter.", registry=registry).inc()
        app = Application([(r"/", RootHandler)])
        Instrumentator(registry=registry).expose(app, should_gzip=True)
        return app

    def test_expose_gzips_when_enabled_and_accepted(self):
        response = self.fetch(
            "/metrics",
            headers={"Accept-Encoding": "gzip"},
            decompress_response=False,
        )

        assert response.code == 200
        assert response.headers["Content-Encoding"] == "gzip"


class MetricsNoGzipTest(AsyncHTTPTestCase):
    def get_app(self):
        registry = CollectorRegistry()
        Counter("no_gzip_demo_total", "Demo counter.", registry=registry).inc()
        app = Application([(r"/", RootHandler)])
        Instrumentator(registry=registry).expose(app, should_gzip=False)
        return app

    def test_expose_does_not_gzip_when_disabled(self):
        response = self.fetch(
            "/metrics",
            headers={"Accept-Encoding": "gzip"},
            decompress_response=False,
        )

        assert response.code == 200
        assert "Content-Encoding" not in response.headers
        assert b"no_gzip_demo_total 1.0" in response.body
