from typing import Literal
from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    text: str
    source: str


class ExtractedClaim(BaseModel):
    answer: Literal["yes", "no", "unclear"]
    claim: str
    evidence: str
    source: str


class ConflictResult(BaseModel):
    status: Literal[
        "Consistent",
        "Potential conflict",
        "Insufficient evidence",
    ]
    explanation: str
    claims: list[ExtractedClaim]

class Level1ConflictChecker:
    """
    Level 1 assumes all retrieved chunks address the same question.

    Conflict rule:
    - At least one "yes" and one "no" -> Potential conflict
    - At least two usable claims with the same answer -> Consistent
    - Fewer than two usable claims -> Insufficient evidence
    """

    def check(self, claims: list[ExtractedClaim]) -> ConflictResult:
        usable_claims = [
            claim for claim in claims
            if claim.answer in {"yes", "no"}
        ]

        if len(usable_claims) < 2:
            return ConflictResult(
                status="Insufficient evidence",
                explanation=(
                    "Fewer than two retrieved sources provide a clear "
                    "answer to the question."
                ),
                claims=claims,
            )

        answers = {claim.answer for claim in usable_claims}

        if answers == {"yes", "no"}:
            return ConflictResult(
                status="Potential conflict",
                explanation=(
                    "At least one source supports the conclusion, while "
                    "another source gives the opposite conclusion."
                ),
                claims=claims,
            )

        return ConflictResult(
            status="Consistent",
            explanation=(
                "The retrieved sources that provide a clear answer "
                "reach the same conclusion."
            ),
            claims=claims,
        )
    
import json
from collections.abc import Callable


def extract_claim(
    question: str,
    chunk: RetrievedChunk,
    llm_generate: Callable[[str], str],
) -> ExtractedClaim:
    prompt = f"""
You are analyzing evidence retrieved by a RAG system.

Question:
{question}

Source text:
{chunk.text}

Determine whether the source answers the question positively,
negatively, or does not provide enough information.

Return JSON only:

{{
  "answer": "yes" | "no" | "unclear",
  "claim": "A concise summary of the source's conclusion",
  "evidence": "The exact sentence or shortest relevant passage"
}}

Rules:
- Use "yes" when the source supports the proposition in the question.
- Use "no" when the source rejects or contradicts the proposition.
- Use "unclear" when the source does not clearly answer it.
- Do not use outside knowledge.
"""

    raw_response = llm_generate(prompt)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON: {raw_response}"
        ) from exc

    answer = data.get("answer", "unclear")

    if answer not in {"yes", "no", "unclear"}:
        answer = "unclear"

    return ExtractedClaim(
        answer=answer,
        claim=data.get("claim", ""),
        evidence=data.get("evidence", chunk.text),
        source=chunk.source,
    )

def analyze_retrieved_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    llm_generate: Callable[[str], str],
) -> ConflictResult:
    claims = [
        extract_claim(
            question=question,
            chunk=chunk,
            llm_generate=llm_generate,
        )
        for chunk in chunks
    ]

    checker = Level1ConflictChecker()
    return checker.check(claims)