# Interview Signals Scoring Spec

This document defines the elements in the **Periodic Table of Interview Signals** and explains how each can be scored.

The table intentionally mixes raw measurements, derived signals, and judgment-based signals. That is useful visually, but it must be explicit in scoring. `WPM` and `Trust` should not be treated as the same kind of value.

## Signal Layers

| Layer | Code | Meaning | Example |
|---|---|---|---|
| Raw Metric | `M` | Directly measured from transcript/audio | `WPM`, `Noi`, `FP` |
| Derived Signal | `D` | Calculated from multiple metrics | `Pac`, `Pau`, `Flo` |
| Judgment Signal | `J` | Requires context/semantic interpretation | `Pres`, `Trust`, `Prof` |
| Composite Signal | `C` | Higher-level aggregate of many signals | `Conf`, `Comp` |

## Scoring Types

| Type | Code | Meaning |
|---|---|---|
| Boolean | `BOOL` | Present/absent |
| Count | `COUNT` | Number of occurrences |
| Rate | `RATE` | Count normalized by time, answer, or words |
| Range | `RANGE` | Numeric value with target bands |
| Categorical | `CAT` | Fixed labels, not necessarily ordered |
| Ordinal | `ORD` | Ordered score, usually `0-4` |
| Composite | `COMP` | Formula or weighted combination of other signals |

## Default Ordinal Scale

Use this when a signal is scored on `0-4`.

| Score | Meaning |
|---:|---|
| 0 | Not demonstrated, damaging, or not measurable |
| 1 | Weak; frequent problems or strong negative signal |
| 2 | Basic; understandable but inconsistent |
| 3 | Good; mostly controlled with minor issues |
| 4 | Strong; controlled, intentional, and reliable under pressure |

## Should Raw And Derived Signals Be In One Table?

Yes, visually, but not analytically.

The periodic table should be treated as a taxonomy of signals, not a flat scoring model. Each tile should have a layer tag:

| Tag | Meaning |
|---|---|
| `M` | Raw metric |
| `D` | Derived signal |
| `J` | Judgment signal |
| `C` | Composite signal |

Recommended scoring flow:

```text
Raw metrics -> Derived signals -> Judgment signals -> Category scores
```

Example:

```text
WPM + Rushing + Dragging + Acceleration + Deceleration -> Pace Control -> Confidence / Presence
```

## Voice Delivery

### Var - Vocal Variety

- Layer: `D`
- Scoring type: `ORD`
- Raw value: pitch/tone variation across an answer or interview
- Depends on: pitch movement, tone shifts, emphasis patterns, monotony
- Criteria:
  - 0: flat or erratic enough to hurt comprehension
  - 1: mostly flat; little expressive variation
  - 2: some variation, but inconsistent or unnatural
  - 3: natural variation in most answers
  - 4: deliberate variation that supports meaning and emphasis

### Ste - Steadiness

- Layer: `D`
- Scoring type: `ORD`
- Raw value: stability of volume, pace, and tone under normal and harder questions
- Depends on: volume variation, pace shifts, pressure hold, recovery speed
- Criteria:
  - 0: collapses or becomes difficult to evaluate
  - 1: frequent drops, tremors, or instability
  - 2: understandable but visibly unstable
  - 3: mostly stable with recoverable dips
  - 4: stable throughout, including under pressure

### Ton - Tone

- Layer: `J`
- Scoring type: `CAT + ORD`
- Raw value: listener perception of voice quality
- Categories: warm, nervous, flat, robotic, casual, confident, strained
- Criteria:
  - 0: tone actively undermines the interview
  - 1: tone is inappropriate, very anxious, or robotic
  - 2: acceptable but inconsistent
  - 3: professional and mostly natural
  - 4: warm, composed, and aligned with the interview context

### Prj - Projection

- Layer: `D`
- Scoring type: `ORD`
- Raw value: perceived voice carrying power and audibility
- Depends on: volume, clarity, microphone quality, background noise
- Criteria:
  - 0: voice does not carry; words regularly lost
  - 1: often weak or swallowed
  - 2: audible but not well projected
  - 3: clear projection most of the time
  - 4: clear, confident, and easy to hear throughout

### En - Energy

- Layer: `J`
- Scoring type: `ORD`
- Raw value: perceived liveliness and engagement
- Depends on: tone, pace, variation, response energy
- Criteria:
  - 0: disengaged or extremely flat
  - 1: low energy across most answers
  - 2: some engagement but inconsistent
  - 3: engaged and appropriate
  - 4: energetic without sounding rushed or performative

### Clr - Clarity

