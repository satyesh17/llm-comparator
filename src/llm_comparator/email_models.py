"""Pydantic models for email classification benchmarks.

Used by benchmark_schema.py to test how reliably each provider produces
schema-conforming output on real-world emails (Enron corpus).
"""

from typing import Literal

from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    """Strict-output schema for an LLM-classified email.

    Used to enforce shape on LLM responses — bad responses get rejected
    before they reach downstream code.

    NOTE: This is a copy of email-classifier/src/email_classifier/models.py.
    Both projects are kept self-contained; if the schema changes, update both.
    """

    category: Literal["sales", "support", "billing", "spam", "other"] = Field(
        ...,
        description="The functional category of the email.",
    )

    priority: Literal["low", "medium", "high", "urgent"] = Field(
        ...,
        description="How urgently this email needs attention.",
    )

    action_required: bool = Field(
        ...,
        description="Whether the email requires the recipient to take action.",
    )

    summary: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="A 1-2 sentence summary of the email's content.",
    )


class EmailClassificationLite(BaseModel):
    """Gemini-API-compatible variant without length constraints.
    
    Gemini's native response_schema mode rejects minLength/maxLength fields.
    This lite version is sent to Gemini for shape enforcement; the full
    EmailClassification (with constraints) validates the response afterward.
    """
    
    category: Literal["sales", "support", "billing", "spam", "other"] = Field(
        ..., description="The functional category of the email."
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        ..., description="How urgently this email needs attention."
    )
    action_required: bool = Field(
        ..., description="Whether the email requires the recipient to take action."
    )
    summary: str = Field(
        ..., description="A 1-2 sentence summary of the email's content."
    )

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailClassificationResult:
    """Result of attempting to classify a single email with one provider.
    
    Captures both successes and failures uniformly so batch jobs can continue
    processing when individual classifications fail.
    """
    
    provider: str                        # "ollama", "gemini", "huggingface"
    model: str                           # "llama3.1:8b", "gemini-2.5-flash-lite", etc.
    raw_output: str = ""                 # what the model actually returned (for debugging)
    classification: Optional["EmailClassification"] = None  # parsed + validated, or None
    schema_pass: bool = False            # True if Pydantic validation passed
    latency_ms: float = 0.0
    error: Optional[str] = None          # type + truncated message if anything failed