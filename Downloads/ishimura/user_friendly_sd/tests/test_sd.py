import pytest

from user_friendly_sd import C, Group, Player
from user_friendly_sd.payoff_caluculator import caluculate_payoff, num_of_coopeartors


def test_set_payoffs(mock_group, mock_players):
    """ペイオフ計算のテスト"""
    mock_group.set_payoffs()

    # 協力者の数: 3 / 5
    expected_payoff = (3 * C.BC_RATIO) / 5

    for player in mock_players:
        assert player.payoff == pytest.approx(expected_payoff, 0.1)


def test_set_payoffs_all_cooperate(mock_group):
    """全員が協力 (C) を選択した場合のテスト"""
    mock_group.get_players = lambda: [Player(decision="C") for _ in range(5)]
    mock_group.set_payoffs()

    for player in mock_group.get_players():
        assert player.payoff == C.BASE_PAYOFF + C.MAX_BONUS


def test_set_payoffs_all_defect(mock_group):
    """全員が裏切り (D) を選択した場合のテスト"""
    mock_group.get_players = lambda: [Player(decision="D") for _ in range(5)]
    mock_group.set_payoffs()

    for player in mock_group.get_players():
        assert player.payoff == C.BASE_PAYOFF  # 追加ボーナスなし
