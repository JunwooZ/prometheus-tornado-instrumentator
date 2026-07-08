from prometheus_client import CollectorRegistry

from prometheus_tornado_instrumentator import metrics


class HeaderCarrier:
    def __init__(self, headers):
        self.headers = headers


def make_info(
    *,
    method="GET",
    handler="/items/{item_id}",
    status="2xx",
    duration=0.25,
    request_headers=None,
    response_headers=None,
):
    return metrics.Info(
        request=HeaderCarrier(request_headers or {}),
        response=HeaderCarrier(response_headers or {}),
        method=method,
        modified_handler=handler,
        modified_status=status,
        modified_duration=duration,
        modified_duration_without_streaming=duration / 2,
    )


def test_is_duplicated_time_series():
    error = ValueError("xx Duplicated timeseries in CollectorRegistry: xx")
    assert metrics._is_duplicated_time_series(error)

    error = ValueError("xx Duplicated time series in CollectorRegistry: xx")
    assert metrics._is_duplicated_time_series(error)

    error = ValueError("xx xx")
    assert not metrics._is_duplicated_time_series(error)


def test_observation_info_attributes_exist():
    info = metrics.Info(
        request=None,
        response=None,
        method=None,
        modified_duration=None,
        modified_status=None,
        modified_handler=None,
    )

    assert info.request is None
    assert info.response is None
    assert info.method is None
    assert info.modified_duration is None
    assert info.modified_status is None
    assert info.modified_handler is None
    assert info.modified_duration_without_streaming == 0.0


def test_api_throwing_error(monkeypatch):
    def raise_non_duplicate_error(*args, **kwargs):
        raise ValueError("not a duplicate collector error")

    monkeypatch.setattr(metrics, "Counter", raise_non_duplicate_error)

    try:
        metrics.requests(registry=CollectorRegistry())
    except ValueError as error:
        assert str(error) == "not a duplicate collector error"
    else:
        raise AssertionError("Expected non-duplicate collector errors to propagate")


def test_build_label_attribute_names_all_false():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )

    assert label_names == []
    assert info_attribute_names == []


def test_build_label_attribute_names_all_true():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
    )

    assert label_names == ["handler", "method", "status"]
    assert info_attribute_names == [
        "modified_handler",
        "method",
        "modified_status",
    ]


def test_build_label_attribute_names_mixed():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
    )

    assert label_names == ["handler", "status"]
    assert info_attribute_names == ["modified_handler", "modified_status"]


def test_latency_observes_duration_with_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.latency(registry=registry)

    instrumentation(make_info())

    assert (
        registry.get_sample_value(
            "http_request_duration_seconds_sum",
            {"handler": "/items/{item_id}", "method": "GET", "status": "2xx"},
        )
        == 0.25
    )


def test_latency_can_disable_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.latency(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(make_info())

    assert registry.get_sample_value("http_request_duration_seconds_sum", {}) == 0.25


def test_requests_increments_counter_with_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.requests(registry=registry)

    instrumentation(make_info())

    assert (
        registry.get_sample_value(
            "http_requests_total",
            {"handler": "/items/{item_id}", "method": "GET", "status": "2xx"},
        )
        == 1
    )


def test_requests_can_disable_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.requests(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(make_info())
    instrumentation(make_info())

    assert registry.get_sample_value("http_requests_total", {}) == 2


def test_requests_can_include_custom_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.requests(
        custom_labels={"deployment": "test"},
        registry=registry,
    )

    instrumentation(make_info())

    assert (
        registry.get_sample_value(
            "http_requests_total",
            {
                "handler": "/items/{item_id}",
                "method": "GET",
                "status": "2xx",
                "deployment": "test",
            },
        )
        == 1
    )


def test_request_size_observes_content_length():
    registry = CollectorRegistry()
    instrumentation = metrics.request_size(registry=registry)

    instrumentation(make_info(request_headers={"Content-Length": "123"}))

    assert (
        registry.get_sample_value(
            "http_request_size_bytes_sum",
            {"handler": "/items/{item_id}", "method": "GET", "status": "2xx"},
        )
        == 123
    )


def test_request_size_observes_zero_without_content_length():
    registry = CollectorRegistry()
    instrumentation = metrics.request_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(make_info(request_headers={}))

    assert registry.get_sample_value("http_request_size_bytes_sum", {}) == 0


def test_response_size_observes_content_length():
    registry = CollectorRegistry()
    instrumentation = metrics.response_size(registry=registry)

    instrumentation(make_info(response_headers={"Content-Length": "456"}))

    assert (
        registry.get_sample_value(
            "http_response_size_bytes_sum",
            {"handler": "/items/{item_id}", "method": "GET", "status": "2xx"},
        )
        == 456
    )


def test_response_size_can_disable_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.response_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(make_info(response_headers={"Content-Length": "456"}))

    assert registry.get_sample_value("http_response_size_bytes_sum", {}) == 456


def test_combined_size_observes_request_and_response_content_lengths():
    registry = CollectorRegistry()
    instrumentation = metrics.combined_size(registry=registry)

    instrumentation(
        make_info(
            request_headers={"Content-Length": "123"},
            response_headers={"Content-Length": "456"},
        )
    )

    assert (
        registry.get_sample_value(
            "http_combined_size_bytes_sum",
            {"handler": "/items/{item_id}", "method": "GET", "status": "2xx"},
        )
        == 579
    )


def test_combined_size_can_disable_all_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.combined_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(
        make_info(
            request_headers={"Content-Length": "123"},
            response_headers={"Content-Length": "456"},
        )
    )

    assert registry.get_sample_value("http_combined_size_bytes_sum", {}) == 579


def test_combined_size_observes_zero_for_missing_lengths():
    registry = CollectorRegistry()
    instrumentation = metrics.combined_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        registry=registry,
    )

    instrumentation(make_info())

    assert registry.get_sample_value("http_combined_size_bytes_sum", {}) == 0


def test_metric_namespace_and_subsystem_prefix_metric_name():
    registry = CollectorRegistry()
    instrumentation = metrics.request_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        metric_namespace="namespace",
        metric_subsystem="subsystem",
        registry=registry,
    )

    instrumentation(make_info(request_headers={"Content-Length": "123"}))

    assert (
        registry.get_sample_value(
            "namespace_subsystem_http_request_size_bytes_sum", {}
        )
        == 123
    )
    assert registry.get_sample_value("http_request_size_bytes_sum", {}) is None


