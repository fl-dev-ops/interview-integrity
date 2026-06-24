from elements.reasoning.why import score_why
from elements.reasoning.cae import score_cae
from elements.reasoning.opt import score_opt
from elements.reasoning.trd import score_trd
from elements.reasoning.jud import score_jud
from elements.reasoning.ins import score_ins
from elements.reasoning.ref import score_ref
from elements.reasoning.beyond import score_beyond

ALL_REASONING = [score_why, score_cae, score_opt, score_trd, score_jud, score_ins, score_ref, score_beyond]