- Layer: `D`
- Scoring type: `ORD`
- Raw value: how easily words can be heard and understood
- Depends on: articulation, volume, recording quality, pace
- Criteria:
  - 0: often unintelligible
  - 1: many words hard to understand
  - 2: understandable with effort
  - 3: clear with minor issues
  - 4: consistently easy to understand

### Vol - Volume

- Layer: `M`
- Scoring type: `RANGE + ORD`
- Raw value: loudness / audibility level
- Criteria:
  - 0: mostly inaudible
  - 1: often too quiet or too loud
  - 2: audible but inconsistent
  - 3: clear most of the time
  - 4: clear and well-projected throughout

### Mon - Monotony

- Layer: `D`
- Scoring type: `ORD`
- Raw value: degree of flatness in pitch/tone
- Note: higher score means less monotony
- Criteria:
  - 0: highly monotonous and disengaging
  - 1: mostly flat
  - 2: some variation but limited
  - 3: natural variation most of the time
  - 4: expressive and appropriately varied

## Pace & Rhythm

### Acc - Acceleration

- Layer: `M`
- Scoring type: `RANGE + ORD`
- Raw value: increase in WPM within an answer or under pressure
- Criteria:
  - 0: severe speeding up that harms comprehension
  - 1: frequent uncontrolled acceleration
  - 2: noticeable but manageable acceleration
  - 3: minor natural acceleration
  - 4: speed remains controlled when difficulty changes

### Dec - Deceleration

- Layer: `M`
- Scoring type: `RANGE + ORD`
- Raw value: decrease in WPM or momentum within an answer
- Criteria:
  - 0: slows/fades until answer breaks down
  - 1: frequent dragging or loss of momentum
  - 2: uneven slowing but answer survives
  - 3: mostly controlled slowing
  - 4: uses slowing deliberately for emphasis or thought

### Pac - Pace Control

- Layer: `D`
- Scoring type: `ORD`
- Raw value: consistency and appropriateness of speaking speed
- Depends on: `WPM`, `Rus`, `Drg`, `Acc`, `Dec`, pause distribution
- Criteria:
  - 0: pace consistently disrupts understanding
  - 1: frequent rushing, dragging, or unstable rhythm
  - 2: understandable but uneven
  - 3: mostly controlled with minor variation
  - 4: controlled, natural, and stable under pressure

### Rhy - Rhythm

- Layer: `D`
- Scoring type: `ORD`
- Raw value: timing pattern across words, phrases, and pauses
- Depends on: pace control, pauses, fluency, sentence boundaries
- Criteria:
  - 0: rhythm is chaotic or broken
  - 1: frequent choppiness or awkward rushes
  - 2: somewhat uneven but understandable
  - 3: mostly natural rhythm
  - 4: smooth, intentional rhythm that supports meaning

### WPM - Words Per Minute

- Layer: `M`
- Scoring type: `RANGE`
- Raw value: spoken words divided by speaking time in minutes
- Normalization: per answer and whole interview
- Suggested healthy interview range: `100-160 WPM`
- Criteria:
  - 0: below `70` or above `210` WPM
  - 1: `70-90` or `180-210` WPM
  - 2: `90-100` or `160-180` WPM
  - 3: `100-120` or `145-160` WPM
  - 4: `120-145` WPM

### Rus - Rushing

- Layer: `D`
- Scoring type: `ORD`
- Raw value: frequency/severity of too-fast speech
- Note: higher score means less rushing
- Depends on: WPM, articulation loss, acceleration
- Criteria:
  - 0: rushing makes content hard to follow
  - 1: frequent rushing
  - 2: occasional rushing under pressure
  - 3: minor rushing, quickly corrected
  - 4: no meaningful rushing

### Drg - Dragging

- Layer: `D`
- Scoring type: `ORD`
- Raw value: frequency/severity of too-slow speech or dead space
- Note: higher score means less dragging
- Depends on: WPM, silence duration, deceleration
- Criteria:
  - 0: dragging makes evaluation difficult
  - 1: frequent long dead spaces or fading momentum
  - 2: occasional dragging
  - 3: mostly steady with minor slow spots
  - 4: no meaningful dragging

## Pauses & Silence

### OP - Owned Pause

- Layer: `D`
- Scoring type: `ORD`
- Raw value: intentional, controlled thinking pauses
- Depends on: pause duration, placement, recovery quality, absence of filler
- Criteria:
  - 0: pauses never feel controlled
  - 1: rare owned pauses; most pauses feel imposed
  - 2: mixed controlled and uncontrolled pauses
  - 3: most pauses are purposeful
  - 4: pauses consistently feel deliberate and confident

