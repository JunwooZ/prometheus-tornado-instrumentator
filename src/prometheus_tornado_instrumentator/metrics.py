"""Ready-to-use metric functions for Tornado instrumentation."""

from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram, Summary


class Info:
    """Observation Info passed to instrumentation functions."""

    def __init__(
        self,
        request: Any,
        response: Any,
        method: str,
        modified_handler: str,
        modified_status: str,
        modified_duration: float,
        modified_duration_without_streaming: float = 0.0,
    ) -> None:
        self.request = request
        self.response = response
        self.method = method
        self.modified_handler = modified_handler
        self.modified_status = modified_status
        self.modified_duration = modified_duration
        self.modified_duration_without_streaming = modified_duration_without_streaming


class Response:
    """Response data exposed to instrumentation functions."""

    def __init__(
        self,
        headers: Any,
        body: bytes = b"",
        body_size: Optional[int] = None,
    ) -> None:
        self.headers = headers
        self.body = body
        self.body_size = body_size


def _build_label_attribute_names(
    should_include_handler: bool,
    should_include_method: bool,
    should_include_status: bool,
) -> Tuple[List[str], List[str]]:
    label_names = []
    info_attribute_names = []

    if should_include_handler:
        label_names.append("handler")
        info_attribute_names.append("modified_handler")

    if should_include_method:
        label_names.append("method")
        info_attribute_names.append("method")

    if should_include_status:
        label_names.append("status")
        info_attribute_names.append("modified_status")

    return label_names, info_attribute_names


def _is_duplicated_time_series(error: ValueError) -> bool:
    return any(
        map(
            error.args[0].__contains__,
            [
                "Duplicated timeseries in CollectorRegistry:",
                "Duplicated time series in CollectorRegistry:",
            ],
        )
    )


def _label_values(info: Info, info_attribute_names: List[str]) -> List[str]:
    return [getattr(info, name) for name in info_attribute_names]


def _add_custom_labels(
    label_names: List[str],
    custom_labels: dict,
) -> List[str]:
    for key in custom_labels:
        label_names.append(key)
    return list(custom_labels.values())


def _label_values_with_custom(
    info: Info,
    info_attribute_names: List[str],
    custom_label_values: List[str],
) -> List[str]:
    return _label_values(info, info_attribute_names) + custom_label_values


def _observe(metric: Any, label_values: List[str], value: float) -> None:
    if label_values:
        metric.labels(*label_values).observe(value)
    else:
        metric.observe(value)


def _inc(metric: Any, label_values: List[str]) -> None:
    if label_values:
        metric.labels(*label_values).inc()
    else:
        metric.inc()


def _content_length(carrier: Any) -> int:
    if carrier is None or not hasattr(carrier, "headers"):
        return 0
    content_length = carrier.headers.get("Content-Length")
    if content_length is not None:
        return int(content_length)
    return getattr(carrier, "body_size", 0) or 0


def _make_metric(
    metric_type: Any,
    metric_name: str,
    metric_doc: str,
    label_names: List[str],
    metric_namespace: str,
    metric_subsystem: str,
    registry: CollectorRegistry,
    **kwargs: Any,
) -> Optional[Any]:
    try:
        return metric_type(
            name=metric_name,
            documentation=metric_doc,
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            labelnames=label_names,
            registry=registry,
            **kwargs,
        )
    except ValueError as error:
        if not _is_duplicated_time_series(error):
            raise
        return None


def _make_counter(
    metric_name: str,
    metric_doc: str,
    label_names: List[str],
    metric_namespace: str,
    metric_subsystem: str,
    registry: CollectorRegistry,
) -> Optional[Counter]:
    return _make_metric(
        Counter, metric_name, metric_doc, label_names, metric_namespace,
        metric_subsystem, registry
    )


def _make_histogram(
    metric_name: str,
    metric_doc: str,
    label_names: List[str],
    metric_namespace: str,
    metric_subsystem: str,
    registry: CollectorRegistry,
    buckets: Sequence[Union[float, str]],
) -> Optional[Histogram]:
    return _make_metric(
        Histogram, metric_name, metric_doc, label_names, metric_namespace,
        metric_subsystem, registry, buckets=buckets
    )


def _make_summary(
    metric_name: str,
    metric_doc: str,
    label_names: List[str],
    metric_namespace: str,
    metric_subsystem: str,
    registry: CollectorRegistry,
) -> Optional[Summary]:
    return _make_metric(
        Summary, metric_name, metric_doc, label_names, metric_namespace,
        metric_subsystem, registry
    )


