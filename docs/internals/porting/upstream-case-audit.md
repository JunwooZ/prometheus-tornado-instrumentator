# Upstream Case Audit

Source audited from `trallnag/prometheus-fastapi-instrumentator` `master` on 2026-07-08.

Status meanings:

- `ported`: Tornado equivalent is implemented and covered by a local test.
- `not-applicable`: Framework-specific behavior does not exist in Tornado HTTP instrumentation.

## Summary

| Upstream file | Upstream cases | Status |
| --- | ---: | --- |
| `test_expose.py` | 3 | 2 ported, 1 not-applicable |
| `test_instrumentation.py` | 24 | 21 ported, 3 not-applicable |
| `test_instrumentator_expose.py` | 2 | 2 ported |
| `test_instrumentator_included_router.py` | 9 | 4 ported, 5 not-applicable |
| `test_instrumentator_mounted_apps.py` | 2 | 2 not-applicable |
| `test_instrumentator_multiple_apps.py` | 3 | 3 ported |
| `test_instrumentator_multiproc.py` | 7 | 7 ported |
| `test_instrumentator_starlette.py` | 8 | 8 ported |
| `test_markers.py` | 2 | 2 ported |
| `test_metrics.py` | 31 | 30 ported, 1 not-applicable |
| `test_middleware.py` | 7 | 7 ported |

Total upstream cases: 98.

## `test_expose.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_expose_default_content_type` | ported | `tests/test_expose.py::MetricsExposeTest::test_expose_default_metrics_endpoint` |
| `test_fastapi_app_expose` | ported | `tests/test_expose.py::MetricsExposeTest::test_expose_default_metrics_endpoint` |
| `test_starlette_app_expose` | not-applicable | Starlette app type is not supported; Tornado app expose is covered. |

## `test_instrumentation.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_app` | ported | `tests/test_package_smoke.py::test_public_imports_are_available` and Tornado app fixture tests |
| `test_metrics_endpoint_availability` | ported | `tests/test_expose.py::MetricsExposeTest::test_expose_default_metrics_endpoint` |
| `test_gzip_accepted` | ported | `tests/test_expose.py::MetricsGzipTest::test_expose_gzips_when_enabled_and_accepted` |
| `test_gzip_not_accepted` | ported | `tests/test_expose.py::MetricsNoGzipTest::test_expose_does_not_gzip_when_disabled` |
| `test_default_metric_name` | ported | `tests/test_instrumentation.py::CustomMetricNameTest::test_custom_metric_name_is_used` |
| `test_default_without_add` | ported | `tests/test_instrumentation.py::DefaultInstrumentationTest::test_instrument_adds_default_metrics_when_none_are_added` |
| `test_custom_metric_name` | ported | `tests/test_instrumentation.py::CustomMetricNameTest::test_custom_metric_name_is_used` |
| `test_grouped_status_codes` | ported | `tests/test_instrumentation.py::ExplicitInstrumentationTest::test_request_counter_observes_real_tornado_requests` |
| `test_grouped_status_codes_with_enumeration` | ported | `tests/test_instrumentation.py::GroupedStatusCodeWithEnumerationTest::test_grouped_status_codes_with_enumeration` |
| `test_ungrouped_status_codes` | ported | `tests/test_instrumentation.py::UngroupedStatusCodeTest::test_status_code_can_be_observed_without_grouping` |
| `test_ignore_untemplated` | ported | `tests/test_instrumentation.py::NotFoundRouteTest::test_unmatched_route_returns_404_without_recording_raw_path` |
| `test_dont_ignore_untemplated_ungrouped` | not-applicable | Tornado unmatched requests do not enter a wrapped registered `RequestHandler`. |
| `test_grouping_untemplated` | not-applicable | Tornado unmatched requests are ignored rather than grouped through a routed handler. |
| `test_excluding_handlers` | ported | `tests/test_instrumentation.py::ExcludedHandlersTest::test_excluded_handler_is_not_instrumented` |
| `test_excluding_handlers_regex` | ported | `tests/test_instrumentation.py::RegexExcludedHandlersTest::test_regex_excluded_handler_is_not_instrumented` |
| `test_excluded_handlers_none` | ported | `tests/test_instrumentation.py::test_excluded_handlers_empty_list_is_preserved` |
| `test_bucket_without_inf` | ported | `tests/test_instrumentation.py::CustomLatencyBucketTest::test_latency_buckets_can_omit_explicit_infinity` |
| `test_should_respect_env_var_existence_exists` | ported | `tests/test_instrumentation.py::EnvVarEnabledInstrumentationTest::test_instrument_and_expose_are_enabled_when_env_var_exists` |
| `test_should_respect_env_var_existence_not_exists` | ported | `tests/test_instrumentation.py::EnvVarDisabledInstrumentationTest::test_instrument_and_expose_are_disabled_when_env_var_is_absent` and `EnvVarFalseInstrumentationTest` |
| `test_entropy` | not-applicable | Upstream helper sanity check for rounding entropy; Tornado port directly asserts rounded `Info` durations. |
| `test_default_no_rounding` | ported | `tests/test_instrumentation.py::RoundedLatencyTest::test_observation_info_durations_are_rounded` covers the rounding path; default non-rounding is covered by default duration tests. |
| `test_rounding` | ported | `tests/test_instrumentation.py::RoundedLatencyTest::test_observation_info_durations_are_rounded` |
| `test_custom_async_instrumentation` | ported | `tests/test_instrumentation.py::AsyncCustomInstrumentationTest::test_async_instrumentation_receives_observation_info` |
| `test_add_sync_instrumentation_does_not_warn_deprecated_coroutine_check` | ported | `tests/test_instrumentation.py::CustomInstrumentationTest::test_sync_instrumentation_receives_observation_info` |

