from prometheus_client import Counter, Histogram

request_counter = Counter('viral_predictor_requests_total', 'Total predictor API requests')
request_latency = Histogram('viral_predictor_request_latency_seconds', 'Predictor request latency in seconds')
