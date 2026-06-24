from elements.voice_delivery import ALL_VOICE_DELIVERY
from elements.pace_rhythm import ALL_PACE_RHYTHM
from elements.pauses_silence import ALL_PAUSES_SILENCE
from elements.fluency import ALL_FLUENCY
from elements.language_quality import ALL_LANGUAGE_QUALITY
from elements.answer_structure import ALL_ANSWER_STRUCTURE
from elements.specificity import ALL_SPECIFICITY
from elements.reasoning import ALL_REASONING
from elements.conversation_behavior import ALL_CONVERSATION_BEHAVIOR
from elements.confidence_signals import ALL_CONFIDENCE_SIGNALS
from elements.role_competency import ALL_ROLE_COMPETENCY
from elements.recording_quality import ALL_RECORDING_QUALITY

ALL_SCORERS = (
    ALL_VOICE_DELIVERY + ALL_PACE_RHYTHM + ALL_PAUSES_SILENCE + ALL_FLUENCY +
    ALL_LANGUAGE_QUALITY + ALL_ANSWER_STRUCTURE + ALL_SPECIFICITY + ALL_REASONING +
    ALL_CONVERSATION_BEHAVIOR + ALL_CONFIDENCE_SIGNALS + ALL_ROLE_COMPETENCY +
    ALL_RECORDING_QUALITY
)
