from prometheus_client import Counter, Histogram

request_counter = Counter('crawler_requests_total', 'Total crawler API requests')
request_latency = Histogram('crawler_request_latency_seconds', 'Crawler request latency in seconds')
