from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from model import Policy

MODEL_PATH = Path("/shared-models/policy.pt")
OUTPUT_PATH = Path("/shared-models/policy.onnx")


def export_policy_to_onnx(model_path: Path = MODEL_PATH, output_path: Path = OUTPUT_PATH) -> Path:
    policy = Policy.load(model_path)

    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, ["batch", 2])
    output_tensor = helper.make_tensor_value_info("output", TensorProto.FLOAT, ["batch", 2])

    initializers = [
        numpy_helper.from_array(policy.w1.astype(np.float32), name="w1"),
        numpy_helper.from_array(policy.b1.astype(np.float32), name="b1"),
        numpy_helper.from_array(policy.w2.astype(np.float32), name="w2"),
        numpy_helper.from_array(policy.b2.astype(np.float32), name="b2"),
    ]

    nodes = [
        helper.make_node("MatMul", ["input", "w1"], ["hidden_mm"]),
        helper.make_node("Add", ["hidden_mm", "b1"], ["hidden_bias"]),
        helper.make_node("Relu", ["hidden_bias"], ["hidden"]),
        helper.make_node("MatMul", ["hidden", "w2"], ["logits_mm"]),
        helper.make_node("Add", ["logits_mm", "b2"], ["logits"]),
        helper.make_node("Softmax", ["logits"], ["output"], axis=1),
    ]

    graph = helper.make_graph(nodes, "policy", [input_tensor], [output_tensor], initializer=initializers)
    model = helper.make_model(graph, producer_name="zlttbots-rl-policy")
    model.ir_version = 10
    model.opset_import[0].version = 17

    output_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, output_path)
    return output_path


if __name__ == "__main__":
    path = export_policy_to_onnx()
    print(json.dumps({"exported": str(path)}))