### RP - Recovery Pause

- Layer: `D`
- Scoring type: `ORD`
- Raw value: pause followed by a clearer or better answer
- Depends on: pause placement, post-pause answer quality
- Criteria:
  - 0: pauses lead to breakdown
  - 1: recovery is rare or weak
  - 2: sometimes recovers after pausing
  - 3: usually resumes clearly after pauses
  - 4: pauses reliably improve answer quality

### Pau - Pause Quality

- Layer: `D`
- Scoring type: `ORD`
- Raw value: whether pauses help or hurt communication
- Depends on: `Lat`, `Sil`, `FP`, `HP`, `OP`, `RP`
- Criteria:
  - 0: pauses are disruptive or panicked
  - 1: frequent awkward or uncontrolled pauses
  - 2: mixed; some useful, some disruptive
  - 3: mostly calm and well placed
  - 4: deliberate, natural, and confidence-building

### HP - Hesitation Pause

- Layer: `M + D`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: mid-thought pause that signals uncertainty
- Note: higher ordinal score means fewer harmful hesitations
- Criteria:
  - 0: frequent hesitations break most answers
  - 1: many hesitation pauses
  - 2: some hesitation, meaning survives
  - 3: few hesitation pauses
  - 4: no meaningful hesitation pauses

### Lat - Latency

- Layer: `M`
- Scoring type: `RANGE + ORD`
- Raw value: time from interviewer question end to candidate answer start
- Suggested healthy range: `2-5 seconds`
- Criteria:
  - 0: consistently under `1s` or over `6s`
  - 1: often too fast or too delayed
  - 2: inconsistent but acceptable
  - 3: mostly `2-5s`
  - 4: consistently `2-4s`, calm and ready

### Sil - Long Silence

- Layer: `M`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: silent gaps above threshold, e.g. `2.5s+`
- Note: higher ordinal score means fewer harmful silences
- Criteria:
  - 0: repeated long silences make evaluation difficult
  - 1: several disruptive long silences
  - 2: some long silences, but answer survives
  - 3: rare long silences
  - 4: no disruptive long silences

### FP - Filled Pause

- Layer: `M`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: filler tokens such as `um`, `uh`, `like`, `you know`
- Normalization: per minute or per 100 words
- Note: higher ordinal score means fewer harmful fillers
- Criteria:
  - 0: fillers dominate or repeatedly break flow
  - 1: frequent fillers distract from content
  - 2: noticeable but tolerable fillers
  - 3: occasional fillers
  - 4: fillers are absent or negligible

## Fluency

### Coh - Cohesion

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: how well ideas connect across phrases/sentences
- Depends on: connectors, structure, sentence flow, relevance
- Criteria:
  - 0: disconnected words or fragments
  - 1: mostly list-like, weak connection
  - 2: basic sequence with some gaps
  - 3: clear flow between ideas
  - 4: smooth, structured, and purposeful flow

### Flo - Speech Flow

- Layer: `D`
- Scoring type: `ORD`
- Raw value: smoothness of spoken output
- Depends on: false starts, repetition, hesitation pauses, run-ons, fragmentation
- Criteria:
  - 0: speech repeatedly breaks down
  - 1: frequent stops/restarts
  - 2: uneven but understandable
  - 3: mostly smooth with minor disruption
  - 4: effortless or intentionally paced flow

### SC - Self-Correct

- Layer: `M + D`
- Scoring type: `COUNT + ORD`
- Raw value: explicit corrections mid-sentence
- Criteria:
  - 0: corrections cause breakdown or confusion
  - 1: frequent corrections disrupt flow
  - 2: some corrections, meaning survives
  - 3: few effective corrections
  - 4: corrections are rare or used skillfully

### Run - Run-On Speech

- Layer: `D`
- Scoring type: `ORD`
- Raw value: speech without clean sentence/idea boundaries
- Note: higher score means fewer run-ons
- Criteria:
  - 0: run-ons make answer hard to parse
  - 1: frequent run-ons
  - 2: some run-ons but meaning survives
  - 3: mostly clean boundaries
  - 4: clear sentence/idea boundaries throughout

### Frag - Fragments

- Layer: `M + D`
- Scoring type: `COUNT + ORD`
- Raw value: incomplete or broken phrases
- Note: higher score means fewer harmful fragments
- Criteria:
  - 0: mostly fragments
  - 1: frequent fragments
  - 2: some fragments, understandable
  - 3: few fragments
  - 4: complete phrasing throughout

### FS - False Starts

