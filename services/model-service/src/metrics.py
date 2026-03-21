import os

_METRICS_ENABLED = os.getenv("PROMETHEUS_METRICS_ENABLED", "1") != "0"

if _METRICS_ENABLED:
    from prometheus_client import Counter, Histogram

    ASYNC_REQUESTS_TOTAL = Counter(
        "model_service_async_requests_total",
        "Async inference requests accepted",
    )
    ASYNC_RESULTS_TOTAL = Counter(
        "model_service_async_results_total",
        "Async results persisted",
        ["status"],
    )
    ASYNC_DLQ_TOTAL = Counter(
        "model_service_async_dlq_total",
        "Async inference failures routed to DLQ",
    )
    RESULT_LOOKUP_LATENCY = Histogram(
        "model_service_result_lookup_seconds",
        "Latency for async result lookups",
    )
else:
    class _NoopMetric:
        def inc(self, amount: float = 1.0) -> None:
            return None

        def observe(self, value: float) -> None:
            return None

        def labels(self, *args, **kwargs):
            return self

    ASYNC_REQUESTS_TOTAL = _NoopMetric()
    ASYNC_RESULTS_TOTAL = _NoopMetric()
    ASYNC_DLQ_TOTAL = _NoopMetric()
    RESULT_LOOKUP_LATENCY = _NoopMetric()
