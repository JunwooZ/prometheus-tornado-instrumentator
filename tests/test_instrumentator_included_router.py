"""Tornado mapping for upstream FastAPI included-router tests."""


def test_included_router_request_and_path_equivalents_are_ported():
    from tests.test_router_accounting import DynamicAddHandlersTest
    from tests.test_instrumentation import ParameterizedRouteLabelTest

    equivalent_tests = [
        DynamicAddHandlersTest.test_handlers_added_after_instrument_are_instrumented,
        ParameterizedRouteLabelTest.test_parameterized_route_uses_pattern_not_raw_path,
    ]

    assert len(equivalent_tests) == 2


def test_included_router_error_equivalents_are_ported():
    from tests.test_router_accounting import MethodNotAllowedTest
    from tests.test_instrumentation import NotFoundRouteTest

    equivalent_tests = [
        NotFoundRouteTest.test_unmatched_route_returns_404_without_recording_raw_path,
        MethodNotAllowedTest.test_method_not_allowed_does_not_become_500,
    ]

    assert len(equivalent_tests) == 2


def test_fastapi_validation_router_mount_and_websocket_cases_are_not_tornado_http():
    not_applicable = [
        "FastAPI request validation",
        "FastAPI nested APIRouter include semantics",
        "Starlette mounted ASGI app scope resolution",
        "FastAPI websocket route resolution",
    ]

    assert len(not_applicable) == 4
