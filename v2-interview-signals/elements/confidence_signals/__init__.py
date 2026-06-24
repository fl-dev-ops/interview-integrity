from elements.confidence_signals.trust import score_trust
from elements.confidence_signals.pres import score_pres
from elements.confidence_signals.hold import score_hold
from elements.confidence_signals.recv import score_recv
from elements.confidence_signals.own import score_own
from elements.confidence_signals.conf import score_conf
from elements.confidence_signals.nerv import score_nerv

ALL_CONFIDENCE_SIGNALS = [score_trust, score_pres, score_hold, score_recv, score_own, score_conf, score_nerv]
