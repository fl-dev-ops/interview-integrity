from elements.language_quality.grm import score_grm
from elements.language_quality.ten import score_ten
from elements.language_quality.sva import score_sva
from elements.language_quality.sent import score_sent
from elements.language_quality.voc import score_voc
from elements.language_quality.reg import score_reg
from elements.language_quality.tech import score_tech
from elements.language_quality.idi import score_idi
from elements.language_quality.repw import score_repw
from elements.language_quality.pwr import score_pwr
from elements.language_quality.gap import score_gap

ALL_LANGUAGE_QUALITY = [score_grm, score_ten, score_sva, score_sent, score_voc,
                        score_reg, score_tech, score_idi, score_repw, score_pwr, score_gap]
