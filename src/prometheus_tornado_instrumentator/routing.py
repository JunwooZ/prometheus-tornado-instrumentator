from functools import wraps

from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator.middleware import wrap_handler


def wrap_application_rules(instrumentator, app: Application) -> None:
    wrap_router_rules(instrumentator, app.default_router)
    wrap_router_rules(instrumentator, app.wildcard_router)


def wrap_router_rules(instrumentator, router) -> None:
    for rule in getattr(router, "rules", []):
        if (
            isinstance(rule.target, type)
            and issubclass(rule.target, RequestHandler)
        ):
            rule.target = wrap_handler(
                instrumentator, rule.target, handler_pattern(rule)
            )
        elif hasattr(rule.target, "rules"):
            wrap_router_rules(instrumentator, rule.target)


def patch_add_handlers(instrumentator, app: Application) -> None:
    app_instrumentators = getattr(app, "_prometheus_tornado_instrumentators", None)
    if app_instrumentators is None:
        app_instrumentators = []
        app._prometheus_tornado_instrumentators = app_instrumentators
    if instrumentator not in app_instrumentators:
        app_instrumentators.append(instrumentator)

    if getattr(app, "_prometheus_tornado_add_handlers_patched", False):
        return

    original_add_handlers = app.add_handlers

    @wraps(original_add_handlers)
    def add_handlers_and_instrument(*args, **kwargs):
        result = original_add_handlers(*args, **kwargs)
        for current_instrumentator in app._prometheus_tornado_instrumentators:
            wrap_application_rules(current_instrumentator, app)
        return result

    app.add_handlers = add_handlers_and_instrument
    app._prometheus_tornado_add_handlers_patched = True


def handler_pattern(rule) -> str:
    matcher = getattr(rule, "matcher", None)
    return getattr(matcher, "_path", None) or getattr(
        getattr(matcher, "regex", None), "pattern", "none"
    )
