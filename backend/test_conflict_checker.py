from conflict_checker import (
    ExtractedClaim,
    Level1ConflictChecker,
)


def test_detects_potential_conflict():
    claims = [
        ExtractedClaim(
            answer="yes",
            claim="Drug X improves survival.",
            evidence="Drug X significantly improved overall survival.",
            source="Document A",
        ),
        ExtractedClaim(
            answer="no",
            claim="Drug X does not improve survival.",
            evidence="No improvement in overall survival was observed.",
            source="Document B",
        ),
    ]

    result = Level1ConflictChecker().check(claims)

    assert result.status == "Potential conflict"
    assert len(result.claims) == 2
    assert result.claims[0].source == "Document A"
    assert result.claims[1].source == "Document B"