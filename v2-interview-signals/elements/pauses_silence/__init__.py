from elements.pauses_silence.fp import score_fp
from elements.pauses_silence.hp import score_hp
from elements.pauses_silence.lat import score_lat
from elements.pauses_silence.sil import score_sil
from elements.pauses_silence.op import score_op
from elements.pauses_silence.rp import score_rp
from elements.pauses_silence.pau import score_pau

ALL_PAUSES_SILENCE = [score_fp, score_hp, score_lat, score_sil, score_op, score_rp, score_pau]
