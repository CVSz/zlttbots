from __future__ import annotations

import os

import requests

API = "https://api.runpod.io/graphql"
KEY = os.getenv("RUNPOD_KEY")



def create_pod() -> dict:
    query = {"query": "mutation { podFindAndDeployOnDemand(input:{gpuCount:1}){id}}"}
    return requests.post(API, json=query, headers={"Authorization": KEY}, timeout=10).json()