- Layer: `M`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: stopped/restarted phrases
- Normalization: per answer or per 100 words
- Note: higher ordinal score means fewer false starts
- Criteria:
  - 0: constant false starts prevent clear meaning
  - 1: frequent false starts
  - 2: noticeable but manageable
  - 3: occasional false starts
  - 4: almost none

### Rep - Repetition

- Layer: `M`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: repeated words or phrases
- Normalization: per answer or per 100 words
- Note: higher ordinal score means less harmful repetition
- Criteria:
  - 0: repetition blocks meaning
  - 1: frequent repetition distracts
  - 2: noticeable repetition
  - 3: minor repetition
  - 4: no meaningful repetition

## Language Quality

### Idi - Idioms

- Layer: `J`
- Scoring type: `ORD`
- Raw value: natural idiomatic/colloquial phrasing appropriate to context
- Criteria:
  - 0: unnatural phrasing repeatedly confuses meaning
  - 1: very limited natural phrasing
  - 2: some natural phrases but inconsistent
  - 3: mostly natural, context-appropriate language
  - 4: idiomatic ease with professional control

### Reg - Register

- Layer: `J`
- Scoring type: `ORD`
- Raw value: fit between language style and interview context
- Criteria:
  - 0: clearly inappropriate for interview
  - 1: too casual, robotic, or awkward
  - 2: acceptable but inconsistent
  - 3: professional most of the time
  - 4: polished and adaptable to context

### Tech - Technical

- Layer: `J`
- Scoring type: `ORD`
- Raw value: correct and natural use of domain-specific vocabulary
- Criteria:
  - 0: no relevant technical language when expected
  - 1: technical words are incorrect or forced
  - 2: some correct technical terms, limited depth
  - 3: relevant technical vocabulary used naturally
  - 4: precise technical language with clear explanation

### Voc - Vocabulary

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: breadth, precision, and level of word choice
- Depends on: word variety, repetition, technical vocabulary, power words
- Criteria:
  - 0: isolated/basic words only
  - 1: very limited range; repeated basic words
  - 2: sufficient but simple range
  - 3: varied and appropriate vocabulary
  - 4: broad, precise, and flexible vocabulary

### Sent - Sentence

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: sentence completeness, order, and complexity
- Criteria:
  - 0: mostly incomplete phrases
  - 1: frequent broken or incorrect sentences
  - 2: simple sentences mostly understandable
  - 3: mostly complete with some complexity
  - 4: complete, varied, and controlled structures

### Ten - Tense

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: tense errors relative to intended meaning
- Note: higher ordinal score means better tense accuracy
- Criteria:
  - 0: tense confusion prevents understanding
  - 1: frequent tense errors
  - 2: some tense errors, meaning survives
  - 3: mostly accurate tense use
  - 4: accurate and flexible tense control

### SVA - Agreement

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: subject-verb agreement errors
- Note: higher ordinal score means better agreement accuracy
- Criteria:
  - 0: agreement errors repeatedly block meaning
  - 1: frequent agreement errors
  - 2: some errors, mostly understandable
  - 3: mostly correct agreement
  - 4: consistently correct agreement

### Grm - Grammar

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: overall grammatical control
- Depends on: tense, agreement, sentence structure, word order
- Criteria:
  - 0: grammar prevents evaluation
  - 1: frequent errors cause strain
  - 2: errors present but meaning usually survives
  - 3: mostly accurate grammar
  - 4: high grammatical control with complex structures

### RepW - Word Repeat

- Layer: `M`
- Scoring type: `COUNT + RATE + ORD`
- Raw value: repeated lexical choices, excluding necessary terms
- Note: higher score means less harmful repetition
- Criteria:
  - 0: word repetition severely limits meaning
  - 1: frequent repeated words
  - 2: noticeable repetition
  - 3: some repetition but acceptable
  - 4: varied word choice

## Answer Structure

### STAR - STAR

- Layer: `C`
- Scoring type: `COMP + ORD`
- Raw value: completeness of Situation, Task, Action, Result
- Depends on: `Ctx`, `Act`, `Res`, `Step`, `Ex`
- Criteria:
  - 0: no STAR components clear
  - 1: only situation or general claim present
  - 2: situation and action present, weak result
  - 3: clear situation/action/result
  - 4: complete STAR with insight or impact

### Ex - Example

- Layer: `J`
- Scoring type: `ORD`
- Raw value: strength and relevance of chosen example
- Criteria:
  - 0: no example
  - 1: generic or weak example
  - 2: real example but not strongest
  - 3: relevant and useful example
  - 4: precise, memorable, competency-revealing example

