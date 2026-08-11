from qualitative_quality import canonical_rating, rating_errors, rating_from_markdown


def _markdown(label="中等偏强", grade="B+", outlook="观察", version="2.0"):
    return f"""## Business Quality Verdict / 商业质量总体评级

**总体评级：{grade} / {label} · {outlook}。**

| 参数 | 值 |
|---|---|
| business_quality_grade | {grade} |
| business_quality_label | {label} |
| rating_outlook | {outlook} |
| rating_version | {version} |
"""


def test_canonical_rating_uses_shared_grade_label_mapping():
    rating = canonical_rating("b+", "观察")
    assert rating.display == "B+ / 中等偏强 · 观察"
    assert rating.version == "2.0"


def test_rating_from_markdown_and_consistency_check():
    assert rating_from_markdown(_markdown()).display == "B+ / 中等偏强 · 观察"
    assert rating_errors(_markdown()) == []


def test_rating_errors_reject_mixed_free_text_scale():
    errors = rating_errors(_markdown(label="较强"))
    assert any("does not match grade" in error for error in errors)
    assert any("first-screen rating" in error for error in errors)
