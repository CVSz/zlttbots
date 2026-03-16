import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "gpu-renderer" / "src" / "core" / "render.py"

spec = importlib.util.spec_from_file_location("gpu_render_module", MODULE_PATH)
render_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_module)


def test_build_ffmpeg_command_defaults_to_cpu_when_no_gpu():
    job = {"input": "in.mp4", "output": "out.mp4"}
    with patch.dict(os.environ, {"FFMPEG_HWACCEL": "auto"}, clear=False), patch.object(
        render_module.shutil, "which", return_value=None
    ):
        cmd = render_module.build_ffmpeg_command(job)

    assert "-hwaccel" not in cmd
    assert "libx264" in cmd
    assert cmd[-1] == "out.mp4"


def test_build_ffmpeg_command_uses_cuda_when_forced():
    job = {"input": "in.mp4", "output": "out.mp4"}
    with patch.dict(os.environ, {"FFMPEG_HWACCEL": "cuda"}, clear=False):
        cmd = render_module.build_ffmpeg_command(job)

    assert "-hwaccel" in cmd
    assert "cuda" in cmd
    assert "h264_nvenc" in cmd
