from prometheus_client import CollectorRegistry
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator


class ReadyHandler(RequestHandler):
    def get(self):
        self.write("ready")


class LateHandler(RequestHandler):
    def get(self):
        self.write("late")


class DynamicAddHandlersTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/ready", ReadyHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        app.add_handlers(r".*$", [(r"/late", LateHandler)])
        return app

    def test_handlers_added_after_instrument_are_instrumented(self):
        assert self.fetch("/ready").code == 200
        assert self.fetch("/late").code == 200

        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/ready", "method": "GET", "status": "2xx"},
            )
            == 1
        )
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/late", "method": "GET", "status": "2xx"},
            )
            == 1
        )


class MultipleInstrumentatorsTest(AsyncHTTPTestCase):
    def get_app(self):
        self.first_registry = CollectorRegistry()
        self.second_registry = CollectorRegistry()
        app = Application([(r"/ready", ReadyHandler)])
        Instrumentator(registry=self.first_registry).instrument(app)
        Instrumentator(registry=self.second_registry).instrument(app)
        app.add_handlers(r".*$", [(r"/late", LateHandler)])
        return app

    def test_multiple_instrumentators_observe_existing_and_late_handlers(self):
        assert self.fetch("/ready").code == 200
        assert self.fetch("/late").code == 200

        for registry in (self.first_registry, self.second_registry):
            assert (
                registry.get_sample_value(
                    "http_requests_total",
                    {"handler": "/ready", "method": "GET", "status": "2xx"},
                )
                == 1
            )
            assert (
                registry.get_sample_value(
                    "http_requests_total",
                    {"handler": "/late", "method": "GET", "status": "2xx"},
                )
                == 1
            )


class MethodNotAllowedTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/ready", ReadyHandler)])
        Instrumentator(registry=self.registry).instrument(app)
        return app

    def test_method_not_allowed_does_not_become_500(self):
        response = self.fetch("/ready", method="POST", body="", raise_error=False)

        assert response.code == 405
        assert (
            self.registry.get_sample_value(
                "http_requests_total",
                {"handler": "/ready", "method": "POST", "status": "4xx"},
            )
            == 1
        )
