from elements.conversation_behavior.adp import score_adp
from elements.conversation_behavior.ask import score_ask
from elements.conversation_behavior.bf import score_bf
from elements.conversation_behavior.lis import score_lis
from elements.conversation_behavior.ans import score_ans
from elements.conversation_behavior.turn import score_turn
from elements.conversation_behavior.rec import score_rec

ALL_CONVERSATION_BEHAVIOR = [score_adp, score_ask, score_bf, score_lis, score_ans, score_turn, score_rec]
