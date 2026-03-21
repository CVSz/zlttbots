import requests

TIMEOUT = 10


def decide_and_scale(campaign_id: str) -> dict:
    features_response = requests.get(f"http://feature-store:8000/features/{campaign_id}", timeout=TIMEOUT)
    features_response.raise_for_status()
    features = features_response.json()

    selection_response = requests.post(
        "http://rl-engine:8000/select",
        json={"campaign_id": campaign_id, "features": features},
        timeout=TIMEOUT,
    )
    selection_response.raise_for_status()
    selection = selection_response.json()

    scale_response = requests.post(
        "http://scaling-engine:8000/scale",
        json={"campaign_id": selection["selected_campaign_id"], "score": selection["score"]},
        timeout=TIMEOUT,
    )
    scale_response.raise_for_status()

    return {"features": features, "rl": selection, "scale": scale_response.json()}
