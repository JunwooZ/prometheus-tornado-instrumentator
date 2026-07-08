# Architecture

The public API stays close to the upstream instrumentator style:

```python
Instrumentator().instrument(app).expose(app)
```

The implementation is Tornado-native. `instrument(app)` wraps registered
`tornado.web.RequestHandler` classes with generated subclasses instead of trying
to emulate ASGI middleware.

This gives the package access to Tornado lifecycle points such as `prepare()`,
`write()`, `finish()`, and `on_finish()`, which are needed for request duration,
in-progress gauges, response-size metrics, and optional response-body capture.

The request log hook was considered as a lower-intrusion integration point, but
it only observes completed requests and cannot support the full semantic parity
surface. It remains useful as background context, not as the primary integration
strategy.

Route traversal and dynamic `Application.add_handlers()` patching live in
`routing.py`. Handler wrapping and observation lifecycle behavior live in
`middleware.py`.