## `test_instrumentator_expose.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_expose_defaults` | ported | `tests/test_instrumentator_expose.py::test_instrumentator_expose_defaults_and_custom_path_are_ported` |
| `test_expose_custom_path` | ported | `tests/test_instrumentator_expose.py::test_instrumentator_expose_defaults_and_custom_path_are_ported` |

## `test_instrumentator_included_router.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_included_router_does_not_crash_request` | ported | `tests/test_router_accounting.py::DynamicAddHandlersTest::test_handlers_added_after_instrument_are_instrumented` |
| `test_included_router_handler_label_includes_prefix` | ported | `tests/test_instrumentation.py::ParameterizedRouteLabelTest::test_parameterized_route_uses_pattern_not_raw_path` |
| `test_included_router_validation_error_does_not_500` | not-applicable | Tornado has no FastAPI request validation layer. |
| `test_include_router_simple_path_is_instrumented` | ported | `tests/test_router_accounting.py::DynamicAddHandlersTest::test_handlers_added_after_instrument_are_instrumented` |
| `test_nested_include_router_path_is_instrumented` | not-applicable | Tornado does not have FastAPI nested router include semantics. |
| `test_included_router_not_found_does_not_500` | ported | `tests/test_instrumentation.py::NotFoundRouteTest::test_unmatched_route_returns_404_without_recording_raw_path` |
| `test_included_router_method_not_allowed_does_not_500` | ported | `tests/test_router_accounting.py::MethodNotAllowedTest::test_method_not_allowed_does_not_become_500` |
| `test_mount_inside_included_router_resolves_path` | not-applicable | Starlette mounted ASGI app routing is not a Tornado HTTP handler feature. |
| `test_websocket_route_under_included_router_resolves_path` | not-applicable | This package instruments Tornado HTTP `RequestHandler` routes, not websocket route resolution. |

## `test_instrumentator_mounted_apps.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_mounted_app_with_app` | not-applicable | FastAPI/Starlette mounted ASGI sub-application semantics are not supported in the first Tornado port. |
| `test_mounted_app_instrumented_only` | not-applicable | No nested ASGI mounted app scope isolation exists in Tornado HTTP instrumentation. |

## `test_instrumentator_multiple_apps.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_multiple_apps_custom_registry` | ported | `tests/test_multiple_apps.py::MultipleAppsCustomRegistryTest::test_custom_registries_do_not_share_metrics` |
| `test_multiple_apps_expose_defaults` | ported | `tests/test_multiple_apps.py::test_multiple_apps_can_use_default_registry_without_duplicate_errors` |
| `test_multiple_apps_expose_full` | ported | `tests/test_multiple_apps.py::test_multiple_apps_can_add_full_metric_set_without_duplicate_errors` |

