from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ..reoccurrence import Reoccurrence
from enum import Enum

TIME_ZONE = ZoneInfo("America/New_York")


class TaskStatus(Enum):

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Task:

    def __init__(self, name: str, desc: str,
                 due: Optional[datetime], reoccurrence: Optional[Reoccurrence]) -> None:
        self.name = name
        self.description = desc
        self.due_date: datetime | None = due if due else None
        self.reoccurrence: Reoccurrence | None = reoccurrence if reoccurrence else None
        self.status: TaskStatus = TaskStatus.CREATED
        self.start_time: datetime | None = None
        self.completed_time: datetime | None = None
        self.runtime: timedelta | None = None
        self.cancellation_reason: str | None = None

    def start(self):
        self.start_time = datetime.now(TIME_ZONE)
        self.status = TaskStatus.IN_PROGRESS

    def _calculate_runtime(self):
        if self.start_time and self.completed_time:
            return self.completed_time - self.start_time
        else:
            raise ValueError(
                f"Start or Completed times missing: start({self.start_time}), completed({self.completed_time})")

    def complete(self):
        self.completed_time = datetime.now(TIME_ZONE)
        self.status = TaskStatus.COMPLETED
        self.runtime = self._calculate_runtime()

    def cancel(self, reason: Optional[str]):
        self.status = TaskStatus.CANCELED
        if reason:
            self.cancellation_reason = reason

    # TODO: add create_next method for Tasks that reoccur after finishing Reoccurrence class model; it should be called, if the task is reoccurring, in both the complete and cancel methods
