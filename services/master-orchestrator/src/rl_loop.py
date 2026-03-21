from distributed_loop import run_cycle


def decide_and_scale(campaign_id: str) -> dict:
    cycle = run_cycle(campaign_id)
    return {"features": cycle["features"], "rl": cycle["rl"], "scale": cycle["scale"], "budget": cycle["budget"], "bid": cycle["bid"]}