## `test_instrumentator_multiproc.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_multiproc_dir_not_found` | ported | `tests/test_multiprocess.py::test_multiproc_dir_not_found` |
| `test_multiproc_expose_no_dir` | ported | `tests/test_multiprocess.py::MultiprocExposeInvalidDirTest::test_metrics_endpoint_reports_invalid_multiproc_dir` |
| `test_multiproc_anti_test` | ported | `tests/test_multiprocess.py::MultiprocExposeValidDirTest::test_metrics_endpoint_accepts_valid_multiproc_dir` |
| `test_multiproc_no_default_stuff` | ported | `tests/test_multiprocess.py::test_multiproc_child_process_counts_requests_and_avoids_duplicates` |
| `test_multiproc_correct_count` | ported | `tests/test_multiprocess.py::test_multiproc_child_process_counts_requests_and_avoids_duplicates` |
| `test_multiproc_inprogress_metric` | ported | `tests/test_multiprocess.py::InProgressGaugeTest::test_inprogress_metric_counts_concurrent_requests` |
| `test_multiproc_no_duplicates` | ported | `tests/test_multiprocess.py::test_multiproc_child_process_counts_requests_and_avoids_duplicates` |

## `test_instrumentator_starlette.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_starlette_instrumentation_basic` | ported | `tests/test_instrumentator_starlette.py::test_starlette_basic_path_method_status_equivalents_are_ported` |
| `test_starlette_different_paths` | ported | `tests/test_instrumentator_starlette.py::test_starlette_basic_path_method_status_equivalents_are_ported` |
| `test_starlette_http_methods` | ported | `tests/test_instrumentator_starlette.py::test_starlette_basic_path_method_status_equivalents_are_ported` |
| `test_starlette_status_codes` | ported | `tests/test_instrumentator_starlette.py::test_starlette_basic_path_method_status_equivalents_are_ported` |
| `test_starlette_excluded_handlers` | ported | `tests/test_instrumentator_starlette.py::test_starlette_exclusion_endpoint_path_parameter_and_gzip_equivalents_are_ported` |
| `test_starlette_custom_endpoint` | ported | `tests/test_instrumentator_starlette.py::test_starlette_exclusion_endpoint_path_parameter_and_gzip_equivalents_are_ported` |
| `test_starlette_path_parameters` | ported | `tests/test_instrumentator_starlette.py::test_starlette_exclusion_endpoint_path_parameter_and_gzip_equivalents_are_ported` |
| `test_starlette_gzip_support` | ported | `tests/test_instrumentator_starlette.py::test_starlette_exclusion_endpoint_path_parameter_and_gzip_equivalents_are_ported` |

## `test_markers.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_slow` | ported | `tests/test_markers.py::test_slow` |
| `test_not_slow` | ported | `tests/test_markers.py::test_not_slow` |

