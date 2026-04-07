from __future__ import annotations

import os
import time

import boto3

S3_BUCKET = os.getenv("MODEL_BUCKET", "zlttbots-models")
LOCAL_PATH = os.getenv("MODEL_SYNC_FILE", "/models/policy.onnx")
ENDPOINT = os.getenv("S3_ENDPOINT")
KEY = os.getenv("MODEL_SYNC_OBJECT_KEY", "policy.onnx")
s3 = boto3.client("s3", endpoint_url=ENDPOINT)


def upload() -> None:
    s3.upload_file(LOCAL_PATH, S3_BUCKET, KEY)


def download() -> None:
    s3.download_file(S3_BUCKET, KEY, LOCAL_PATH)


def loop() -> None:
    while True:
        upload()
        download()
        time.sleep(30)


if __name__ == "__main__":
    loop()