### Res - Result

- Layer: `J`
- Scoring type: `ORD`
- Raw value: outcome after the candidate's action
- Criteria:
  - 0: no result stated
  - 1: vague or passive result
  - 2: result stated but not specific
  - 3: clear result
  - 4: clear, quantified, or meaningful result

### Act - Action

- Layer: `J`
- Scoring type: `ORD`
- Raw value: candidate's own action in the situation
- Criteria:
  - 0: no personal action
  - 1: vague group/passive action
  - 2: personal action present but broad
  - 3: clear personal action
  - 4: precise action with ownership and rationale

### Str - Structure

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: answer organization
- Depends on: relevance, context, action, result, cohesion
- Criteria:
  - 0: no clear structure
  - 1: scattered or list-like
  - 2: basic order but incomplete
  - 3: clear beginning/middle/end
  - 4: purposeful structure that builds a strong answer

### Ctx - Context

- Layer: `J`
- Scoring type: `ORD`
- Raw value: named situation, project, place, role, or task
- Criteria:
  - 0: no context
  - 1: vague context only
  - 2: real context named
  - 3: clear context with role/task
  - 4: precise, verifiable context

### Drf - Drift

- Layer: `J`
- Scoring type: `ORD`
- Raw value: degree of off-topic movement
- Note: higher score means less drift
- Criteria:
  - 0: answer is mostly off-topic
  - 1: frequent drift
  - 2: some drift but returns to question
  - 3: mostly on point
  - 4: every sentence earns its place

### Rel - Relevance

- Layer: `J`
- Scoring type: `ORD`
- Raw value: fit between answer and question asked
- Criteria:
  - 0: could answer any question
  - 1: loosely related but misses the ask
  - 2: addresses the question basically
  - 3: directly answers with a relevant example
  - 4: answers and connects to a broader principle

## Specificity

### Ver - Verifiable

- Layer: `J`
- Scoring type: `ORD`
- Raw value: whether details are checkable or concrete enough to verify
- Depends on: context, names, numbers, dates, systems
- Criteria:
  - 0: hollow and unverifiable
  - 1: mostly vague claims
  - 2: some checkable detail
  - 3: clear verifiable details
  - 4: exact, reproducible, and credible detail

### Step - Steps

- Layer: `J`
- Scoring type: `ORD`
- Raw value: sequence of actions/process
- Criteria:
  - 0: no process visible
  - 1: one vague step
  - 2: basic sequence
  - 3: clear step-by-step process
  - 4: full process plus follow-up/system/change

### Num - Numbers

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: meaningful numbers, dates, amounts, metrics, counts
- Criteria:
  - 0: no numbers where useful
  - 1: vague quantities only
  - 2: some numbers but limited value
  - 3: useful specific numbers
  - 4: exact, relevant, and impact-bearing numbers

### Nam - Names

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: named tools, projects, organizations, systems, roles, people
- Criteria:
  - 0: no named entities where useful
  - 1: vague labels only
  - 2: some named entities
  - 3: useful specific names
  - 4: names make the answer concrete and verifiable

### Det - Detail

- Layer: `J`
- Scoring type: `ORD`
- Raw value: specificity and depth of answer details
- Depends on: names, numbers, context, steps
- Criteria:
  - 0: no meaningful detail
  - 1: vague/general detail
  - 2: enough detail to understand
  - 3: specific and useful detail
  - 4: precise detail that recreates the situation

### Con - Concrete

- Layer: `J`
- Scoring type: `ORD`
- Raw value: concrete language versus abstract/vague claims
- Criteria:
  - 0: entirely vague or abstract
  - 1: mostly vague claims
  - 2: mixed vague and concrete language
  - 3: mostly concrete language
  - 4: precise, vivid, and concrete phrasing

## Reasoning

### Ref - Reflection

- Layer: `J`
- Scoring type: `ORD`
- Raw value: what changed afterward because of the experience
- Criteria:
  - 0: no reflection
  - 1: generic lesson only
  - 2: basic learning stated
  - 3: specific reflection and change
  - 4: generative learning that changed future behavior/system

### Ins - Insight

- Layer: `J`
- Scoring type: `ORD`
- Raw value: new understanding produced by the experience
- Criteria:
  - 0: no insight
  - 1: cliché or generic insight
  - 2: simple insight
  - 3: specific and relevant insight
  - 4: deeper principle or transferable learning

### Trd - Tradeoffs