def request_size(
    metric_name: str = "http_request_size_bytes",
    metric_doc: str = "Content bytes of requests.",
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler=should_include_handler,
        should_include_method=should_include_method,
        should_include_status=should_include_status,
    )
    custom_label_values = _add_custom_labels(label_names, custom_labels)
    metric = _make_summary(
        metric_name,
        metric_doc,
        label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    if metric is None:
        return None

    def instrumentation(info: Info) -> None:
        _observe(
            metric,
            _label_values_with_custom(info, info_attribute_names, custom_label_values),
            _content_length(info.request),
        )

    return instrumentation


def response_size(
    metric_name: str = "http_response_size_bytes",
    metric_doc: str = "Content bytes of responses.",
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler=should_include_handler,
        should_include_method=should_include_method,
        should_include_status=should_include_status,
    )
    custom_label_values = _add_custom_labels(label_names, custom_labels)
    metric = _make_summary(
        metric_name,
        metric_doc,
        label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    if metric is None:
        return None

    def instrumentation(info: Info) -> None:
        _observe(
            metric,
            _label_values_with_custom(info, info_attribute_names, custom_label_values),
            _content_length(info.response),
        )

    return instrumentation


def combined_size(
    metric_name: str = "http_combined_size_bytes",
    metric_doc: str = "Content bytes of requests and responses.",
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler=should_include_handler,
        should_include_method=should_include_method,
        should_include_status=should_include_status,
    )
    custom_label_values = _add_custom_labels(label_names, custom_labels)
    metric = _make_summary(
        metric_name,
        metric_doc,
        label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    if metric is None:
        return None

    def instrumentation(info: Info) -> None:
        _observe(
            metric,
            _label_values_with_custom(info, info_attribute_names, custom_label_values),
            _content_length(info.request) + _content_length(info.response),
        )

    return instrumentation


def latency(
    metric_name: str = "http_request_duration_seconds",
    metric_doc: str = "Duration of HTTP requests in seconds",
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
    should_exclude_streaming_duration: bool = False,
    buckets: Sequence[Union[float, str]] = Histogram.DEFAULT_BUCKETS,
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler=should_include_handler,
        should_include_method=should_include_method,
        should_include_status=should_include_status,
    )
    custom_label_values = _add_custom_labels(label_names, custom_labels)
    metric = _make_histogram(
        metric_name,
        metric_doc,
        label_names,
        metric_namespace,
        metric_subsystem,
        registry,
        buckets,
    )
    if metric is None:
        return None

    def instrumentation(info: Info) -> None:
        duration = (
            info.modified_duration_without_streaming
            if should_exclude_streaming_duration
            else info.modified_duration
        )
        _observe(
            metric,
            _label_values_with_custom(info, info_attribute_names, custom_label_values),
            duration,
        )

    return instrumentation


def requests(
    metric_name: str = "http_requests_total",
    metric_doc: str = "Total number of requests by method, status and handler.",
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler=should_include_handler,
        should_include_method=should_include_method,
        should_include_status=should_include_status,
    )
    custom_label_values = _add_custom_labels(label_names, custom_labels)
    metric = _make_counter(
        metric_name,
        metric_doc,
        label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    if metric is None:
        return None

    def instrumentation(info: Info) -> None:
        _inc(
            metric,
            _label_values_with_custom(info, info_attribute_names, custom_label_values),
        )

    return instrumentation


def default(
    metric_namespace: str = "",
    metric_subsystem: str = "",
    should_only_respect_2xx_for_highr: bool = False,
    should_exclude_streaming_duration: bool = False,
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
    registry: CollectorRegistry = REGISTRY,
    custom_labels: dict = {},
) -> Optional[Callable[[Info], None]]:
    custom_labels = custom_labels or {}
    custom_label_names = list(custom_labels.keys())
    custom_label_values = list(custom_labels.values())
    if latency_highr_buckets[-1] != float("inf"):
        latency_highr_buckets = [*latency_highr_buckets, float("inf")]
    if latency_lowr_buckets[-1] != float("inf"):
        latency_lowr_buckets = [*latency_lowr_buckets, float("inf")]

    total = _make_counter(
        "http_requests",
        "Total number of requests by method, status and handler.",
        ["method", "status", "handler"] + custom_label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    request_summary = _make_summary(
        "http_request_size_bytes",
        "Content length of incoming requests by handler.",
        ["handler"] + custom_label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    response_summary = _make_summary(
        "http_response_size_bytes",
        "Content length of outgoing responses by handler.",
        ["handler"] + custom_label_names,
        metric_namespace,
        metric_subsystem,
        registry,
    )
    latency_highr = _make_histogram(
        "http_request_duration_highr_seconds",
        "Latency with many buckets but no API specific labels.",
        [],
        metric_namespace,
        metric_subsystem,
        registry,
        latency_highr_buckets,
    )
    latency_lowr = _make_histogram(
        "http_request_duration_seconds",
        "Latency with few buckets by handler and method.",
        ["method", "handler"] + custom_label_names,
        metric_namespace,
        metric_subsystem,
        registry,
        latency_lowr_buckets,
    )

    if None in (
        total,
        request_summary,
        response_summary,
        latency_highr,
        latency_lowr,
    ):
        return None

    def instrumentation(info: Info) -> None:
        duration = (
            info.modified_duration_without_streaming
            if should_exclude_streaming_duration
            else info.modified_duration
        )
        total.labels(
            info.method,
            info.modified_status,
            info.modified_handler,
            *custom_label_values,
        ).inc()
        request_summary.labels(info.modified_handler, *custom_label_values).observe(
            _content_length(info.request)
        )
        response_summary.labels(info.modified_handler, *custom_label_values).observe(
            _content_length(info.response)
        )
        if (
            not should_only_respect_2xx_for_highr
            or info.modified_status.startswith("2")
        ):
            latency_highr.observe(duration)
        latency_lowr.labels(
            info.method, info.modified_handler, *custom_label_values
        ).observe(duration)

    return instrumentation
