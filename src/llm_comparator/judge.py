"""LLM-as-judge implementation using Gemini for output scoring."""

import json
import os
from dataclasses import dataclass

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


RUBRIC = """You are an expert judge evaluating responses to user questions.

Score the candidate response from 0 to 10 across these dimensions:
- ACCURACY (max 5 pts): Are the facts correct? Penalize hallucinations.
- COMPLETENESS (max 3 pts): Does it fully answer the question?
- CLARITY (max 2 pts): Is the language clear, precise, and well-written?

The final score is the sum of all three (max 10).

ORIGINAL QUESTION:
{prompt}

CANDIDATE RESPONSE:
{answer}

Be strict and consistent. Return your score and a brief (1-2 sentence) reasoning."""


@dataclass
class JudgeResult:
    """Result from the judge: score, reasoning, optional error."""
    score: float
    reasoning: str
    error: str | None = None


class Judge:
    """LLM-as-judge using Gemini 2.5 Flash to score responses."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found.")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def score(self, prompt: str, answer: str) -> JudgeResult:
        """Score a candidate answer against the original prompt."""
        if not answer.strip():
            return JudgeResult(
                score=0.0,
                reasoning="Empty response — nothing to evaluate.",
            )

        try:
            judge_prompt = RUBRIC.format(prompt=prompt, answer=answer)
            response = self._model.generate_content(
                judge_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "number"},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["score", "reasoning"],
                    },
                },
            )
            parsed = json.loads(response.text)
            return JudgeResult(
                score=float(parsed["score"]),
                reasoning=parsed["reasoning"],
            )
        except Exception as e:
            return JudgeResult(
                score=0.0,
                reasoning="",
                error=f"Judge failed: {e}",
            )