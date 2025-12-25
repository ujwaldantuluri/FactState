import pytest
from app.services.scoring import to_badge

@pytest.mark.parametrize("score,expected", [
    (0, "✅ Trusted"),
    (39.9, "✅ Trusted"),
    (40.0, "⚠️ Caution"),
    (69.9, "⚠️ Caution"),
    (70.0, "❌ High Risk"),
    (99.0, "❌ High Risk"),
])
def test_badge_ranges(score, expected):
    assert to_badge(score) == expected
