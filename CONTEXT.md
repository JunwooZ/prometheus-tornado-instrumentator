# Prometheus Tornado Instrumentator

This context describes a Tornado-focused Prometheus instrumentation library inspired by `prometheus-fastapi-instrumentator`.

## Language

**Instrumentator**:
The public object users configure to attach request instrumentation and expose Prometheus metrics for a Tornado application.
_Avoid_: exporter, plugin, middleware manager

**Instrumentation Function**:
A user-provided or built-in callable that receives request/response observation data and updates one or more Prometheus metrics.
_Avoid_: metric callback, hook, handler

**Observation Info**:
The per-request data passed into instrumentation functions, including the request, response status, handler representation, method, and duration.
_Avoid_: context, event, sample

**Metrics Endpoint**:
The HTTP endpoint that serves Prometheus scrape output, usually `/metrics`.
_Avoid_: dashboard, report endpoint

**Handler Representation**:
The normalized label value used to identify which Tornado request handler or route handled the request.
_Avoid_: route name, URL label, path label

**Lifecycle Hook**:
A Tornado request-handling point used by the instrumentator to start, finish, or expose observation work around a request.
_Avoid_: middleware hook, ASGI hook, interceptor

**Request Log Hook**:
The Tornado application callback invoked at the end of a request with the completed `RequestHandler`, useful as a low-intrusion fallback observation point.
_Avoid_: access log, middleware, after-request hook

**Instrumented Handler Wrapper**:
A generated Tornado `RequestHandler` subclass that wraps an existing handler class to observe request lifecycle events without requiring application code to inherit from a project-specific base handler.
_Avoid_: monkey patch, middleware clone, required base handler
