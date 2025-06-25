from otree.api import *

from user_friendly_sd.convert_py_obj import *
from user_friendly_sd.payoff_caluculator import *

doc = """
Simple Social Dilemma Game
"""


class C(BaseConstants):
    NAME_IN_URL = "user_friendly_sd"
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 1
    BC_RATIO = 3
    DECISION_DICT = {
        "C": {"bs5": "success", "btn_label": "A"},
        "D": {"bs5": "warning text-dark", "btn_label": "B"},
    }


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.session.config.get("players_per_group"):
            self.session.config["players_per_group"] = C.PLAYERS_PER_GROUP


class Group(BaseGroup):
    def set_payoffs(group: BaseGroup):
        players = group.get_players()
        for p in players:
            p_decision_list = extract_player_decisions(players)
            p.num_of_coopeartors = num_of_coopeartors(p_decision_list)
            p.payoff = caluculate_payoff(p_decision_list, C.BC_RATIO)

            # bs5 で使うためのフィールド
            p.decision_color = C.DECISION_DICT[p.decision]["bs5"]
            p.decision_str = C.DECISION_DICT[p.decision]["btn_label"]


class Player(BasePlayer):
    decision = models.StringField(
        choices=["C", "D"],
        widget=widgets.RadioSelectHorizontal,
    )
    num_of_coopeartors = models.IntegerField()

    # user 視点でのフィールド
    decision_color = models.StringField(
        doc="bs5 で使うためのフィールド (C: success, D: warning)",
    )
    decision_str = models.StringField(
        doc="user 視点でのフィールド (C: A, D: B)",
    )


# PAGES
class MyPage(Page):
    extra_js = ["user_friendly_sd/MyPage/btn_flow.js"]
    form_model = "player"
    form_fields = ["decision"]


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = Group.set_payoffs


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group_players = player.get_others_in_group()
        return {
            "player": player,
            "group_players": group_players,
            "num_cooperators": player.num_of_coopeartors,
            "num_defectors": C.PLAYERS_PER_GROUP - player.num_of_coopeartors,
            "total_players": len(group_players),
            "payoff": player.payoff,
        }


page_sequence = [MyPage, ResultsWaitPage, Results]
