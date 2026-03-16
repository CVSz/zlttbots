from prometheus_client import Counter, Histogram

request_counter = Counter('arbitrage_requests_total', 'Total arbitrage API requests')
request_latency = Histogram('arbitrage_request_latency_seconds', 'Arbitrage request latency in seconds')
