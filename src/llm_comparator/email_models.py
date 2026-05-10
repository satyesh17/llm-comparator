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