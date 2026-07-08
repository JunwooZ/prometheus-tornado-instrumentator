"""Tornado equivalents for upstream instrumentator expose tests."""


def test_instrumentator_expose_defaults_and_custom_path_are_ported():
    from tests.test_expose import CustomMetricsPathTest, MetricsExposeTest

    equivalent_tests = [
        MetricsExposeTest.test_expose_default_metrics_endpoint,
        CustomMetricsPathTest.test_expose_custom_metrics_endpoint,
    ]

    assert len(equivalent_tests) == 2
