import inspect
import time
from typing import Type

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

from prometheus_tornado_instrumentator import metrics


def wrap_handler(
    instrumentator,
    handler_class: Type[RequestHandler],
    handler_pattern: str,
) -> Type[RequestHandler]:
    instrumentation_specs = getattr(
        handler_class, "_prometheus_tornado_instrumentators", None
    )
    if instrumentation_specs is not None:
        if (instrumentator, handler_pattern) in instrumentation_specs:
            return handler_class
        instrumentation_specs.append((instrumentator, handler_pattern))
        return handler_class

    class InstrumentedHandler(handler_class):
        def prepare(self):
            self._instrumentator_states = []
            for current_instrumentator, current_handler_pattern in (
                self._prometheus_tornado_instrumentators
            ):
                inprogress_metric = None
                if current_instrumentator.inprogress is not None:
                    inprogress_metric = current_instrumentator._inprogress_child(
                        current_handler_pattern,
                        self.request.method,
                    )
                    inprogress_metric.inc()
                self._instrumentator_states.append(
                    {
                        "instrumentator": current_instrumentator,
                        "handler_pattern": current_handler_pattern,
                        "started_at": time.perf_counter(),
                        "first_write_at": None,
                        "response_body": [],
                        "should_capture_body": (
                            current_instrumentator._should_capture_body(
                                current_handler_pattern
                            )
                        ),
                        "inprogress_metric": inprogress_metric,
                    }
                )
            result = super().prepare()
            return result

        def write(self, chunk):
            now = time.perf_counter()
            for state in self._instrumentator_states:
                if state["first_write_at"] is None:
                    state["first_write_at"] = now
            if not any(
                state["should_capture_body"] for state in self._instrumentator_states
            ):
                return super().write(chunk)
            write_buffer_start = len(self._write_buffer)
            result = super().write(chunk)
            written_body = self._write_buffer[write_buffer_start:]
            for state in self._instrumentator_states:
                if state["should_capture_body"]:
                    state["response_body"].extend(written_body)
            return result

        def on_finish(self):
            try:
                for state in self._instrumentator_states:
                    current_instrumentator = state["instrumentator"]
                    current_handler_pattern = state["handler_pattern"]
                    status_code = self.get_status()
                    status_label = (
                        f"{status_code // 100}xx"
                        if current_instrumentator.should_group_status_codes
                        else str(status_code)
                    )
                    if current_instrumentator._is_handler_excluded(
                        current_handler_pattern
                    ):
                        continue
                    modified_handler = current_instrumentator._modified_handler(
                        current_handler_pattern
                    )
                    if modified_handler is None:
                        continue
                    duration_without_streaming = 0.0
                    if state["first_write_at"] is not None:
                        duration_without_streaming = (
                            state["first_write_at"] - state["started_at"]
                        )
                    duration = self.request.request_time()
                    if current_instrumentator.should_round_latency_decimals:
                        duration = round(
                            duration,
                            current_instrumentator.round_latency_decimals,
                        )
                        duration_without_streaming = round(
                            duration_without_streaming,
                            current_instrumentator.round_latency_decimals,
                        )
                    response = metrics.Response(
                        headers=self._headers,
                        body=b"".join(state["response_body"]),
                    )
                    info = metrics.Info(
                        request=self.request,
                        response=response,
                        method=self.request.method,
                        modified_handler=modified_handler,
                        modified_status=status_label,
                        modified_duration=duration,
                        modified_duration_without_streaming=duration_without_streaming,
                    )
                    for instrumentation in current_instrumentator.instrumentations:
                        result = instrumentation(info)
                        if inspect.isawaitable(result):
                            IOLoop.current().spawn_callback(
                                current_instrumentator._run_async_instrumentation,
                                result,
                            )
                    for instrumentation in current_instrumentator.async_instrumentations:
                        IOLoop.current().spawn_callback(instrumentation, info)
            finally:
                for state in self._instrumentator_states:
                    if state["inprogress_metric"] is not None:
                        state["inprogress_metric"].dec()
                super().on_finish()

    InstrumentedHandler.__name__ = f"Instrumented{handler_class.__name__}"
    InstrumentedHandler._prometheus_tornado_instrumented = True
    InstrumentedHandler._prometheus_tornado_instrumentators = [
        (instrumentator, handler_pattern)
    ]
    return InstrumentedHandler
