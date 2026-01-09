from __future__ import annotations
from enum import Enum
from typing import Optional, Any, Annotated
from datetime import datetime, timedelta
from time import time as timestamp
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo

from pydantic import BaseModel, PositiveInt, BeforeValidator, ValidationError, Field

load_dotenv()

TIME_ZONE = ZoneInfo("America/New_York")


class ReoccurrenceType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ItemSchedule:

    def __init__(self, created: float, start_date: datetime,
                 occurrence_date: datetime,
                 reoccurrence: ReoccurrenceType = ReoccurrenceType.DAILY,
                 end_date: Optional[datetime] = None,
                 scheduled_time: Optional[str] = None,
                 duration_minutes: Optional[PositiveInt] = None) -> None:
        # represents the timestamp when the schedule was originally created
        self.created: float = created
        # the date when the reoccurrence starts
        self.start_date: datetime = start_date
        occur = self._validate_occurrence_date(occurrence_date=occurrence_date)
        self.occurrence_date: datetime = occurrence_date
        # date to stop reoccurrences
        self.end_date: datetime | None = end_date if end_date else None
        self.reoccurrence: ReoccurrenceType = reoccurrence
        # formats: %H:%M:%S %H:%M
        self.at_time: str | None = self._validate_start_time(
            scheduled_time) if scheduled_time else None
        if self.at_time:
            self._insert_occurrence_time()

        self.duration_minutes: PositiveInt | None = self._validate_duration(
            duration_minutes) if duration_minutes else None
        self.now = datetime.now(TIME_ZONE)

    def _validate_time_str(self, time_str: Any) -> tuple[str, datetime]:
        if not isinstance(time_str, str):
            raise ValidationError(f"'{time_str}' is not a string")
        expected_format = os.getenv("TIME_INPUT_FORMATS", "%H:%M:%S")

        time_obj: datetime | None = None

        try:
            time_obj = datetime.strptime(time_str, expected_format)
        except ValueError:
            raise ValidationError(
                f"'{time_str}' does not adhere to the expected format: {expected_format}")

        return (time_str, time_obj)

    def _insert_occurrence_time(self) -> None:
        _, time_obj = self._validate_time_str(self.at_time)
        occurrence_datetime = datetime(
            year=self.occurrence_date.year,
            month=self.occurrence_date.month,
            day=self.occurrence_date.day,
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=time_obj.second,
            tzinfo=TIME_ZONE
        )
        self.occurrence_date = occurrence_datetime

    def _validate_start_time(self, time_str: Any) -> str:

        return_str, time_obj = self._validate_time_str(time_str)
        if time_obj.hour == 0 and time_obj.minute == 0 and time_obj.second == 0:
            raise ValidationError(
                f"Start time cannot be 00:00:00, got: {return_str}")
        if time_obj < self.now:
            raise ValidationError(
                f"Start time {return_str} cannot be in the past, current time is {self.now.time().strftime(os.getenv('TIME_INPUT_FORMATS', '%H:%M:%S'))}")
        return return_str

    def _validate_occurrence_date(self, occurrence_date) -> None:
        if occurrence_date < self.start_date:
            raise ValidationError(
                f"Occurrence date {occurrence_date} cannot be before start date {self.start_date}")
        return occurrence_date

    def _validate_duration(self, duration_minutes: int) -> int:
        if duration_minutes is not None and 1440 >= duration_minutes <= 0:
            raise ValidationError(
                f"Duration must be a positive integer between 1 and 1440 (minutes in a day), got: {duration_minutes}")

        endured = self.occurrence_date + timedelta(minutes=duration_minutes)
        if endured.day != self.occurrence_date.day:
            raise ValidationError(
                f"Duration of {duration_minutes} minutes causes occurrence to extend past midnight, which is not allowed.")
        return duration_minutes
