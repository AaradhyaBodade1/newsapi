from __future__ import annotations

from dataclasses import dataclass

from better_profanity import profanity

from common.schemas import GeneratedContent

profanity.load_censor_words()


@dataclass
class QualityResult:
    passed: bool
    profanity_flag: bool
    reasons: list[str]


def evaluate(content: GeneratedContent, quality_score_threshold: float) -> QualityResult:
    reasons: list[str] = []

    combined_text = " ".join(
        [content.headline, content.caption, content.summary, content.cta, " ".join(content.hashtags)]
    )
    profanity_flag = profanity.contains_profanity(combined_text)
    if profanity_flag:
        reasons.append("profanity detected")

    if not content.headline or len(content.headline) > 150:
        reasons.append("headline missing or too long")
    if not content.caption or len(content.caption) < 10:
        reasons.append("caption missing or too short")
    if not (1 <= len(content.hashtags) <= 15):
        reasons.append("hashtag count out of range (expected 1-15)")
    if not content.image_prompt:
        reasons.append("image_prompt missing")
    if content.quality_score < quality_score_threshold:
        reasons.append(f"quality_score {content.quality_score} below threshold {quality_score_threshold}")
    if not content.is_india_relevant:
        reasons.append("not relevant to India")

    return QualityResult(passed=not reasons, profanity_flag=profanity_flag, reasons=reasons)
