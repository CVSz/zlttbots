from datetime import date

from enterprise_maturity.go_to_market import (
    ContentInput,
    DeckMetrics,
    generate_daily_plan,
    generate_date_stamped_status,
    generate_pitch_deck_outline,
    generate_post,
)


def test_generate_daily_plan_phases_and_validation():
    launch = generate_daily_plan(1)
    traction = generate_daily_plan(5)
    scale = generate_daily_plan(10)

    assert "Launch burst" in launch.objective
    assert "Traction loop" in traction.objective
    assert "Scale phase" in scale.objective
    assert launch.kpi.users_target_min == 50
    assert launch.kpi.deploys_target_min == 100


def test_generate_post_is_deterministic_by_slot():
    content = ContentInput(product_link="https://zttato.dev", social_proof_count=125)

    first = generate_post(content, slot=0)
    second = generate_post(content, slot=1)
    repeat = generate_post(content, slot=0)

    assert first != second
    assert first == repeat
    assert "125+ developers" in first


def test_pitch_deck_and_status_contains_metrics():
    metrics = DeckMetrics(users=310, deploys=1200, daily_growth_percent=14.5)

    outline = generate_pitch_deck_outline(metrics)
    status = generate_date_stamped_status(date(2026, 3, 23), metrics)

    assert len(outline) == 10
    assert "Users=310" in outline[5]
    assert "2026-03-23" in status
    assert "daily_growth=14.5%" in status