## `test_metrics.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_is_duplicated_time_series` | ported | `tests/test_metrics.py::test_is_duplicated_time_series` |
| `test_existence_of_attributes` | ported | `tests/test_metrics.py::test_observation_info_attributes_exist` |
| `test_build_label_attribute_names_all_false` | ported | `tests/test_metrics.py::test_build_label_attribute_names_all_false` |
| `test_build_label_attribute_names_all_true` | ported | `tests/test_metrics.py::test_build_label_attribute_names_all_true` |
| `test_build_label_attribute_names_mixed` | ported | `tests/test_metrics.py::test_build_label_attribute_names_mixed` |
| `test_api_throwing_error` | ported | `tests/test_metrics.py::test_api_throwing_error` |
| `test_request_size_all_labels` | ported | `tests/test_metrics.py::test_request_size_observes_content_length` |
| `test_request_size_no_labels` | ported | `tests/test_metrics.py::test_request_size_observes_zero_without_content_length` |
| `test_namespace_subsystem` | ported | `tests/test_metrics.py::test_metric_namespace_and_subsystem_prefix_metric_name` |
| `test_request_size_no_cl` | ported | `tests/test_metrics.py::test_request_size_observes_zero_without_content_length` |
| `test_response_size_all_labels` | ported | `tests/test_metrics.py::test_response_size_observes_content_length` |
| `test_response_size_no_labels` | ported | `tests/test_metrics.py::test_response_size_can_disable_all_labels` |
| `test_response_size_with_runtime_error` | ported | `tests/test_instrumentation.py::RuntimeErrorResponseSizeTest::test_response_size_records_5xx_for_runtime_error` |
| `test_combined_size_all_labels` | ported | `tests/test_metrics.py::test_combined_size_observes_request_and_response_content_lengths` |
| `test_combined_size_all_labels_with_data` | ported | `tests/test_metrics.py::test_combined_size_observes_request_and_response_content_lengths` |
| `test_combined_size_no_labels` | ported | `tests/test_metrics.py::test_combined_size_can_disable_all_labels` |
| `test_combined_size_with_runtime_error` | ported | `tests/test_instrumentation.py::RuntimeErrorCombinedSizeTest::test_combined_size_records_5xx_for_runtime_error` |
| `test_latency_all_labels` | ported | `tests/test_metrics.py::test_latency_observes_duration_with_all_labels` |
| `test_latency_no_labels` | ported | `tests/test_metrics.py::test_latency_can_disable_all_labels` |
| `test_latency_with_bucket_no_inf` | ported | `tests/test_metrics.py::test_latency_accepts_buckets_without_explicit_infinity` |
| `test_latency_duration_without_streaming` | ported | `tests/test_metrics.py::test_latency_can_observe_duration_without_streaming` |
| `test_default` | ported | `tests/test_metrics.py::test_default_records_core_metric_samples` |
| `test_default_should_only_respect_2xx_for_highr` | ported | `tests/test_metrics.py::test_default_high_resolution_latency_can_only_respect_2xx` |
| `test_default_should_not_only_respect_2xx_for_highr` | ported | `tests/test_metrics.py::test_default_high_resolution_latency_can_include_non_2xx` |
| `test_default_with_runtime_error` | ported | `tests/test_instrumentation.py::RuntimeErrorDefaultMetricsTest::test_default_metrics_record_5xx_for_runtime_error` |
| `test_default_duration_without_streaming` | ported | `tests/test_metrics.py::test_default_can_observe_duration_without_streaming` |
| `test_custom_labels` | ported | `tests/test_metrics.py::test_default_can_include_custom_labels` |
| `test_request_all_labels` | ported | `tests/test_metrics.py::test_requests_increments_counter_with_all_labels` |
| `test_request_no_labels` | ported | `tests/test_metrics.py::test_requests_can_disable_all_labels` |
| `test_request_custom_namespace` | ported | `tests/test_metrics.py::test_metric_namespace_and_subsystem_prefix_metric_name` |
| `test_request_mount_redirection_bug` | not-applicable | FastAPI/Starlette mount trailing-slash redirect bug has no Tornado equivalent in this port. |

## `test_middleware.py`

| Upstream case | Status | Local coverage |
| --- | --- | --- |
| `test_info_body_default` | ported | `tests/test_instrumentation.py::ResponseBodyDefaultTest::test_response_body_is_empty_by_default` |
| `test_info_body_empty` | ported | `tests/test_instrumentation.py::ResponseBodyCaptureTest::test_empty_response_body_is_captured_as_empty` |
| `test_info_body_stream_small` | ported | `tests/test_instrumentation.py::StreamingBodyCaptureTest::test_streamed_response_body_is_captured` |
| `test_info_body_stream_large` | ported | `tests/test_instrumentation.py::StreamingBodyCaptureTest::test_large_streamed_response_body_is_captured` |
| `test_info_body_bulk_small` | ported | `tests/test_instrumentation.py::ResponseBodyCaptureTest::test_body_handlers_enable_response_body_capture` |
| `test_info_body_bulk_large` | ported | `tests/test_instrumentation.py::ResponseBodyCaptureTest::test_large_response_body_is_captured` |
| `test_info_body_duration_without_streaming` | ported | `tests/test_instrumentation.py::StreamingBodyCaptureTest::test_duration_without_streaming_is_less_than_full_duration` |

## Source Layout Notes

- `src/prometheus_tornado_instrumentator/middleware.py` contains the Tornado handler-wrapper analogue to upstream ASGI middleware behavior.
- `src/prometheus_tornado_instrumentator/routing.py` contains Tornado route traversal and dynamic `add_handlers` patching, as the Tornado analogue to upstream route handling.
