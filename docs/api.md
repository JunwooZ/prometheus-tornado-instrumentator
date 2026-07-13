# API Reference

## Public Imports

```python
from prometheus_tornado_instrumentator import Instrumentator, metrics
from prometheus_tornado_instrumentator.metrics import Info
```

## `Instrumentator`

`Instrumentator` is the public entry point for configuring request
instrumentation and exposing Prometheus metrics.

Important constructor options:

- `should_group_status_codes`: group status labels such as `200` into `2xx`.
- `should_ignore_untemplated`: ignore untemplated requests.
- `should_round_latency_decimals`: round observed request durations.
- `should_respect_env_var`: enable instrumentation only when `env_var_name` is true.
- `should_instrument_requests_inprogress`: expose an in-progress gauge.
- `should_exclude_streaming_duration`: use first-write duration for latency metrics.
- `excluded_handlers`: regex patterns for handlers that should not be observed.
- `body_handlers`: regex patterns whose response bodies should be captured.
- `registry`: custom Prometheus `CollectorRegistry`.

Tornado's ordinary unmatched 404s do not enter a registered wrapped handler.
They are therefore never observed, regardless of the untemplated options.

## `instrument(app)`

```python
Instrumentator().instrument(app)
```

Wraps registered Tornado handlers and patches later `add_handlers()` calls so
new routes are instrumented too.

Optional metric naming arguments:

- `metric_namespace`
- `metric_subsystem`
- `latency_highr_buckets`
- `latency_lowr_buckets`
- `should_only_respect_2xx_for_highr`

If no custom instrumentation has been added, default metrics are registered.

## `expose(app)`

```python
Instrumentator().instrument(app).expose(app)
```

Adds a metrics endpoint to the Tornado app.

Options:

- `endpoint`: defaults to `/metrics`.
- `should_gzip`: compress output when the client accepts gzip.

FastAPI-compatible arguments such as `include_in_schema` and `tags` are accepted
for API familiarity but have no Tornado effect.

## `add(*instrumentations)`

```python
instrumentator = Instrumentator()
instrumentator.add(custom_metric).instrument(app).expose(app)
```

Adds one or more sync or async instrumentation functions. Each function receives
one `Info` object. Sync functions run during request completion; async functions
are scheduled after completion and must not be used when a scrape must include
their result immediately.

## `Info`

`Info` is passed to instrumentation functions after a request finishes.

Fields:

- `request`: Tornado request object.
- `response`: response data with `headers`, optional captured `body`, and the
  actual written `body_size` when no `Content-Length` header is available.
- `method`: HTTP method.
- `modified_handler`: normalized low-cardinality handler label.
- `modified_status`: status label, optionally grouped.
- `modified_duration`: full request duration.
- `modified_duration_without_streaming`: duration until first response write.

## Built-In Metrics

The `metrics` module provides ready-to-use instrumentation closures:

- `metrics.default()`
- `metrics.requests()`
- `metrics.latency()`
- `metrics.request_size()`
- `metrics.response_size()`
- `metrics.combined_size()`

Common options include:

- `metric_name`
- `metric_doc`
- `metric_namespace`
- `metric_subsystem`
- `should_include_handler`
- `should_include_method`
- `should_include_status`
- `registry`
- `custom_labels`
