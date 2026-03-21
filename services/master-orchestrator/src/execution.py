import requests


def execute_campaign(campaign):
    payload = {
        "campaign_id": campaign["id"],
        "video_url": campaign["video_url"],
        "caption": campaign["caption"],
        "destination_url": campaign["landing"],
    }

    response = requests.post("http://execution-engine:9600/publish", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
