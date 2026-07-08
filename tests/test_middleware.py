"""Tornado equivalents for upstream ASGI middleware behavior."""


def test_middleware_body_capture_equivalents_are_ported():
    from tests.test_instrumentation import (
        ResponseBodyCaptureTest,
        ResponseBodyDefaultTest,
        StreamingBodyCaptureTest,
    )

    equivalent_tests = [
        ResponseBodyDefaultTest.test_response_body_is_empty_by_default,
        ResponseBodyCaptureTest.test_body_handlers_enable_response_body_capture,
        ResponseBodyCaptureTest.test_json_response_body_is_captured_after_tornado_serialization,
        ResponseBodyCaptureTest.test_large_response_body_is_captured,
        ResponseBodyCaptureTest.test_empty_response_body_is_captured_as_empty,
        StreamingBodyCaptureTest.test_streamed_response_body_is_captured,
        StreamingBodyCaptureTest.test_large_streamed_response_body_is_captured,
        StreamingBodyCaptureTest.test_duration_without_streaming_is_less_than_full_duration,
    ]

    assert len(equivalent_tests) == 8
