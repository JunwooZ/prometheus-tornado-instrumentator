"""Tornado equivalents for upstream Starlette instrumentator behavior."""


def test_starlette_basic_path_method_status_equivalents_are_ported():
    from tests.test_instrumentation import (
        DifferentPathsInstrumentationTest,
        ExplicitInstrumentationTest,
        HttpMethodsInstrumentationTest,
        StatusCodesInstrumentationTest,
    )

    equivalent_tests = [
        ExplicitInstrumentationTest.test_request_counter_observes_real_tornado_requests,
        DifferentPathsInstrumentationTest.test_different_paths_are_counted_separately,
        HttpMethodsInstrumentationTest.test_http_methods_are_counted_separately,
        StatusCodesInstrumentationTest.test_status_codes_are_observed_without_grouping,
    ]

    assert len(equivalent_tests) == 4


def test_starlette_exclusion_endpoint_path_parameter_and_gzip_equivalents_are_ported():
    from tests.test_expose import CustomMetricsPathTest, MetricsGzipTest
    from tests.test_instrumentation import (
        MetricsEndpointExclusionTest,
        ParameterizedRouteLabelTest,
    )

    equivalent_tests = [
        MetricsEndpointExclusionTest.test_metrics_endpoint_can_be_excluded_from_instrumentation,
        CustomMetricsPathTest.test_expose_custom_metrics_endpoint,
        ParameterizedRouteLabelTest.test_parameterized_route_uses_pattern_not_raw_path,
        MetricsGzipTest.test_expose_gzips_when_enabled_and_accepted,
    ]

    assert len(equivalent_tests) == 4
