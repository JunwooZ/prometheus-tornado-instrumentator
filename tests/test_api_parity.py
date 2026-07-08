import inspect

from prometheus_tornado_instrumentator import Instrumentator, metrics


def test_instrumentator_constructor_matches_upstream_public_options():
    signature = inspect.signature(Instrumentator)

    assert list(signature.parameters) == [
        "should_group_status_codes",
        "should_ignore_untemplated",
        "should_group_untemplated",
        "should_round_latency_decimals",
        "should_respect_env_var",
        "should_instrument_requests_inprogress",
        "should_exclude_streaming_duration",
        "excluded_handlers",
        "body_handlers",
        "round_latency_decimals",
        "env_var_name",
        "inprogress_name",
        "inprogress_labels",
        "registry",
    ]
    assert signature.parameters["should_ignore_untemplated"].default is False
    assert signature.parameters["should_group_untemplated"].default is True
    assert signature.parameters["should_round_latency_decimals"].default is False
    assert signature.parameters["should_respect_env_var"].default is False
    assert signature.parameters["should_instrument_requests_inprogress"].default is False
    assert signature.parameters["should_exclude_streaming_duration"].default is False
    assert signature.parameters["excluded_handlers"].default == []
    assert signature.parameters["body_handlers"].default == []
    assert signature.parameters["round_latency_decimals"].default == 4
    assert signature.parameters["env_var_name"].default == "ENABLE_METRICS"
    assert (
        signature.parameters["inprogress_name"].default
        == "http_requests_inprogress"
    )
    assert signature.parameters["inprogress_labels"].default is False
    assert signature.parameters["registry"].default is None


def test_instrument_matches_upstream_public_options():
    signature = inspect.signature(Instrumentator.instrument)

    assert list(signature.parameters) == [
        "self",
        "app",
        "metric_namespace",
        "metric_subsystem",
        "should_only_respect_2xx_for_highr",
        "latency_highr_buckets",
        "latency_lowr_buckets",
    ]
    assert signature.parameters["metric_namespace"].default == ""
    assert signature.parameters["metric_subsystem"].default == ""
    assert (
        signature.parameters["should_only_respect_2xx_for_highr"].default
        is False
    )


def test_expose_matches_upstream_public_options():
    signature = inspect.signature(Instrumentator.expose)

    assert list(signature.parameters) == [
        "self",
        "app",
        "should_gzip",
        "endpoint",
        "include_in_schema",
        "tags",
        "kwargs",
    ]
    assert signature.parameters["should_gzip"].default is False
    assert signature.parameters["endpoint"].default == "/metrics"
    assert signature.parameters["include_in_schema"].default is True
    assert signature.parameters["tags"].default is None
    assert signature.parameters["kwargs"].kind == inspect.Parameter.VAR_KEYWORD


def test_metric_factories_match_upstream_public_defaults():
    assert (
        inspect.signature(metrics.requests).parameters["metric_name"].default
        == "http_requests_total"
    )
    assert (
        inspect.signature(metrics.requests).parameters["metric_doc"].default
        == "Total number of requests by method, status and handler."
    )

    for factory in (
        metrics.latency,
        metrics.request_size,
        metrics.response_size,
        metrics.combined_size,
        metrics.requests,
        metrics.default,
    ):
        assert (
            inspect.signature(factory).parameters["custom_labels"].default
            == {}
        )