- Layer: `J`
- Scoring type: `ORD`
- Raw value: awareness of what was gained/lost in a decision
- Criteria:
  - 0: no tradeoff awareness
  - 1: one-sided decision only
  - 2: basic tradeoff mentioned
  - 3: clear tradeoff explanation
  - 4: nuanced tradeoff reasoning with consequence

### Opt - Options

- Layer: `J`
- Scoring type: `ORD`
- Raw value: alternatives considered before choosing
- Criteria:
  - 0: no option or decision visible
  - 1: states action without alternatives
  - 2: implies alternatives weakly
  - 3: compares more than one option
  - 4: explains alternatives and why chosen approach was best

### Jud - Judgment

- Layer: `J`
- Scoring type: `ORD`
- Raw value: deliberate professional choice and ownership of consequence
- Criteria:
  - 0: no judgment visible
  - 1: says safe/right thing without demonstrating it
  - 2: basic decision visible
  - 3: deliberate informed choice with owned outcome
  - 4: strong judgment, clear consequence, no deflection

### C&E - Cause/Effect

- Layer: `J`
- Scoring type: `ORD`
- Raw value: causal link between action and result
- Criteria:
  - 0: no cause/effect
  - 1: sequence without explanation
  - 2: simple cause/effect visible
  - 3: clear consequence chain
  - 4: nuanced causal reasoning with impact

### Why - Reasoning

- Layer: `J`
- Scoring type: `ORD`
- Raw value: explanation of why a choice/action was made
- Criteria:
  - 0: pure description only
  - 1: weak or circular reason
  - 2: basic reason present
  - 3: clear reasoning behind action
  - 4: reasoning plus insight and changed behavior

## Conversation Behavior

### Adp - Adaptability

- Layer: `J`
- Scoring type: `ORD`
- Raw value: adjustment to follow-up questions, corrections, or new direction
- Criteria:
  - 0: cannot adapt
  - 1: struggles with any change
  - 2: adapts with help
  - 3: handles follow-ups reasonably well
  - 4: adapts naturally and strengthens the answer

### Rec - Recovery

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: ability to regain control after weak start, pause, confusion, or error
- Depends on: self-correction, recovery pause, answer improvement
- Criteria:
  - 0: does not recover
  - 1: recovery is slow or incomplete
  - 2: sometimes recovers
  - 3: usually recovers well
  - 4: recovers immediately and confidently

### Ask - Clarifying

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: appropriate clarifying questions when prompt is unclear
- Criteria:
  - 0: does not clarify and answers wrong question
  - 1: rarely clarifies when needed
  - 2: clarification behavior is acceptable
  - 3: asks useful clarifying questions when appropriate
  - 4: clarifies strategically without overusing it

### B&F - Back/Forth

- Layer: `J`
- Scoring type: `ORD`
- Raw value: ability to sustain interview exchange
- Criteria:
  - 0: cannot continue without heavy support
  - 1: needs frequent interviewer rescue
  - 2: manages basic exchange
  - 3: keeps conversation going with light support
  - 4: handles conversation and follow-ups naturally

### Lis - Listening

- Layer: `J`
- Scoring type: `ORD`
- Raw value: evidence the candidate understood the question
- Depends on: relevance, direct answer, follow-up handling
- Criteria:
  - 0: repeatedly misses question
  - 1: often misunderstands or ignores key ask
  - 2: generally understands simple prompts
  - 3: understands and responds directly
  - 4: listens actively and incorporates prompt nuance

### Ans - Responsive

- Layer: `J`
- Scoring type: `ORD`
- Raw value: directness of response to prompt
- Criteria:
  - 0: no real answer
  - 1: indirect or evasive
  - 2: basic answer present
  - 3: direct and relevant answer
  - 4: direct answer with strong supporting detail

### Turn - Turn-Taking

- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: interruptions, over-talking, or awkward turn timing
- Criteria:
  - 0: turn-taking repeatedly disrupts interview
  - 1: frequent interruptions/overlap
  - 2: some awkward timing
  - 3: mostly clean turn-taking
  - 4: smooth, respectful turn-taking

## Confidence Signals

### Trust - Trust

- Layer: `J`
- Scoring type: `ORD`
- Raw value: whether the listener would trust the candidate based on answer quality and delivery
- Depends on: relevance, specificity, ownership, steadiness, clarity, honesty
- Criteria:
  - 0: difficult to trust/evaluate
  - 1: significant uncertainty about reliability
  - 2: somewhat credible but inconsistent
  - 3: credible and mostly trustworthy
  - 4: strong trust; answers feel clear, grounded, and believable

### Pres - Presence

