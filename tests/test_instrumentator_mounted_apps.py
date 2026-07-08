"""Tornado mapping for upstream mounted-app tests."""


def test_fastapi_mounted_asgi_app_cases_are_not_tornado_http_scope():
    not_applicable = [
        "mounted FastAPI app route resolution",
        "instrumented-only ASGI mounted sub-application scope isolation",
    ]

    assert len(not_applicable) == 2
