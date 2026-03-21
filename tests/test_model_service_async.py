import importlib.util
import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient


class FakeTensor:
    def __init__(self, values):
        self.values = [float(v) for v in values]

    def __getitem__(self, index):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def item(self):
        if len(self.values) != 1:
            raise ValueError("item() expects a single value")
        return self.values[0]


class FakeTorch(types.SimpleNamespace):
    float32 = "float32"

    @staticmethod
    def tensor(values, dtype=None):
        return FakeTensor(values)

    @staticmethod
    def dot(left, right):
        return FakeTensor([sum(a * b for a, b in zip(left.values, right.values))])


class FakeProducer:
    def __init__(self, *args, **kwargs):
        self.messages = []

    def produce(self, topic, value):
        self.messages.append((topic, value))

    def flush(self):
        return None


class FakeConsumer:
    def __init__(self, *args, **kwargs):
        self.subscriptions = []

    def subscribe(self, topics):
        self.subscriptions.append(tuple(topics))

    def poll(self, timeout):
        return None


class FakeResultStore:
    def __init__(self):
        self.data = {}

    def set_result(self, job_id, payload):
        record = {"job_id": job_id, **payload}
        self.data[job_id] = record
        return record

    def get_result(self, job_id):
        return self.data.get(job_id)


class NoopMetric:
    def inc(self, amount=1):
        return None

    def observe(self, value):
        return None

    def labels(self, *args, **kwargs):
        return self


def load_main_module():
    base = Path("/workspace/zttato-platform/services/model-service/src")
    sys.path.insert(0, str(base))
    sys.modules["torch"] = FakeTorch()
    sys.modules["confluent_kafka"] = types.SimpleNamespace(Producer=FakeProducer, Consumer=FakeConsumer)
    sys.modules["prometheus_client"] = types.SimpleNamespace(
        CONTENT_TYPE_LATEST="text/plain",
        generate_latest=lambda: b"metrics 1\n",
        Counter=lambda *args, **kwargs: NoopMetric(),
        Histogram=lambda *args, **kwargs: NoopMetric(),
    )
    sys.modules["result_store"] = types.SimpleNamespace(result_store=FakeResultStore())

    spec = importlib.util.spec_from_file_location("model_service_main", base / "main.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_predict_async_accepts_idempotency_key():
    module = load_main_module()
    client = TestClient(module.app)

    response = client.post(
        "/predict_async",
        headers={"Idempotency-Key": "job-123"},
        json={"views": 10, "clicks": 4, "conversions": 2},
    )

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-123", "status": "queued"}
    assert module.result_store.get_result("job-123")["status"] == "queued"
    assert module.producer.messages[0][0] == module.REQUEST_TOPIC


def test_fetch_result_returns_pending_when_missing():
    module = load_main_module()
    client = TestClient(module.app)

    response = client.get("/result/unknown-job")

    assert response.status_code == 200
    assert response.json() == {"job_id": "unknown-job", "status": "pending"}
