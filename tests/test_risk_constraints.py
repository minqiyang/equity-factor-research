import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from risk.constraints import apply_long_only_position_cap


def _targets() -> pd.DataFrame:
    return pd.DataFrame(
        [[0.5, 0.5, 0.0], [0.2, 0.3, 0.0], [0.0, 0.0, 0.0]],
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
        columns=["AAA", "BBB", "CCC"],
    )


def test_position_cap_clips_without_renormalizing_or_mutating() -> None:
    targets = _targets()
    original = targets.copy()

    constrained = apply_long_only_position_cap(
        targets,
        max_position_weight=0.3,
    )

    assert constrained.iloc[0].tolist() == pytest.approx([0.3, 0.3, 0.0])
    assert constrained.iloc[0].sum() == pytest.approx(0.6)
    assert constrained.iloc[1].tolist() == pytest.approx([0.2, 0.3, 0.0])
    assert constrained.iloc[2].sum() == pytest.approx(0.0)
    assert_frame_equal(targets, original)


def test_position_cap_one_is_noop() -> None:
    targets = _targets()
    assert_frame_equal(
        apply_long_only_position_cap(targets, max_position_weight=1.0),
        targets,
    )


@pytest.mark.parametrize("cap", [0.0, -0.1, 1.1, np.nan, np.inf, True, "0.5"])
def test_position_cap_rejects_invalid_cap(cap: object) -> None:
    with pytest.raises(
        ValueError,
        match="max_position_weight must be greater than 0 and no greater than 1",
    ):
        apply_long_only_position_cap(_targets(), max_position_weight=cap)


@pytest.mark.parametrize(
    ("mutator", "error_type", "message"),
    [
        (lambda frame: frame.to_numpy(), TypeError, "must be a pandas DataFrame"),
        (lambda frame: frame.iloc[0:0], ValueError, "must not be empty"),
        (
            lambda frame: frame.set_axis([frame.index[0]] * 3),
            ValueError,
            "unique assets and unique, increasing dates",
        ),
        (
            lambda frame: frame.rename(columns={"BBB": "AAA"}),
            ValueError,
            "unique assets and unique, increasing dates",
        ),
        (
            lambda frame: frame.assign(AAA=np.nan),
            ValueError,
            "finite non-negative real weights",
        ),
        (
            lambda frame: frame.assign(AAA=-0.1),
            ValueError,
            "finite non-negative real weights",
        ),
        (
            lambda frame: frame.assign(AAA=True),
            TypeError,
            "finite non-negative real weights",
        ),
        (
            lambda frame: frame.assign(AAA=0.8, BBB=0.8),
            ValueError,
            "gross exposure must not exceed 1",
        ),
    ],
)
def test_position_cap_rejects_invalid_targets(mutator, error_type, message) -> None:
    with pytest.raises(error_type, match=message):
        apply_long_only_position_cap(mutator(_targets()), max_position_weight=0.3)
