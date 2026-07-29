from worker.ai.quality_checks import evaluate
from common.schemas import GeneratedContent


def _valid_content(**overrides) -> GeneratedContent:
    base = dict(
        headline="Local team wins championship in dramatic finish",
        caption="What a night for the home crowd! The final score tells only part of the story.",
        summary="The home team won the championship after a close final match.",
        cta="Tap the link in bio for the full recap!",
        hashtags=["sports", "championship", "win"],
        image_prompt="A dynamic editorial illustration of a stadium celebration at night.",
        quality_score=0.85,
    )
    base.update(overrides)
    return GeneratedContent(**base)


def test_good_content_passes():
    result = evaluate(_valid_content(), quality_score_threshold=0.6)
    assert result.passed
    assert not result.profanity_flag


def test_low_quality_score_fails():
    result = evaluate(_valid_content(quality_score=0.2), quality_score_threshold=0.6)
    assert not result.passed
    assert any("quality_score" in r for r in result.reasons)


def test_profanity_is_flagged_and_fails():
    result = evaluate(_valid_content(caption="This is such fucking great news!"), quality_score_threshold=0.6)
    assert result.profanity_flag
    assert not result.passed


def test_not_india_relevant_fails():
    result = evaluate(_valid_content(is_india_relevant=False), quality_score_threshold=0.6)
    assert not result.passed
    assert any("India" in r for r in result.reasons)