- Layer: `J`
- Scoring type: `ORD`
- Raw value: whether the candidate sounds like they belong in the room
- Depends on: volume, steadiness, pace control, pause quality, register, ownership
- Criteria:
  - 0: does not sound ready or evaluable
  - 1: very hesitant or difficult to place professionally
  - 2: some presence but inconsistent
  - 3: composed and credible
  - 4: polished, grounded, and interview-ready

### Hold - Pressure Hold

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: stability when question difficulty increases
- Depends on: steadiness, pace control, pause quality, recovery speed
- Criteria:
  - 0: collapses under pressure
  - 1: holds only on familiar topics
  - 2: wobbles but meaning survives
  - 3: holds with minor recoverable dips
  - 4: holds consistently under pressure

### Recv - Recovery Speed

- Layer: `D`
- Scoring type: `ORD`
- Raw value: time/quality of regaining control after disruption
- Depends on: recovery pauses, self-correction, answer continuation
- Criteria:
  - 0: no recovery
  - 1: slow recovery, answer remains weak
  - 2: recovery after visible struggle
  - 3: quick recovery
  - 4: immediate recovery with no listener concern

### Own - Ownership

- Layer: `J`
- Scoring type: `ORD`
- Raw value: active agency and responsibility in answers
- Criteria:
  - 0: passive/deflecting language dominates
  - 1: mostly vague group ownership
  - 2: some personal ownership
  - 3: clear ownership of action/outcome
  - 4: complete ownership with named impact or learning

### Conf - Confidence

- Layer: `C`
- Scoring type: `COMP + ORD`
- Raw value: composite confidence impression
- Depends on: volume, steadiness, pace control, pause quality, pressure hold, recovery, presence
- Criteria:
  - 0: confidence signal prevents evaluation
  - 1: low confidence with frequent breakdowns
  - 2: some confidence but inconsistent
  - 3: mostly confident and stable
  - 4: confident, composed, and pressure-resistant

### Nerv - Nervousness

- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: audible anxiety or nervous behaviors
- Note: higher score means less harmful nervousness
- Depends on: fillers, pace instability, voice tremor, hesitation, pressure hold
- Criteria:
  - 0: nervousness dominates the interview
  - 1: frequent nervous signals
  - 2: noticeable but manageable nervousness
  - 3: minor nervousness
  - 4: calm or nerves are well controlled

## Role Competency

### Imp - Impact

- Layer: `J`
- Scoring type: `ORD`
- Raw value: named or quantified outcome of candidate action
- Criteria:
  - 0: no impact
  - 1: vague impact
  - 2: basic outcome named
  - 3: clear impact
  - 4: quantified or meaningful impact, connected to candidate action

### Lead - Leadership

- Layer: `J`
- Scoring type: `ORD`
- Raw value: initiative, influence, or guidance of others
- Criteria:
  - 0: no leadership evidence
  - 1: claims leadership without example
  - 2: basic initiative shown
  - 3: clear leadership behavior
  - 4: leadership with impact, ownership, or follow-through

### Prof - Maturity

- Layer: `J`
- Scoring type: `ORD`
- Raw value: workplace judgment and professional norms
- Criteria:
  - 0: poor professional judgment
  - 1: immature or unsafe framing
  - 2: basic professional awareness
  - 3: sound professional judgment
  - 4: mature, accountable, and context-aware judgment

### Prob - Problem Solve

- Layer: `J`
- Scoring type: `ORD`
- Raw value: ability to handle ambiguity, constraints, or issues
- Criteria:
  - 0: no problem-solving evidence
  - 1: generic claim only
  - 2: basic problem-solving step
  - 3: clear problem-solving process
  - 4: structured problem solving with impact/learning

### Coll - Collab

- Layer: `J`
- Scoring type: `ORD`
- Raw value: teamwork and collaboration evidence
- Criteria:
  - 0: no collaboration evidence
  - 1: vague teamwork claim
  - 2: basic collaboration described
  - 3: clear teamwork behavior
  - 4: collaboration with specific contribution and outcome

### Learn - Learnability

- Layer: `J`
- Scoring type: `ORD`
- Raw value: ability to improve from feedback, failure, or new information
- Criteria:
  - 0: no learning evidence
  - 1: generic desire to learn
  - 2: basic learning example
  - 3: specific improvement behavior
  - 4: learning translated into changed system/habit/result

### Comp - Competency

- Layer: `C`
- Scoring type: `COMP + ORD`
- Raw value: whether the answer demonstrates behavior needed for the role
- Depends on: relevance, example, action, judgment, impact, role-specific criteria
- Criteria:
  - 0: no role-relevant behavior
  - 1: understands competency but cannot demonstrate it
  - 2: basic competency evidence
  - 3: clear role-relevant behavior
  - 4: strong competency evidence with ownership and impact

