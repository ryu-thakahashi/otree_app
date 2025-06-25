def extract_player_decisions(players):
    return [extract_p_decision(p) for p in players]


def extract_p_decision(player):
    return player.decision
