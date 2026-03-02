from __future__ import annotations

from ai_config.orchestrator.router import (
    SPECIALIST_DATA_ANALYTICS,
    SPECIALIST_KNOWLEDGE_WORK,
    SPECIALIST_SOFTWARE_ENGINEERING,
    route_specialist,
)


def test_route_specialist_knowledge_work() -> None:
    specialist, score = route_specialist("sales call prep for enterprise account")
    assert specialist == SPECIALIST_KNOWLEDGE_WORK
    assert score > 0


def test_route_specialist_software_engineering() -> None:
    specialist, score = route_specialist("fix react hook bug in build pipeline")
    assert specialist == SPECIALIST_SOFTWARE_ENGINEERING
    assert score > 0


def test_route_specialist_data_analytics() -> None:
    specialist, score = route_specialist("analyze SQL dashboard metrics and data quality")
    assert specialist == SPECIALIST_DATA_ANALYTICS
    assert score > 0
