import gzip
import inspect
import os
import re
import warnings
from enum import Enum
from typing import Any, Awaitable, Callable, List, Optional, Pattern, Sequence, Union, cast

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, Gauge
from prometheus_client.exposition import generate_latest
from prometheus_client import multiprocess
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import metrics
from prometheus_tornado_instrumentator import routing


class Instrumentator:
    """Public entry point for Tornado application instrumentation."""

    def __init__(
        self,
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_round_latency_decimals: bool = False,
        should_respect_env_var: bool = False,
        should_instrument_requests_inprogress: bool = False,
        should_exclude_streaming_duration: bool = False,
        excluded_handlers: List[str] = [],
        body_handlers: List[str] = [],
        round_latency_decimals: int = 4,
        env_var_name: str = "ENABLE_METRICS",
        inprogress_name: str = "http_requests_inprogress",
        inprogress_labels: bool = False,
        registry: Optional[CollectorRegistry] = None,
    ) -> None:
        self.should_group_status_codes = should_group_status_codes
        self.should_ignore_untemplated = should_ignore_untemplated
        self.should_group_untemplated = should_group_untemplated
        self.should_round_latency_decimals = should_round_latency_decimals
        self.should_respect_env_var = should_respect_env_var
        self.should_instrument_requests_inprogress = should_instrument_requests_inprogress
        self.should_exclude_streaming_duration = should_exclude_streaming_duration
        self.round_latency_decimals = round_latency_decimals
        self.env_var_name = env_var_name
        self.inprogress_name = inprogress_name
        self.inprogress_labels = inprogress_labels
        self.excluded_handlers: List[Pattern[str]] = [
            re.compile(handler) for handler in excluded_handlers
        ]
        self.body_handlers: List[Pattern[str]] = [
            re.compile(handler) for handler in body_handlers
        ]
        self.inprogress = None
        self.instrumentations: List[Callable[[metrics.Info], None]] = []
        self.async_instrumentations: List[
            Callable[[metrics.Info], Awaitable[None]]
        ] = []
        if registry:
            self.registry = registry
        else:
            self.registry = REGISTRY
        self._normalize_multiproc_env()
        self._validate_multiproc_dir()

    def add(
        self,
        *instrumentations: Optional[
            Callable[[metrics.Info], Union[None, Awaitable[None]]]
        ],
    ) -> "Instrumentator":
        for instrumentation in instrumentations:
            if instrumentation is None:
                continue
            if inspect.iscoroutinefunction(instrumentation):
                self.async_instrumentations.append(
                    cast(Callable[[metrics.Info], Awaitable[None]], instrumentation)
                )
            else:
                self.instrumentations.append(
                    cast(Callable[[metrics.Info], None], instrumentation)
                )
        return self

    def instrument(
        self,
        app: Application,
        metric_namespace: str = "",
        metric_subsystem: str = "",
        should_only_respect_2xx_for_highr: bool = False,
        latency_highr_buckets: Sequence[Union[float, str]] = (
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1,
            1.5,
            2,
            2.5,
            3,
            3.5,
            4,
            4.5,
            5,
            7.5,
            10,
            30,
            60,
        ),
        latency_lowr_buckets: Sequence[Union[float, str]] = (0.1, 0.5, 1),
    ) -> "Instrumentator":
        if not self._should_instrument():
            return self
        self._validate_multiproc_dir()
        self._ensure_inprogress_metric()
        if not self.instrumentations and not self.async_instrumentations:
            self.add(
                metrics.default(
                    metric_namespace=metric_namespace,
                    metric_subsystem=metric_subsystem,
                    should_only_respect_2xx_for_highr=(
                        should_only_respect_2xx_for_highr
                    ),
                    should_exclude_streaming_duration=(
                        self.should_exclude_streaming_duration
                    ),
                    latency_highr_buckets=latency_highr_buckets,
                    latency_lowr_buckets=latency_lowr_buckets,
                    registry=self.registry,
                )
            )

        routing.wrap_application_rules(self, app)
        routing.patch_add_handlers(self, app)

        return self

    def expose(
        self,
        app: Application,
        should_gzip: bool = False,
        endpoint: str = "/metrics",
        include_in_schema: bool = True,
        tags: Optional[List[Union[str, Enum]]] = None,
        **kwargs: Any,
    ) -> "Instrumentator":
        if not self._should_instrument():
            return self
        del include_in_schema, tags, kwargs
        registry = self.registry
        instrumentator = self

        class MetricsHandler(RequestHandler):
            def get(self):
                try:
                    instrumentator._validate_multiproc_dir(
                        prefix="env PROMETHEUS_MULTIPROC_DIR"
                    )
                except ValueError as error:
                    self.set_status(500)
                    self.write(str(error))
                    return
                output_registry = registry
                if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
                    output_registry = CollectorRegistry()
                    multiprocess.MultiProcessCollector(output_registry)
                output = generate_latest(output_registry)
                if should_gzip and "gzip" in self.request.headers.get(
                    "Accept-Encoding", ""
                ):
                    output = gzip.compress(output)
                    self.set_header("Content-Encoding", "gzip")
                self.set_header("Content-Type", CONTENT_TYPE_LATEST)
                self.write(output)

        app.add_handlers(r".*$", [(endpoint, MetricsHandler)])
        return self

    async def _run_async_instrumentation(self, awaitable) -> None:
        await awaitable

    def _ensure_inprogress_metric(self) -> None:
        if not self.should_instrument_requests_inprogress or self.inprogress is not None:
            return
        labelnames = ["method", "handler"] if self.inprogress_labels else []
        self.inprogress = Gauge(
            self.inprogress_name,
            "Number of HTTP requests in progress.",
            labelnames=labelnames,
            registry=self.registry,
            multiprocess_mode="livesum",
        )

    def _is_handler_excluded(self, handler_pattern: str) -> bool:
        return any(
            excluded_handler.search(handler_pattern)
            for excluded_handler in self.excluded_handlers
        )

    def _should_capture_body(self, handler_pattern: str) -> bool:
        return any(
            body_handler.search(handler_pattern)
            for body_handler in self.body_handlers
        )

    def _modified_handler(self, handler_pattern: str) -> Optional[str]:
        if handler_pattern != "none":
            return handler_pattern
        if self.should_ignore_untemplated:
            return None
        if self.should_group_untemplated:
            return "none"
        return handler_pattern

    def _inprogress_child(self, handler_pattern: str, method: str):
        if self.inprogress_labels:
            return self.inprogress.labels(method, handler_pattern)
        return self.inprogress

    def _should_instrument(self) -> bool:
        return (
            not self.should_respect_env_var
            or os.getenv(self.env_var_name, "False").lower() in ["true", "1"]
        )

    def _normalize_multiproc_env(self) -> None:
        if (
            "prometheus_multiproc_dir" in os.environ
            and "PROMETHEUS_MULTIPROC_DIR" not in os.environ
        ):
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = os.environ[
                "prometheus_multiproc_dir"
            ]
            warnings.warn(
                "prometheus_multiproc_dir variable has been deprecated in favor of "
                "the upper case naming PROMETHEUS_MULTIPROC_DIR",
                DeprecationWarning,
                stacklevel=2,
            )

    def _validate_multiproc_dir(
        self, prefix: str = "PROMETHEUS_MULTIPROC_DIR"
    ) -> None:
        multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        if multiproc_dir and not os.path.isdir(multiproc_dir):
            raise ValueError(f"{prefix}={multiproc_dir!r} not a directory")
