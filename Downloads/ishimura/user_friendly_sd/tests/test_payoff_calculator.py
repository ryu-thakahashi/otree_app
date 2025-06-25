import pytest

from user_friendly_sd.payoff_caluculator import caluculate_payoff, num_of_coopeartors


@pytest.mark.parametrize(
    "user_decisions, expected_num_of_cooperators",
    [(["C"] * 5, 5), (["D"] * 5, 0), (["C"] * 3 + ["D"] * 1, 3)],
)
def test_num_of_coopが正しいかどうか(user_decisions, expected_num_of_cooperators):
    """num_of_coopのテスト"""
    assert num_of_coopeartors(user_decisions) == expected_num_of_cooperators


@pytest.mark.parametrize(
    "user_decisions, bc_ratio, expected_payoff",
    [
        (["C"] * 5, 2, (5 * 2) / 5),
        (["D"] * 5, 5, 0),
        (["C"] * 3 + ["D"] * 1, 10, (3 * 10) / 4),
    ],
)
def test_caluculate_payoffが正しいかどうか(user_decisions, bc_ratio, expected_payoff):
    """caluculate_payoffのテスト"""
    assert caluculate_payoff(user_decisions, bc_ratio) == expected_payoff
