import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap

import pytest
from prometheus_client import CollectorRegistry, generate_latest
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator


def is_prometheus_multiproc_valid():
    return os.path.isdir(os.environ.get("PROMETHEUS_MULTIPROC_DIR", ""))


class PingHandler(RequestHandler):
    def get(self):
        self.write("pong")


class SleepHandler(RequestHandler):
    async def get(self):
        seconds = float(self.get_query_argument("seconds", "0.1"))
        await gen.sleep(seconds)
        self.write("slept")


@pytest.mark.skipif(
    is_prometheus_multiproc_valid(),
    reason="PROMETHEUS_MULTIPROC_DIR must be unset or invalid.",
)
def test_multiproc_dir_not_found(monkeypatch):
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/DOES/NOT/EXIST")

    app = Application([(r"/ping", PingHandler)])
    with pytest.raises(ValueError, match="not a directory"):
        Instrumentator().instrument(app)


@pytest.mark.skipif(
    is_prometheus_multiproc_valid(),
    reason="PROMETHEUS_MULTIPROC_DIR must be unset or invalid.",
)
def test_lowercase_multiproc_dir_is_supported_with_deprecation(monkeypatch, tmp_path):
    monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)
    monkeypatch.setenv("prometheus_multiproc_dir", str(tmp_path))

    with pytest.deprecated_call(match="prometheus_multiproc_dir"):
        Instrumentator(registry=CollectorRegistry())

    assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == str(tmp_path)
    os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)


def test_env_disabled_inprogress_metric_does_not_register(monkeypatch):
    monkeypatch.setenv("PROM_TORNADO_TEST_ENABLED", "false")
    registry = CollectorRegistry()

    app = Application([(r"/ping", PingHandler)])
    Instrumentator(
        registry=registry,
        should_respect_env_var=True,
        env_var_name="PROM_TORNADO_TEST_ENABLED",
        should_instrument_requests_inprogress=True,
    ).instrument(app)

    assert b"http_requests_inprogress" not in generate_latest(registry)


def test_inprogress_labels_match_upstream_order():
    registry = CollectorRegistry()
    app = Application([])
    instrumentator = Instrumentator(
        registry=registry,
        should_instrument_requests_inprogress=True,
        inprogress_labels=True,
    ).instrument(app)

    assert instrumentator.inprogress._labelnames == ("method", "handler")


@pytest.mark.skipif(
    is_prometheus_multiproc_valid(),
    reason="PROMETHEUS_MULTIPROC_DIR must be unset or invalid.",
)
class MultiprocExposeInvalidDirTest(AsyncHTTPTestCase):
    def get_app(self):
        self._old_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)
        app = Application([(r"/ping", PingHandler)])
        Instrumentator(registry=CollectorRegistry()).expose(app)
        return app

    def tearDown(self):
        if self._old_multiproc_dir is None:
            os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)
        else:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = self._old_multiproc_dir
        super().tearDown()

    def test_metrics_endpoint_reports_invalid_multiproc_dir(self):
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/DOES/NOT/EXIST"

        response = self.fetch("/metrics", raise_error=False)

        assert response.code == 500
        assert b"PROMETHEUS_MULTIPROC_DIR" in response.body


class InProgressGaugeTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/sleep", SleepHandler)])
        Instrumentator(
            registry=self.registry,
            should_instrument_requests_inprogress=True,
            inprogress_labels=True,
        ).instrument(app).expose(app)
        return app

    @gen_test
    async def test_inprogress_metric_counts_concurrent_requests(self):
        requests = [
            self.http_client.fetch(self.get_url("/sleep?seconds=0.2"))
            for _ in range(3)
        ]
        await gen.sleep(0.05)
        metrics_response = await self.http_client.fetch(self.get_url("/metrics"))
        await gen.multi(requests)

        body = metrics_response.body.decode()
        assert (
            'http_requests_inprogress{handler="/sleep",method="GET"} 3.0'
            in body
        )
        assert (
            'http_requests_inprogress{handler="/metrics",method="GET"} 1.0'
            in body
        )


class ExcludedHandlerLifecycleTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        self.observed = []

        def observe(info):
            self.observed.append(info.modified_handler)

        app = Application([(r"/sleep", SleepHandler)])
        Instrumentator(
            registry=self.registry,
            excluded_handlers=[r"/sleep"],
            body_handlers=[r"/sleep"],
            should_instrument_requests_inprogress=True,
            inprogress_labels=True,
        ).add(observe).instrument(app).expose(app)
        return app

    @gen_test
    async def test_excluded_handler_has_no_inprogress_or_observation_side_effects(self):
        request = self.http_client.fetch(self.get_url("/sleep?seconds=0.2"))
        await gen.sleep(0.05)
        metrics_response = await self.http_client.fetch(self.get_url("/metrics"))
        await request

        assert 'handler="/sleep"' not in metrics_response.body.decode()
        assert self.observed == ["/metrics"]


class CustomInProgressGaugeNameTest(AsyncHTTPTestCase):
    def get_app(self):
        self.registry = CollectorRegistry()
        app = Application([(r"/sleep", SleepHandler)])
        Instrumentator(
            registry=self.registry,
            should_instrument_requests_inprogress=True,
            inprogress_name="tornado_requests_inprogress",
        ).instrument(app).expose(app)
        return app

    @gen_test
    async def test_inprogress_metric_name_can_match_upstream_api_option(self):
        request = self.http_client.fetch(self.get_url("/sleep?seconds=0.2"))
        await gen.sleep(0.05)
        metrics_response = await self.http_client.fetch(self.get_url("/metrics"))
        await request

        body = metrics_response.body.decode()
        assert "tornado_requests_inprogress 2.0" in body
        assert "http_requests_inprogress" not in body


@pytest.mark.skipif(
    is_prometheus_multiproc_valid(),
    reason="PROMETHEUS_MULTIPROC_DIR must be unset before this test mutates it.",
)
class MultiprocExposeValidDirTest(AsyncHTTPTestCase):
    def get_app(self):
        self._old_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        self.tmpdir = tempfile.mkdtemp()
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = self.tmpdir
        app = Application([(r"/ping", PingHandler)])
        Instrumentator(registry=CollectorRegistry()).expose(app)
        return app

    def tearDown(self):
        if self._old_multiproc_dir is None:
            os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)
        else:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = self._old_multiproc_dir
        shutil.rmtree(self.tmpdir)
        super().tearDown()

    def test_metrics_endpoint_accepts_valid_multiproc_dir(self):
        response = self.fetch("/metrics", raise_error=False)

        assert response.code == 200
        assert response.body == b""


@pytest.mark.skipif(
    is_prometheus_multiproc_valid(),
    reason="PROMETHEUS_MULTIPROC_DIR must be unset before spawning child process.",
)
def test_multiproc_child_process_counts_requests_and_avoids_duplicates(tmp_path):
    env = os.environ.copy()
    env["PROMETHEUS_MULTIPROC_DIR"] = str(tmp_path)
    src_path = pathlib.Path(__file__).resolve().parents[1] / "src"
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(src_path), env.get("PYTHONPATH", "")) if part
    )
    code = textwrap.dedent(
        """
        import unittest

        from tornado.testing import AsyncHTTPTestCase
        from tornado.web import Application, RequestHandler

        from prometheus_tornado_instrumentator import Instrumentator


        class PingHandler(RequestHandler):
            def get(self):
                self.write("pong")


        class MultiprocSmokeTest(AsyncHTTPTestCase):
            def get_app(self):
                app = Application([(r"/ping", PingHandler)])
                Instrumentator().instrument(app).expose(app)
                return app

            def test_request_count_and_no_duplicate_type_lines(self):
                assert self.fetch("/ping").code == 200
                assert self.fetch("/ping").code == 200
                assert self.fetch("/ping").code == 200

                response = self.fetch("/metrics")
                body = response.body.decode()

                assert response.code == 200
                assert (
                    'http_requests_total{handler="/ping",method="GET",status="2xx"} 3.0'
                    in body
                ), body
                assert body.count("# TYPE http_requests_total counter") == 1, body
                assert "process_open_fds" not in body


        if __name__ == "__main__":
            unittest.main()
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=pathlib.Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
