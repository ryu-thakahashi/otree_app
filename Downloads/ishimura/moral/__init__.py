from otree.api import *

class C(BaseConstants):
    NAME_IN_URL = 'observe_moral'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 4  # 評価なし・ありを交互に2回繰り返す
    QUESTIONS = [
        dict(
            scenario="あなたの町で感染症が流行し、医薬品が不足しています。あなたの家族には持病のある高齢者がいて、薬が必要です。あなたは薬局で最後の一箱の薬を見つけましたが、後ろには小さな子供を連れた女性が並んでいます。薬局のスタッフは「お一人様一箱」と言いますが、あなたとその女性のどちらかにしか渡せません。",
            question="この場面で、あなたは薬を譲ると思いますか？"
        ),
        dict(
            scenario="あなたは志望する企業のESに「リーダーシップ経験」を書く欄があります。実際のところ、あなたはチームの中の1メンバーとして活動した経験しかありません。しかし、バイトリーダーとしてメンバーをまとめていたように脚色して書けば印象はよくなるはずです。あなたは演技力に一定の自信があり、面接で深掘りされなければバレることもありません。",
            question="この場面で、あなたはESを正直に書こうと思いますか？"
        ),
    ]

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    def get_player_by_role(self, role):
        if role == 'responder':
            return self.get_player_by_id(1)
        elif role == 'evaluator':
            return self.get_player_by_id(2)
        return None

class Player(BasePlayer):
    player_role = models.StringField()  # 'responder' or 'evaluator'
    
    # 初回回答
    answer_0 = models.IntegerField(
        label="この場面で、あなたは薬を譲ると思いますか？(1=絶対に譲らないと思う〜7=必ず譲ると思う)",
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect
    )

    answer_1 = models.IntegerField(
        label="この場面で、あなたはESをどのように書こうと思いますか？（1=完全に脚色して書く〜7=正直に事実のみを書く）",
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect
    )

    # フィードバック後の再回答
    answer_0_after = models.IntegerField(
        label="この場面で、あなたは薬を譲ると思いますか？(1=絶対に譲らないと思う〜7=必ず譲ると思う)",
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect
    )

    answer_1_after = models.IntegerField(
        label="この場面で、あなたはESをどのように書こうと思いますか？（1=完全に脚色して書く〜7=正直に事実のみを書く）",
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect
    )

    # 評価者の評価
    moral_eval = models.IntegerField(
        label="この回答は道徳的だと思いますか？（1=全くそう思わない〜7=非常にそう思う）",
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect
    )

    # 回答者に返す評価（フィードバック用）
    feedback_eval = models.IntegerField()

# ページ設定

class RoleAssignmentWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1
    
    def after_all_players_arrive(self):
        # 1人目がresponder, 2人目がevaluator
        for p in self.group.get_players():
            if p.id_in_group == 1:
                p.player_role = 'responder'
            else:
                p.player_role = 'evaluator'
                
