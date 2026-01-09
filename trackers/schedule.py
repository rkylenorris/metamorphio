from __future__ import annotations
import os
import re

from enum import Enum
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from dataclasses import dataclass
from time import time as timestamp
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Any, Annotated
from pydantic import BaseModel, PositiveInt, BeforeValidator, ValidationError, Field, model_validator

load_dotenv()

TIME_ZONE = ZoneInfo("America/New_York")


class ReoccurrenceType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


def ensure_time_format(time_str: Any) -> str:
    if not isinstance(time_str, str):
        raise ValidationError(f"'{time_str}' is not a string")
    format_matches = re.match(
        f'^([0-1][0-9]|2[0-3]):([0-5][0-9])$', time_str.strip())
    if format_matches is None:
        raise ValidationError(
            f"'{time_str}' does not adhere to the expected format: %H:%M")
    return time_str.strip()


class Schedule(BaseModel):
    # represents the timestamp when the schedule was originally created
    created: float = Field(default_factory=timestamp)
    now: datetime = Field(default_factory=lambda: datetime.now(TIME_ZONE))
    start_date: datetime  # the date when the reoccurrence starts
    reoccurrence: ReoccurrenceType = ReoccurrenceType.DAILY
    # the date of the current occurrence
    occurrence_date: datetime
    end_date: Optional[datetime] = None  # optional date to end reoccurrence
    # formats: %H:%M:%S %H:%M
    at_any_time: bool = Field(default=True)
    at_time: Annotated[Optional[str],
                       BeforeValidator(ensure_time_format)] = None
    duration_minutes: Optional[PositiveInt] = None

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    @model_validator(mode="after")
    def validate_occurrence(self):

        occur_obj: datetime = self.occurrence_date
        if occur_obj < self.start_date:
            raise ValidationError(
                f"Occurrence date {occur_obj} cannot be before start date {self.start_date}")
        if occur_obj < self.now:
            raise ValidationError(
                f"Occurrence date {occur_obj} cannot be in the past")
        if self.end_date and occur_obj > self.end_date:
            raise ValidationError(
                f"Occurrence date {occur_obj} cannot be after end date {self.end_date}")

        if self.at_time:
            try:
                hours, minutes = map(int, self.at_time.split(":"))
                occur_obj = occur_obj.replace(
                    hour=hours, minute=minutes, second=0, microsecond=0)
            except Exception as e:
                raise ValidationError(
                    f"Error parsing at_time '{self.at_time}': {e}")

            self.occurrence_date = occur_obj

        return self

    @model_validator(mode="after")
    def validate_duration(self):
        if self.duration_minutes is not None and (self.duration_minutes not in range(1, 1441)):
            raise ValidationError(
                f"Duration must be a positive integer between 1 and 1440 (minutes in a day), got: {self.duration_minutes}")

        if self.duration_minutes is not None:
            endured = self.occurrence_date + \
                timedelta(minutes=self.duration_minutes)
            if endured.day != self.occurrence_date.day:
                raise ValidationError(
                    f"Duration of {self.duration_minutes} minutes causes occurrence to extend past midnight, which is not allowed.")

        return self
