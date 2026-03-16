import os
import shutil
import subprocess


def _should_use_cuda() -> bool:
    """Enable CUDA only when explicitly requested or when nvidia-smi exists."""
    hwaccel_mode = os.environ.get("FFMPEG_HWACCEL", "auto").strip().lower()

    if hwaccel_mode in {"none", "cpu", "off", "false", "0"}:
        return False

    if hwaccel_mode in {"cuda", "nvidia", "gpu", "on", "true", "1"}:
        return True

    # auto mode
    return shutil.which("nvidia-smi") is not None


def build_ffmpeg_command(job):
    input_file = job["input"]
    output_file = job["output"]

    base_cmd = ["ffmpeg", "-y", "-i", input_file]

    if _should_use_cuda():
        return [
            "ffmpeg",
            "-y",
            "-hwaccel",
            "cuda",
            "-i",
            input_file,
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p4",
            "-b:v",
            "5M",
            output_file,
        ]

    return [
        *base_cmd,
        "-c:v",
        "libx264",
        "-preset",
        os.environ.get("FFMPEG_CPU_PRESET", "veryfast"),
        "-crf",
        os.environ.get("FFMPEG_CPU_CRF", "23"),
        output_file,
    ]


def render(job):
    cmd = build_ffmpeg_command(job)
    subprocess.run(cmd, check=True)
