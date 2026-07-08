# Upstream Test Parity Matrix

Source: `trallnag/prometheus-fastapi-instrumentator`, `master`, inspected from the upstream `tests/` directory.

The completion bar for this port is not "the code exists"; it is "the Tornado port's full semantic-equivalent test suite passes." Every upstream test must be either ported to a Tornado-equivalent test or explicitly marked not applicable with a reason.

## Summary

| Upstream file | Count | Tornado parity route | First-version target |
| --- | ---: | --- | --- |
| `test_metrics.py` | 31 | Mostly direct port; replace Starlette request/response objects with Tornado-compatible `Observation Info` fixtures. | Covered by `tests/test_metrics.py` and runtime error cases in `tests/test_instrumentation.py`. |
| `test_instrumentation.py` | 24 | Port to Tornado `Application`, handler wrapper, and Tornado test client. | Covered by `tests/test_instrumentation.py`; FastAPI validation-only semantics are not applicable. |
| `test_middleware.py` | 7 | Port as handler-wrapper lifecycle/body-capture tests. | Covered by body-capture tests in `tests/test_instrumentation.py` and traceability checks in `tests/test_middleware.py`. |
| `test_expose.py` | 3 | Port to Tornado `/metrics` handler behavior. | Covered by `tests/test_expose.py`; FastAPI/Starlette app type variants collapse to Tornado app expose. |
| `test_instrumentator_expose.py` | 2 | Port expose defaults and custom endpoint. | Covered by `tests/test_expose.py`. |
| `test_instrumentator_multiple_apps.py` | 3 | Port multiple Tornado applications and custom registries. | Covered by `tests/test_multiple_apps.py`. |
| `test_instrumentator_multiproc.py` | 7 | Port Prometheus multiprocess behavior; may remain env-gated. | Covered by `tests/test_multiprocess.py`, including a child-process multiprocess smoke. |
| `test_instrumentator_starlette.py` | 8 | Starlette-specific file; port generic behavior to Tornado path/method/status/exclusion/gzip tests. | Covered semantically by Tornado path/method/status/exclusion/custom-endpoint/gzip tests and traceability checks. |
| `test_instrumentator_included_router.py` | 9 | FastAPI router-specific file; port handler representation and nested route semantics where Tornado has equivalents. | Tornado equivalents covered by behavior tests and traceability checks; FastAPI validation/router/mount/websocket-only cases marked not applicable below. |
| `test_instrumentator_mounted_apps.py` | 2 | FastAPI mounted-app-specific file; port only if Tornado sub-application routing is supported, otherwise mark not applicable. | Not applicable for first version; no nested ASGI mounted app support is promised. |
| `test_markers.py` | 2 | Pytest marker sanity tests. | Covered by `tests/test_markers.py`. |

Total upstream tests accounted for: 98. See [`docs/upstream-case-audit.md`](upstream-case-audit.md) for the per-case audit.

Current local verification: `uv run --extra dev python -m pytest -q` passes with 105 tests.

## Parity Rules

- Do not run upstream FastAPI tests unchanged as the success metric.
- Do port every upstream behavior into a Tornado-semantic test when Tornado has an equivalent concept.
- Do record "not applicable" only for framework features that Tornado does not expose or that the project intentionally does not support.
- Do not mark the port complete while any required Tornado-equivalent test is failing.

## File-Level Mapping

### `test_metrics.py`

Behavior: metric closure behavior, label construction, duplicated time series handling, request/response size metrics, latency metrics, default metrics, custom labels, and request counters.

Tornado route: keep the metric closure API and assertions; build `Observation Info` fixtures around Tornado request/response equivalents instead of Starlette objects.

Tests:

