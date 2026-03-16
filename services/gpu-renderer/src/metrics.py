from prometheus_client import Counter, Histogram

request_counter = Counter('gpu_renderer_requests_total', 'Total renderer API requests')
request_latency = Histogram('gpu_renderer_request_latency_seconds', 'Renderer request latency in seconds')
