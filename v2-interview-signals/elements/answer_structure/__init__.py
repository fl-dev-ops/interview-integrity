from elements.answer_structure.str import score_str
from elements.answer_structure.ctx import score_ctx
from elements.answer_structure.act import score_act
from elements.answer_structure.res import score_res
from elements.answer_structure.ex import score_ex
from elements.answer_structure.star import score_star
from elements.answer_structure.rel import score_rel
from elements.answer_structure.drf import score_drf

ALL_ANSWER_STRUCTURE = [score_str, score_ctx, score_act, score_res, score_ex, score_star, score_rel, score_drf]