## Recording Quality

### Dia - Diarization

- Layer: `M`
- Scoring type: `ORD`
- Raw value: ability to separate speakers accurately
- Criteria:
  - 0: speakers cannot be separated
  - 1: frequent speaker confusion
  - 2: usable but error-prone speaker split
  - 3: mostly accurate speaker split
  - 4: clean speaker separation

### SNR - Signal-To-Noise Ratio

- Layer: `M`
- Scoring type: `RANGE + ORD`
- Raw value: voice signal strength relative to noise floor
- Criteria:
  - 0: noise overwhelms speech
  - 1: poor SNR; many words affected
  - 2: acceptable but noisy
  - 3: good SNR with minor noise
  - 4: clean voice signal

### Drop - Dropouts

- Layer: `M`
- Scoring type: `COUNT + ORD`
- Raw value: missing audio chunks, glitches, or packet loss
- Note: higher score means fewer dropouts
- Criteria:
  - 0: major missing content
  - 1: frequent dropouts
  - 2: some dropouts but usable
  - 3: rare minor dropouts
  - 4: no meaningful dropouts

### Clip - Clipping

- Layer: `M`
- Scoring type: `COUNT + ORD`
- Raw value: distorted peaks from overly loud signal
- Note: higher score means less clipping
- Criteria:
  - 0: clipping regularly makes speech unintelligible
  - 1: frequent clipping
  - 2: occasional clipping
  - 3: rare minor clipping
  - 4: no clipping

### Echo - Echo

- Layer: `M`
- Scoring type: `ORD`
- Raw value: room echo/reverb or call echo
- Note: higher score means less harmful echo
- Criteria:
  - 0: echo makes evaluation difficult
  - 1: strong echo distracts often
  - 2: noticeable echo but usable
  - 3: minor echo
  - 4: clean, dry enough recording

### Mic - Mic Quality

- Layer: `M`
- Scoring type: `ORD`
- Raw value: clarity and fidelity of microphone capture
- Criteria:
  - 0: unusable microphone quality
  - 1: poor quality, many words affected
  - 2: usable but degraded
  - 3: clear enough for scoring
  - 4: clean and reliable capture

### Noi - Noise

- Layer: `M`
- Scoring type: `ORD`
- Raw value: background noise level and intrusiveness
- Note: higher score means less harmful noise
- Criteria:
  - 0: noise prevents evaluation
  - 1: frequent intrusive noise
  - 2: noticeable but manageable noise
  - 3: minor background noise
  - 4: no meaningful noise

## Rubric-Specific Additions Recommended

The current table is a superset of the rubric, but four rubric cards deserve exact visible elements if this table will be used to defend rubric coverage.

### Pwr - Power Words

- Suggested category: Language Quality
- Layer: `J`
- Scoring type: `ORD`
- Raw value: strength, precision, and active quality of word choice
- Criteria:
  - 0: vague/weak words dominate
  - 1: mostly generic words
  - 2: some specific words
  - 3: active and precise word choice
  - 4: strong, precise, emphasis-aware language

### Gap - Working Around Gaps

- Suggested category: Language Quality or Fluency
- Layer: `D + J`
- Scoring type: `ORD`
- Raw value: ability to explain around missing vocabulary without losing meaning
- Criteria:
  - 0: word gaps stop communication
  - 1: gaps cause repeated breakdowns
  - 2: sometimes works around gaps
  - 3: usually explains around missing words
  - 4: gaps are smoothly overcome with circumlocution

### Conn - Connector Words

- Suggested category: Fluency or Answer Structure
- Layer: `M + J`
- Scoring type: `COUNT + ORD`
- Raw value: use of linking words beyond `and`, `but`, `so`
- Criteria:
  - 0: no meaningful connectors
  - 1: mostly `and/then`; ideas feel listed
  - 2: basic connectors like `because`, `but`, `so`
  - 3: varied connectors like `however`, `therefore`, `although`
  - 4: connectors clearly mark logical relationships

### Beyond - Goes Beyond

- Suggested category: Reasoning or Specificity
- Layer: `J`
- Scoring type: `ORD`
- Raw value: lesson, system, follow-up action, or broader principle beyond the direct answer
- Criteria:
  - 0: no beyond-answer value
  - 1: generic add-on only
  - 2: simple lesson or follow-up
  - 3: specific insight/process change
  - 4: memorable broader principle, system, or changed behavior
