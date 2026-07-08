"""PawPal+ system classes.

Implements the domain model and scheduling logic described in reflection.md:
an Owner collects Pets and Tasks; a Scheduler fits the highest-value tasks into
a fixed daily time budget (breaking ties by priority) and produces a
DailyAgenda that can be sorted and displayed, along with a plain-language
explanation of what was included, excluded, or reordered.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import IntEnum


class Priority(IntEnum):
    """Comparable priority so the scheduler can break ties with < / >."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def __str__(self) -> str:
        return self.name.lower()


@dataclass
class TimeWindow:
    """A preferred window a task should ideally be scheduled within."""

    start: datetime.time
    end: datetime.time

    def __str__(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M}"


class Pet:
    """A pet with basic identifying info and the tasks assigned to it."""

    def __init__(self, name: str, breed: str, age: int):
        self.name = name
        self.breed = breed
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def __repr__(self) -> str:
        return (
            f"Pet(name={self.name!r}, breed={self.breed!r}, "
            f"age={self.age}, tasks={len(self.tasks)})"
        )


class Task:
    """A single care activity for a pet, with duration, priority, and status."""

    def __init__(
        self,
        name: str,
        task_type: str,
        pet: Pet,
        duration: int,
        priority: Priority,
        preferred_time_window: TimeWindow | None = None,
        completed: bool = False,
    ):
        self.name = name
        self.task_type = task_type
        self.pet = pet
        self.duration = duration
        self.priority = priority
        self.preferred_time_window = preferred_time_window
        self.completed = completed

    def mark_complete(self) -> None:
        self.completed = True

    def __repr__(self) -> str:
        return (
            f"Task(name={self.name!r}, type={self.task_type!r}, "
            f"pet={self.pet.name!r}, duration={self.duration}, "
            f"priority={self.priority}, completed={self.completed})"
        )


class Owner:
    """A pet owner that keeps track of their pets and care tasks."""

    def __init__(self, name: str):
        self.name = name
        self.pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_pet(self, pet: Pet) -> None:
        if pet not in self.pets:
            self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def __repr__(self) -> str:
        return (
            f"Owner(name={self.name!r}, pets={len(self.pets)}, "
            f"tasks={len(self.tasks)})"
        )


class Scheduler:
    """Fits tasks into a fixed daily time budget, favoring higher priority.

    ``available_time`` is a budget in minutes for the day. ``generate_plan``
    greedily selects tasks in priority order (breaking ties toward shorter
    tasks so more can fit, then toward earlier preferred windows) until the
    budget is exhausted, recording a reason for every decision.
    """

    def __init__(self, available_time: int, tasks: list[Task] | None = None):
        self.available_time = available_time
        self.tasks: list[Task] = tasks if tasks is not None else []
        self.last_agenda: DailyAgenda | None = None
        self._reasoning: list[str] = []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    @staticmethod
    def _order_key(task: Task):
        # Highest priority first; then shorter tasks; then earliest window.
        window_start = (
            task.preferred_time_window.start
            if task.preferred_time_window is not None
            else datetime.time.max
        )
        return (-int(task.priority), task.duration, window_start)

    def generate_plan(self, date: datetime.date | None = None) -> "DailyAgenda":
        plan_date = date or datetime.date.today()
        agenda = DailyAgenda(plan_date)
        self._reasoning = []

        pending = [t for t in self.tasks if not t.completed]
        skipped_done = [t for t in self.tasks if t.completed]
        for task in skipped_done:
            self._reasoning.append(
                f"'{task.name}' excluded: already completed."
            )

        ordered = sorted(pending, key=self._order_key)
        remaining = self.available_time

        for task in ordered:
            if task.duration <= remaining:
                agenda.scheduled_tasks.append(task)
                remaining -= task.duration
                self._reasoning.append(
                    f"'{task.name}' scheduled: {task.priority} priority, "
                    f"{task.duration} min fits (remaining {remaining} min)."
                )
            else:
                agenda.skipped_tasks.append(task)
                self._reasoning.append(
                    f"'{task.name}' excluded: needs {task.duration} min but "
                    f"only {remaining} min left in the budget."
                )

        # Present the day in chronological order.
        agenda.sort_by_time()
        self.last_agenda = agenda
        return agenda

    def explain_plan(self) -> str:
        if self.last_agenda is None:
            return "No plan generated yet. Call generate_plan() first."

        used = sum(t.duration for t in self.last_agenda.scheduled_tasks)
        header = (
            f"Plan for {self.last_agenda.date:%Y-%m-%d}: "
            f"{len(self.last_agenda.scheduled_tasks)} scheduled, "
            f"{len(self.last_agenda.skipped_tasks)} skipped. "
            f"Used {used}/{self.available_time} min."
        )
        return "\n".join([header, *(f"- {line}" for line in self._reasoning)])


class DailyAgenda:
    """A day's plan holding the scheduled and skipped tasks for a date."""

    def __init__(self, date: datetime.date):
        self.date = date
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def sort_by_time(self) -> None:
        # Tasks without a preferred window sort to the end.
        self.scheduled_tasks.sort(
            key=lambda t: (
                t.preferred_time_window is None,
                t.preferred_time_window.start
                if t.preferred_time_window is not None
                else datetime.time.max,
            )
        )

    def sort_by_priority(self) -> None:
        self.scheduled_tasks.sort(key=lambda t: -int(t.priority))

    def display(self) -> None:
        print(f"=== Daily Agenda for {self.date:%Y-%m-%d} ===")
        if self.scheduled_tasks:
            print("Scheduled:")
            for task in self.scheduled_tasks:
                window = (
                    f" @ {task.preferred_time_window}"
                    if task.preferred_time_window is not None
                    else ""
                )
                print(
                    f"  • {task.name} ({task.task_type}, {task.duration} min, "
                    f"{task.priority}){window}"
                )
        else:
            print("Scheduled: (none)")

        if self.skipped_tasks:
            print("Skipped:")
            for task in self.skipped_tasks:
                print(
                    f"  • {task.name} ({task.duration} min, {task.priority})"
                )
