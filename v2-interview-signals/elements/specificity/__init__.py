from elements.specificity.ver import score_ver
from elements.specificity.step import score_step
from elements.specificity.num import score_num
from elements.specificity.nam import score_nam
from elements.specificity.det import score_det
from elements.specificity.con import score_con

ALL_SPECIFICITY = [score_ver, score_step, score_num, score_nam, score_det, score_con]
