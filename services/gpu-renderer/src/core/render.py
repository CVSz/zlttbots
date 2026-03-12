import subprocess

def render(job):

    input_file = job["input"]
    output_file = job["output"]

    cmd = [
        "ffmpeg",
        "-y",
        "-hwaccel","cuda",
        "-i",input_file,
        "-c:v","h264_nvenc",
        "-preset","p4",
        "-b:v","5M",
        output_file
    ]

    subprocess.run(cmd, check=True)
