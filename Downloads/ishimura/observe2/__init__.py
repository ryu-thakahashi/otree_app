from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = "observe2"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 8
    task_texts = [
        "Statistics are like a drunk with a lamppost: used more for support than illumination.",
        "Don't cross your bridges before you get to them.",
        "He that is always shooting must sometimes hit.",
        "An army of sheep led by a lion would defeat an army of lions led by a sheep.",
        "Full is care, care was to be come miss note.",
        "Don't count your chickens before they hatch.",
        "You can’t make an omelette without breaking eggs.",
        "Even a stopped clock is right twice a day.",
    ]


import random


class Subsession(BaseSubsession):
    def creating_session(self):
        if "shuffled_texts" not in self.session.vars:
            self.session.vars["shuffled_texts"] = random.sample(
                C.task_texts, len(C.task_texts)
            )
        if "condition_list" not in self.session.vars:
            condition_list = [True] * 4 + [False] * 4
            random.shuffle(condition_list)
            self.session.vars["condition_list"] = condition_list

            print(f"[DEBUG] Condition list: {condition_list}")

        round_index = self.round_number - 1
        selected_text = self.session.vars["shuffled_texts"][round_index]

        self.condition = self.session.vars["condition_list"][round_index]

        if self.round_number == 1:
            players = self.get_players()
            random.shuffle(players)

            group_matrix = []
            i = 0
            while i + 1 < len(players):
                typist = players[i]
                observer = players[i + 1]

                typist.custom_role = "typist"
                observer.custom_role = "observer"

                has_obs = random.choice([True, False])

                typist.has_observer = has_obs
                typist.is_evaluated = has_obs

                observer.has_observer = has_obs
                observer.is_evaluated = not has_obs

                typist.task_text = selected_text
                observer.task_text = selected_text

                typist.condition = self.condition
                observer.condition = self.condition

                group_matrix.append([typist, observer])
                i += 2

            if i < len(players):
                solo = players[i]
                solo.custom_role = "typist"
                solo.has_observer = False
                solo.is_evaluated = False
                solo.task_text = selected_text
                solo.condition = self.condition
                group_matrix.append([solo])

            self.set_group_matrix(group_matrix)

        else:
            for p in self.get_players():
                p1 = p.in_round(1)
                p.custom_role = p1.custom_role
                p.has_observer = p1.has_observer
                p.is_evaluated = p1.is_evaluated
                p.task_text = selected_text
                p.condition = self.session.vars["condition_list"][round_index]

            for g in self.get_groups():
                has_obs_in_group = any(
                    p.custom_role == "observer" and p.condition for p in g.get_players()
                )
                g.has_observer = has_obs_in_group
                g.save()
                print(f"[DEBUG] Group {g.id} has_observer: {g.has_observer}")


class Group(BaseGroup):
    latest_typing_duration = models.FloatField(initial=0)
    has_observer = models.BooleanField(initial=False)
    is_evaluated = models.BooleanField(initial=True)

    def get_player_by_role(self, role):
        for p in self.get_players():
            if p.get_role() == role:
                return p
        return None


class Player(BasePlayer):
    task_text = models.StringField()
    typed_text = models.LongStringField()
    start_time = models.FloatField(initial=0)
    end_time = models.FloatField()
    typing_duration = models.FloatField()
    condition = models.BooleanField()

    star_rating = models.IntegerField(
        choices=[1, 2, 3, 4, 5],
        blank=False,
        label="このタイピングの出来を星で評価してください（1〜5）",
    )
    observer_star_rating = models.IntegerField(choices=[5, 4, 3, 2, 1])

    custom_role = models.StringField(null=True, blank=True)
    has_observer = models.BooleanField()
    is_evaluated = models.BooleanField()

    def get_role(self):
        return "typist" if self.id_in_group == 1 else "observer"


# PAGES
class TypingPage(Page):
    form_model = "player"
    form_fields = ["typed_text", "start_time", "end_time"]

    def is_displayed(player: Player):
        return player.get_role() == "typist"

    def vars_for_template(player):
        return {"task_text": C.task_texts[player.round_number - 1]}

    def error_message(player, values):
        task_text = C.task_texts[player.round_number - 1]  # 課題文の取得
        typed = values["typed_text"]
        if typed != task_text:
            return "課題文と完全に一致するように入力してください。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        if player.end_time is not None and player.start_time is not None:
            player.typing_duration = player.end_time - player.start_time
        else:
            player.typing_duration = 0


class WaitTypist(WaitPage):
    wait_for_all_groups = False

    def is_displayed(player: Player):
        print(player.get_role())
        return player.get_role() == "observer"

    def after_all_players_arrive(self):
        pass  # なくてもOKだけど一応書いておく


class ObserverPage(Page):
    form_model = "player"
    form_fields = ["observer_star_rating"]

    def is_displayed(player: Player):
        return player.get_role() == "observer"

    def vars_for_template(self):
        task_text = C.task_texts[self.round_number - 1]
        typist = self.group.get_player_by_id(1)
        duration = typist.field_maybe_none("typing_duration")
        if duration is None:
            duration = 0
        typed = typist.field_maybe_none("typed_text") or ""

        char_count = len(typed) if typed else 1  # 0除算防止！

        seconds_per_char = duration / char_count if char_count > 0 else 0

        return {
            "task_text": task_text,
            "typing_duration": duration,
            "typed_text": typed,
            "seconds_per_char": round(seconds_per_char, 2),
        }


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # 観察者の評価をタイピストに渡す
        for group in self.subsession.get_groups():
            typist = group.get_player_by_role("typist")
            observer = group.get_player_by_role("observer")
            if observer is not None and typist is not None:
                observer_rating = observer.field_maybe_none("observer_star_rating")
                typist.observer_star_rating = (
                    observer_rating if observer_rating is not None else 0
                )
            else:
                # observerがいない場合の代替処理
                typist.observer_star_rating = 0


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.get_role() == "typist"
    
    @staticmethod
    def vars_for_template(player):
        print(f"[DEBUG] player id: {player.id}, role: {player.get_role()}, group.has_observer: {player.group.has_observer}")
        typist = player.group.get_player_by_role("typist")
        observer = player.group.get_player_by_role("observer")
        duration = typist.field_maybe_none("typing_duration") or 0
        typed = typist.field_maybe_none("typed_text") or ""

        context = {
            "task_text": C.task_texts[player.round_number - 1],
            "typing_duration": duration,
            "typed_text": typed,
            "has_observer": player.group.has_observer,
            "observer_star_rating": player.field_maybe_none("observer_star_rating") or "評価なし",
        }

        if player.group.has_observer:
            observer = player.group.get_player_by_role("observer")
            context.update(
                {
                    "observer_star_rating": observer.field_maybe_none(
                        "observer_star_rating"
                    )
                    or "評価なし",
                }
            )
        else:
            context.update(
                {
                    "observer_star_rating": "評価なし",
                }
            )

        return context


page_sequence = [TypingPage, WaitTypist, ObserverPage, ResultsWaitPage, Results]