- `test_is_duplicated_time_series` -> direct port.
- `test_existence_of_attributes` -> direct port with Tornado-shaped `Observation Info`.
- `test_build_label_attribute_names_all_false` -> direct port.
- `test_build_label_attribute_names_all_true` -> direct port.
- `test_build_label_attribute_names_mixed` -> direct port.
- `test_api_throwing_error` -> direct port.
- `test_request_size_all_labels` -> Tornado info fixture.
- `test_request_size_no_labels` -> Tornado info fixture.
- `test_namespace_subsystem` -> direct port.
- `test_request_size_no_cl` -> Tornado request without `Content-Length`.
- `test_response_size_all_labels` -> Tornado response fixture.
- `test_response_size_no_labels` -> Tornado response fixture.
- `test_response_size_with_runtime_error` -> direct port.
- `test_combined_size_all_labels` -> Tornado info fixture.
- `test_combined_size_all_labels_with_data` -> Tornado info fixture.
- `test_combined_size_no_labels` -> Tornado info fixture.
- `test_combined_size_with_runtime_error` -> direct port.
- `test_latency_all_labels` -> direct port.
- `test_latency_no_labels` -> direct port.
- `test_latency_with_bucket_no_inf` -> direct port.
- `test_latency_duration_without_streaming` -> covered by wrapper first-write duration tests.
- `test_default` -> direct port.
- `test_default_should_only_respect_2xx_for_highr` -> direct port.
- `test_default_should_not_only_respect_2xx_for_highr` -> direct port.
- `test_default_with_runtime_error` -> direct port.
- `test_default_duration_without_streaming` -> covered by default metrics streaming-duration exclusion tests.
- `test_custom_labels` -> direct port.
- `test_request_all_labels` -> direct port.
- `test_request_no_labels` -> direct port.
- `test_request_custom_namespace` -> direct port.
- `test_request_mount_redirection_bug` -> not applicable for first version; this is a FastAPI/Starlette `Mount` trailing-slash redirect bug, and the Tornado port does not expose ASGI mount routing.

### `test_instrumentation.py`

Behavior: end-to-end application instrumentation, metrics endpoint availability, gzip, metric names, status grouping, untemplated route handling, exclusions, buckets, env-var gating, latency rounding, and custom async/sync instrumentation.

Tornado route: use Tornado `Application` with representative handlers and the generated instrumented handler wrapper.

Tests:

- `test_app` -> Tornado app sanity test.
- `test_metrics_endpoint_availability` -> Tornado `/metrics` availability.
- `test_gzip_accepted` -> Tornado metrics endpoint gzip.
- `test_gzip_not_accepted` -> Tornado metrics endpoint without gzip.
- `test_default_metric_name` -> direct behavior.
- `test_default_without_add` -> default instrumentation behavior.
- `test_custom_metric_name` -> direct behavior.
- `test_grouped_status_codes` -> Tornado status grouping.
- `test_grouped_status_codes_with_enumeration` -> Tornado status grouping with `HTTPStatus`.
- `test_ungrouped_status_codes` -> Tornado status labels without grouping.
- `test_ignore_untemplated` -> covered by Tornado unmatched-route non-recording policy.
- `test_dont_ignore_untemplated_ungrouped` -> not applicable for first version; unmatched Tornado requests do not enter a wrapped registered `RequestHandler`, so the port intentionally does not expose raw unmatched paths as metric labels.
- `test_grouping_untemplated` -> not applicable for first version; unmatched Tornado requests are ignored rather than grouped as `none`.
- `test_excluding_handlers` -> regex/path exclusion.
- `test_excluding_handlers_regex` -> regex exclusion.
- `test_excluded_handlers_none` -> no exclusion.
- `test_bucket_without_inf` -> histogram bucket behavior.
- `test_should_respect_env_var_existence_exists` -> env-var gating.
- `test_should_respect_env_var_existence_not_exists` -> env-var gating.
- `test_entropy` -> not applicable; it is a helper sanity check for the upstream rounding heuristic, while the Tornado port directly asserts rounded `Info` durations.
- `test_default_no_rounding` -> latency rounding disabled.
- `test_rounding` -> latency rounding enabled.
- `test_custom_async_instrumentation` -> async instrumentation callback.
- `test_add_sync_instrumentation_does_not_warn_deprecated_coroutine_check` -> sync callback path.

### `test_middleware.py`

Behavior: response body capture and duration without streaming.

Tornado route: these become handler-wrapper tests because Tornado does not use ASGI middleware.

Tests:

- `test_info_body_default` -> default empty `info.response.body`.
- `test_info_body_empty` -> body capture with empty response.
- `test_info_body_stream_small` -> streaming response body capture.
- `test_info_body_stream_large` -> large streaming response body capture.
- `test_info_body_bulk_small` -> normal small response body capture.
- `test_info_body_bulk_large` -> normal large response body capture.
- `test_info_body_duration_without_streaming` -> first-write duration vs full duration.

### `test_expose.py`

Behavior: metrics endpoint content type and app support.

Tornado route: all become Tornado expose tests.

Tests:

- `test_expose_default_content_type` -> Tornado content type is valid and not duplicated.
- `test_fastapi_app_expose` -> replace with Tornado app expose.
- `test_starlette_app_expose` -> not applicable as Starlette; covered by Tornado app expose.

### `test_instrumentator_expose.py`

Behavior: expose defaults and custom metrics path.