def test_latency_can_observe_duration_without_streaming():
    registry = CollectorRegistry()
    instrumentation = metrics.latency(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        should_exclude_streaming_duration=True,
        registry=registry,
    )

    instrumentation(make_info(duration=0.4))

    assert registry.get_sample_value("http_request_duration_seconds_sum", {}) == 0.2


def test_latency_accepts_buckets_without_explicit_infinity():
    registry = CollectorRegistry()
    instrumentation = metrics.latency(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
        buckets=(0.1, 0.2, 0.3),
        registry=registry,
    )

    instrumentation(make_info(duration=0.25))

    assert (
        registry.get_sample_value(
            "http_request_duration_seconds_bucket", {"le": "+Inf"}
        )
        == 1
    )


def test_default_high_resolution_latency_can_only_respect_2xx():
    registry = CollectorRegistry()
    instrumentation = metrics.default(
        should_only_respect_2xx_for_highr=True,
        registry=registry,
    )

    instrumentation(make_info(status="4xx"))

    assert registry.get_sample_value("http_request_duration_highr_seconds_count") == 0


def test_default_high_resolution_latency_can_include_non_2xx():
    registry = CollectorRegistry()
    instrumentation = metrics.default(
        should_only_respect_2xx_for_highr=False,
        registry=registry,
    )

    instrumentation(make_info(status="4xx"))
    instrumentation(make_info(status="5xx"))

    assert registry.get_sample_value("http_request_duration_highr_seconds_count") == 2


def test_default_records_core_metric_samples():
    registry = CollectorRegistry()
    instrumentation = metrics.default(registry=registry)

    instrumentation(
        make_info(
            request_headers={"Content-Length": "123"},
            response_headers={"Content-Length": "456"},
        )
    )

    assert (
        registry.get_sample_value(
            "http_requests_total",
            {"method": "GET", "status": "2xx", "handler": "/items/{item_id}"},
        )
        == 1
    )
    assert (
        registry.get_sample_value(
            "http_request_size_bytes_sum", {"handler": "/items/{item_id}"}
        )
        == 123
    )
    assert (
        registry.get_sample_value(
            "http_response_size_bytes_sum", {"handler": "/items/{item_id}"}
        )
        == 456
    )
    assert registry.get_sample_value("http_request_duration_highr_seconds_count") == 1
    assert (
        registry.get_sample_value(
            "http_request_duration_seconds_count",
            {"method": "GET", "handler": "/items/{item_id}"},
        )
        == 1
    )


def test_default_can_observe_duration_without_streaming():
    registry = CollectorRegistry()
    instrumentation = metrics.default(
        should_exclude_streaming_duration=True,
        registry=registry,
    )

    instrumentation(make_info(duration=0.4))

    assert (
        registry.get_sample_value(
            "http_request_duration_seconds_sum",
            {"method": "GET", "handler": "/items/{item_id}"},
        )
        == 0.2
    )


def test_default_can_include_custom_labels():
    registry = CollectorRegistry()
    instrumentation = metrics.default(
        custom_labels={"deployment": "test"},
        registry=registry,
    )

    instrumentation(make_info())

    assert (
        registry.get_sample_value(
            "http_requests_total",
            {
                "method": "GET",
                "status": "2xx",
                "handler": "/items/{item_id}",
                "deployment": "test",
            },
        )
        == 1
    )
    assert (
        registry.get_sample_value(
            "http_request_duration_seconds_count",
            {
                "method": "GET",
                "handler": "/items/{item_id}",
                "deployment": "test",
            },
        )
        == 1
    )


def test_metric_factories_return_none_for_duplicate_collectors():
    registry = CollectorRegistry()

    assert metrics.requests(registry=registry) is not None
    assert metrics.requests(registry=registry) is None

    assert metrics.latency(registry=registry) is not None
    assert metrics.latency(registry=registry) is None

    assert metrics.request_size(registry=registry) is not None
    assert metrics.request_size(registry=registry) is None

    assert metrics.response_size(registry=registry) is not None
    assert metrics.response_size(registry=registry) is None

    assert metrics.combined_size(registry=registry) is not None
    assert metrics.combined_size(registry=registry) is None


def test_default_returns_none_when_collectors_already_exist():
    registry = CollectorRegistry()

    assert metrics.default(registry=registry) is not None
    assert metrics.default(registry=registry) is None
