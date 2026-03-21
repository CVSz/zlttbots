import os
from pathlib import Path

import numpy as np
import onnxruntime as ort

MODEL_PATH = os.getenv("MODEL_PATH", "/models/policy.onnx")
INTRA_OP_THREADS = int(os.getenv("ORT_INTRA_OP_THREADS", "1"))
INTER_OP_THREADS = int(os.getenv("ORT_INTER_OP_THREADS", "1"))
CPU_MEM_ARENA = os.getenv("ORT_ENABLE_CPU_MEM_ARENA", "1") == "1"


class ONNXModel:
    def __init__(self, model_path: str | Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.session: ort.InferenceSession | None = None
        self.input_name: str | None = None
        self.output_name: str | None = None
        self.ready = False
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            return

        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.intra_op_num_threads = INTRA_OP_THREADS
        session_options.inter_op_num_threads = INTER_OP_THREADS
        session_options.enable_cpu_mem_arena = CPU_MEM_ARENA

        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.ready = True

    def warm_up(self) -> None:
        if not self.ready:
            return
        sample = np.zeros((1, self.input_width), dtype=np.float32)
        self.predict(sample)

    @property
    def input_width(self) -> int:
        if not self.ready or self.session is None:
            return 0
        shape = self.session.get_inputs()[0].shape
        width = shape[-1]
        if isinstance(width, int):
            return width
        return 2

    def predict(self, x: np.ndarray | list[float] | list[list[float]]) -> np.ndarray:
        if not self.ready or self.session is None or self.input_name is None or self.output_name is None:
            raise RuntimeError(f"ONNX model is unavailable at {self.model_path}")

        array = np.asarray(x, dtype=np.float32)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        if array.ndim != 2:
            raise ValueError("Input must be a 1D or 2D numeric array")
        if self.input_width and array.shape[1] != self.input_width:
            raise ValueError(f"Expected feature width {self.input_width}, got {array.shape[1]}")

        outputs = self.session.run([self.output_name], {self.input_name: array})
        return np.asarray(outputs[0], dtype=np.float32)