Tornado route: direct Tornado endpoint tests.

Tests:

- `test_expose_defaults` -> default `/metrics`.
- `test_expose_custom_path` -> custom endpoint path.

### `test_instrumentator_multiple_apps.py`

Behavior: multiple applications, custom registries, no duplicate metric registration.

Tornado route: direct Tornado multi-application tests.

Tests:

- `test_multiple_apps_custom_registry` -> separate Tornado apps and registries.
- `test_multiple_apps_expose_defaults` -> separate Tornado apps using default registry behavior.
- `test_multiple_apps_expose_full` -> all built-in metric closures across multiple apps.

### `test_instrumentator_multiproc.py`

Behavior: Prometheus multiprocess env handling, metrics endpoint behavior, in-progress metric, and duplicate prevention.

Tornado route: port with Tornado app and env-gated pytest markers.

Tests:

- `test_multiproc_dir_not_found` -> invalid `PROMETHEUS_MULTIPROC_DIR` fails early.
- `test_multiproc_expose_no_dir` -> invalid multiprocess dir fails from expose endpoint.
- `test_multiproc_anti_test` -> covered by valid-dir scrape test that documents empty output when multiprocess env is set after process start.
- `test_multiproc_no_default_stuff` -> multiprocess registry output.
- `test_multiproc_correct_count` -> request counter under multiprocess mode.
- `test_multiproc_inprogress_metric` -> in-progress gauge during concurrent Tornado requests.
- `test_multiproc_no_duplicates` -> no duplicate metrics in multiprocess output.

### `test_instrumentator_starlette.py`

Behavior: generic framework behavior currently expressed with Starlette.

Tornado route: port semantics to Tornado; do not keep Starlette as a supported app type.

Tests:

- `test_starlette_instrumentation_basic` -> Tornado basic instrumentation.
- `test_starlette_different_paths` -> Tornado different paths.
- `test_starlette_http_methods` -> Tornado HTTP methods.
- `test_starlette_status_codes` -> Tornado status codes.
- `test_starlette_excluded_handlers` -> Tornado exclusions.
- `test_starlette_custom_endpoint` -> Tornado custom metrics endpoint.
- `test_starlette_path_parameters` -> Tornado path parameters.
- `test_starlette_gzip_support` -> Tornado gzip support.

### `test_instrumentator_included_router.py`

Behavior: FastAPI included-router path handling, validation errors, method errors, nested routers, mounted apps, and websocket routes.

Tornado route: account for each test. Port handler representation behavior where Tornado has a route equivalent; mark FastAPI-only validation/router semantics not applicable if no intentional Tornado feature maps to them.

Tests:

- `test_included_router_does_not_crash_request` -> covered by Tornado registered-handler and dynamically added-handler tests.
- `test_included_router_handler_label_includes_prefix` -> covered by Tornado route-pattern labels; Tornado host patterns do not add path prefixes.
- `test_included_router_validation_error_does_not_500` -> not applicable for this library; Tornado has no FastAPI-style request validation layer.
- `test_include_router_simple_path_is_instrumented` -> covered by Tornado `add_handlers` after `instrument(app)`.
- `test_nested_include_router_path_is_instrumented` -> not applicable as a distinct feature; Tornado does not have FastAPI nested routers, and registered route patterns are already covered.
- `test_included_router_not_found_does_not_500` -> covered by Tornado unmatched-route 404 policy.
- `test_included_router_method_not_allowed_does_not_500` -> covered by Tornado 405 test.
- `test_mount_inside_included_router_resolves_path` -> not applicable for first version; Tornado does not expose FastAPI/Starlette mounted ASGI app routing.
- `test_websocket_route_under_included_router_resolves_path` -> not applicable for first version; this package instruments HTTP `RequestHandler` routes, not websocket route resolution.

### `test_instrumentator_mounted_apps.py`

Behavior: FastAPI mounted application routing and scope isolation.

Tornado route: account for but likely defer unless the project supports nested Tornado applications.

Tests:

- `test_mounted_app_with_app` -> not applicable for first version; Tornado does not have FastAPI/Starlette mounted ASGI sub-app semantics.
- `test_mounted_app_instrumented_only` -> not applicable for first version; no nested Tornado application support is promised.

### `test_markers.py`

Behavior: pytest slow marker selection sanity.

Tornado route: keep the same marker policy and register the `slow` marker in pytest config.

Tests:

- `test_slow` -> covered by `tests/test_markers.py`.
- `test_not_slow` -> covered by `tests/test_markers.py`.
