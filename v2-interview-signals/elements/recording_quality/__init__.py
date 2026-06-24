from elements.recording_quality.dia import score_dia
from elements.recording_quality.snr import score_snr
from elements.recording_quality.drop import score_drop
from elements.recording_quality.clip import score_clip
from elements.recording_quality.echo import score_echo
from elements.recording_quality.mic import score_mic
from elements.recording_quality.noi import score_noi

ALL_RECORDING_QUALITY = [score_dia, score_snr, score_drop, score_clip, score_echo, score_mic, score_noi]