# 実験説明ページ（回答者用）
class ResponderInstructionPage(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.id_in_group == 1

    def vars_for_template(self):
        return {
            'player_role': '回答者',
            'round_number': self.round_number
        }

# 実験説明ページ（評価者用）
class EvaluatorInstructionPage(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.id_in_group == 2

    def vars_for_template(self):
        return {
            'player_role': '評価者',
            'round_number': self.round_number
        }

# 実験開始前の待機ページ
class InstructionWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1
    
    wait_for_all_groups = False
    
    def after_all_players_arrive(self):
        pass
    
class ResponderPage(Page):
    def is_displayed(self):
        # player_roleに依存せず、id_in_groupで判定
        return self.id_in_group == 1

    form_model = 'player'
    
    def get_form_fields(self):
        # ラウンド1,2では質問0、ラウンド3,4では質問1
        if self.round_number <= 2:
            return ['answer_0']
        else:
            return ['answer_1']

    def vars_for_template(self):
        eval_condition = 'あり' if self.round_number % 2 == 0 else 'なし'
        
        scale_text = "(1 = 全くそう思わない〜7 = 非常にそう思う)"
        
        if self.round_number <= 2:
            current_scenario = C.QUESTIONS[0]['scenario']
            current_question = C.QUESTIONS[0]['question']
            question_index = 0
        else:
            current_scenario = C.QUESTIONS[1]['scenario']
            current_question = C.QUESTIONS[1]['question']
            question_index = 1
            
        return {
            'eval_condition': eval_condition,
            'round_number': self.round_number,
            'current_scenario': current_scenario,
            'current_question': current_question,
            'question_index': question_index,
            'scale_text': scale_text  # 統一されたスケール
        }

    def before_next_page(self, timeout_happened=False):
        # ResponderPageでは評価の取得は不要
        # 評価は後でEvaluatorPageで行われる
        pass

class EvaluatorWaitPage(WaitPage):
    def is_displayed(self):
        # evaluatorのみ表示され、responderの回答を待つ
        return self.id_in_group == 2
    
    wait_for_all_groups = False  # グループ内での待機
    
    def after_all_players_arrive(self):
        pass  # 特に処理は不要
    
class EvaluatorPage(Page):
    def is_displayed(self):
        # player_roleに依存せず、id_in_groupで判定
        return self.id_in_group == 2 and self.round_number % 2 == 0

    form_model = 'player'
    form_fields = ['moral_eval']

    def vars_for_template(self):
        responder = self.group.get_player_by_id(1)
        
        scale_text = "(1 = 全くそう思わない〜7 = 非常にそう思う)"
        
        # 現在のラウンドに応じた回答を取得
        if self.round_number <= 2:
            answer_0 = responder.field_maybe_none('answer_0') if responder else None
            answer_1 = None
            question_scenario = C.QUESTIONS[0]['scenario']
            question_text = C.QUESTIONS[0]['question']
        else:
            answer_0 = None
            answer_1 = responder.field_maybe_none('answer_1') if responder else None
            question_scenario = C.QUESTIONS[1]['scenario']
            question_text = C.QUESTIONS[1]['question']
            
        return {
            'responder': responder,
            'answer_0': answer_0,
            'answer_1': answer_1,
            'question_scenario': question_scenario,
            'question_text': question_text,
            'scale_text': scale_text,  # 統一されたスケール
            'round_number': self.round_number,
            'eval_condition': 'あり'
        }
    
    def before_next_page(self, timeout_happened=False):
        # 評価後、回答者のfeedback_evalフィールドに評価を設定
        responder = self.group.get_player_by_id(1)
        if responder:
            responder.feedback_eval = self.moral_eval
        
class ResponderWaitPage(WaitPage):
    def is_displayed(self):
        # 偶数ラウンドでresponderのみ表示
        return self.id_in_group == 1 and self.round_number % 2 == 0
    
    wait_for_all_groups = False

class FeedbackPage(Page):
    def is_displayed(self):
        # 回答者に評価フィードバックを見せるページ
        return self.id_in_group == 1 and self.round_number % 2 == 0

    def vars_for_template(self):
        evaluator = self.group.get_player_by_id(2)
        feedback_value = evaluator.field_maybe_none('moral_eval') if evaluator else 0
        return {
            'feedback_eval': feedback_value if feedback_value is not None else 0,
            'round_number': self.round_number  # この行を追加
        }

class SecondRespondPage(Page):
    def is_displayed(self):
        return self.id_in_group == 1 and self.round_number % 2 == 0

    form_model = 'player'
    
    def get_form_fields(self):
        if self.round_number <= 2:
            return ['answer_0_after']
        else:
            return ['answer_1_after']

    def vars_for_template(self):
        scale_text = "(1 = 全くそう思わない〜7 = 非常にそう思う)"
        
        if self.round_number <= 2:
            current_scenario = C.QUESTIONS[0]['scenario']
            current_question = C.QUESTIONS[0]['question']
            question_index = 0
        else:
            current_scenario = C.QUESTIONS[1]['scenario']
            current_question = C.QUESTIONS[1]['question']
            question_index = 1
            
        return {
            'eval_condition': 'あり',
            'round_number': self.round_number,
            'current_scenario': current_scenario,
            'current_question': current_question,
            'question_index': question_index,
            'scale_text': scale_text,
            'is_after_feedback': True  
        }

class SecondEvaluatorWaitPage(WaitPage):
    def is_displayed(self):
        return self.id_in_group == 2 and self.round_number % 2 == 0
    
    wait_for_all_groups = False

class CheckSecondPage(Page):
    def is_displayed(self):
        return self.id_in_group == 2 and self.round_number % 2 == 0

    def vars_for_template(self):
        responder = self.group.get_player_by_id(1)
        
        scale_text = "(1 = 全くそう思わない〜7 = 非常にそう思う)"
        
        # 現在のラウンドに応じた初回回答と再回答を取得
        if self.round_number <= 2:
            answer_original = responder.field_maybe_none('answer_0') if responder else None
            answer_after = responder.field_maybe_none('answer_0_after') if responder else None
            question_scenario = C.QUESTIONS[0]['scenario']
            question_text = C.QUESTIONS[0]['question']
        else:
            answer_original = responder.field_maybe_none('answer_1') if responder else None
            answer_after = responder.field_maybe_none('answer_1_after') if responder else None
            question_scenario = C.QUESTIONS[1]['scenario']
            question_text = C.QUESTIONS[1]['question']
            
        return {
            'responder': responder,
            'answer_original': answer_original,
            'answer_after': answer_after,
            'question_scenario': question_scenario,
            'question_text': question_text,
            'scale_text': scale_text,
            'round_number': self.round_number,
            "difference": answer_after - answer_original if answer_after is not None and answer_original is not None else None,
        }
        
class SecondRespondorWaitPage(WaitPage):
    def is_displayed(self):
        return self.id_in_group == 1 and self.round_number % 2 == 0
    
    wait_for_all_groups = False

page_sequence = [
    RoleAssignmentWaitPage,
    ResponderInstructionPage,
    EvaluatorInstructionPage,
    InstructionWaitPage,
    ResponderPage,
    EvaluatorWaitPage,  
    EvaluatorPage,
    ResponderWaitPage,  
    FeedbackPage,
    SecondRespondPage,      
    SecondEvaluatorWaitPage,  
    CheckSecondPage,  
    SecondRespondorWaitPage,  
]