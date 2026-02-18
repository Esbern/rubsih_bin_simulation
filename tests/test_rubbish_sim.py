import random

import pytest

from simulated_city.config import SimulationConfig, SimulationLocationConfig
from simulated_city.rubbish_sim import (
    ContainerState,
    LocationState,
    boundaries_crossed,
    choose_container,
    step_location,
)


def test_boundaries_crossed_simple() -> None:
    assert boundaries_crossed(0, 1, boundary_pct=10) == []
    assert boundaries_crossed(9, 10, boundary_pct=10) == [10]
    assert boundaries_crossed(19, 31, boundary_pct=10) == [20, 30]


def test_boundaries_crossed_requires_positive_boundary() -> None:
    with pytest.raises(ValueError):
        boundaries_crossed(0, 10, boundary_pct=0)


def test_choose_container_returns_none_if_all_full() -> None:
    rng = random.Random(123)
    full = ContainerState(fill_pct=100)
    assert choose_container(rng=rng, left=full, center=full, right=full) is None


def test_choose_container_falls_back_when_preferred_is_full() -> None:
    # Use a deterministic RNG and make one container full.
    rng = random.Random(0)
    left = ContainerState(fill_pct=0)
    center = ContainerState(fill_pct=100)
    right = ContainerState(fill_pct=0)

    chosen = choose_container(rng=rng, left=left, center=center, right=right)
    assert chosen in {"left", "right"}


def test_step_location_deposits_when_arrival_prob_is_one() -> None:
    sim_cfg = SimulationConfig(
        timestep_minutes=15,
        arrival_prob=1.0,
        bag_fill_delta_pct=2,
        status_boundary_pct=10,
        seed=42,
        locations=(SimulationLocationConfig(location_id="a", lat=55.0, lon=12.0),),
    )

    rng = random.Random(1)
    loc = LocationState(
        location_id="a",
        lat=55.0,
        lon=12.0,
        left=ContainerState(fill_pct=0),
        center=ContainerState(fill_pct=0),
        right=ContainerState(fill_pct=0),
    )

    updated, result = step_location(rng=rng, sim_cfg=sim_cfg, location=loc)
    assert result.deposited is True
    assert result.container in {"left", "center", "right"}
    assert result.old_fill_pct == 0
    assert result.new_fill_pct == 2

    assert (
        updated.left.fill_pct + updated.center.fill_pct + updated.right.fill_pct
    ) == 2
