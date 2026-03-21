def latency_adjusted_bid(
    base_bid: float,
    score: float,
    latency_ms: float,
    pacing_multiplier: float = 1.0,
    ctr: float = 0.0,
    cvr: float = 0.0,
    max_bid: float = 10.0,
) -> float:
    """Apply a latency penalty while preserving EV- and pacing-based bid shaping."""
    safe_latency = max(latency_ms, 0.0)
    latency_penalty = max(0.5, 1 - (max(safe_latency - 100.0, 0.0) / 500.0))
    expected_value = ctr * cvr * score
    bid = base_bid * (1 + (expected_value * 10.0)) * pacing_multiplier * latency_penalty
    return max(0.01, min(bid, max_bid))
