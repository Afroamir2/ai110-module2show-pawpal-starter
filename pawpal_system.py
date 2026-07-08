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

    def overlaps(self, other: "TimeWindow") -> bool:
        """True if this window and ``other`` share any clock time.

        Uses the standard interval-overlap test ``start1 < end2 and
        start2 < end1``. Windows that merely touch at an endpoint (e.g.
        07:00-08:00 and 08:00-08:30) are treated as non-overlapping.
        """
        return self.start < other.end and other.start < self.end

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
    """A single care activity for a pet, with duration, priority, and status.

    A task may repeat on a schedule via ``recurrence`` ("daily" or "weekly").
    Recurring tasks carry a ``due_date`` so the "next occurrence" lands on a
    real, later day when the task is completed.
    """

    # Recurrence values mapped to how far the next occurrence moves.
    RECURRENCE_STEPS = {
        "daily": datetime.timedelta(days=1),
        "weekly": datetime.timedelta(weeks=1),
    }

    def __init__(
        self,
        name: str,
        task_type: str,
        pet: Pet,
        duration: int,
        priority: Priority,
        preferred_time_window: TimeWindow | None = None,
        completed: bool = False,
        recurrence: str | None = None,
        due_date: datetime.date | None = None,
    ):
        if recurrence is not None:
            recurrence = recurrence.lower()
            if recurrence not in self.RECURRENCE_STEPS:
                raise ValueError(
                    f"recurrence must be one of "
                    f"{sorted(self.RECURRENCE_STEPS)} or None, "
                    f"got {recurrence!r}."
                )

        self.name = name
        self.task_type = task_type
        self.pet = pet
        self.duration = duration
        self.priority = priority
        self.preferred_time_window = preferred_time_window
        self.completed = completed
        self.recurrence = recurrence
        self.due_date = due_date

    def mark_complete(self) -> "Task | None":
        """Mark this task done, spawning the next occurrence if it recurs.

        Returns the newly created follow-up ``Task`` for a recurring task, or
        ``None`` for a one-off task. The caller is responsible for adding the
        returned task to an owner/pet so it enters future plans.
        """
        self.completed = True
        return self._create_next_occurrence()

    def _create_next_occurrence(self) -> "Task | None":
        """Build the follow-up task for a recurring task, or ``None``.

        Returns ``None`` for a one-off task (no ``recurrence``). Otherwise
        returns a fresh, uncompleted copy of this task whose ``due_date`` is
        advanced from today by the recurrence step (``+1 day`` for daily,
        ``+7 days`` for weekly).
        """
        if self.recurrence is None:
            return None

        step = self.RECURRENCE_STEPS[self.recurrence]
        # The next occurrence is measured from *today*, the day the task was
        # completed. timedelta does the calendar arithmetic exactly, rolling
        # over month and year boundaries (e.g. Jul 31 + 1 day -> Aug 1).
        next_due = datetime.date.today() + step

        return Task(
            self.name,
            self.task_type,
            self.pet,
            self.duration,
            self.priority,
            preferred_time_window=self.preferred_time_window,
            completed=False,
            recurrence=self.recurrence,
            due_date=next_due,
        )

    def __repr__(self) -> str:
        return (
            f"Task(name={self.name!r}, type={self.task_type!r}, "
            f"pet={self.pet.name!r}, duration={self.duration}, "
            f"priority={self.priority}, completed={self.completed}, "
            f"recurrence={self.recurrence!r})"
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

    def mark_task_complete(self, task: Task) -> "Task | None":
        """Complete a task and enroll its next occurrence if it recurs.

        Delegates to ``Task.mark_complete`` (which flips ``completed`` and
        builds the follow-up), then adds any returned follow-up back into this
        owner's task list so it shows up in future plans. Returns the newly
        added task, or ``None`` for a one-off task.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks matching the given filters.

        Both filters are optional. A filter left as ``None`` is ignored, so
        passing neither returns every task, and passing both narrows to tasks
        that satisfy *both* conditions (logical AND).

        Args:
            completed: If set, keep only tasks whose ``completed`` flag matches.
            pet_name: If set, keep only tasks whose pet has this name
                (case-insensitive).
        """
        result = self.tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            result = [
                t for t in result if t.pet.name.lower() == pet_name.lower()
            ]
        return result

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

    def _note(self, message: str) -> None:
        """Record one line of plain-language reasoning for the current plan."""
        self._reasoning.append(message)

    @staticmethod
    def _order_key(task: Task):
        """Sort key defining the scheduler's greedy order.

        Returns a tuple sorted ascending, which yields: highest priority
        first (negated so HIGH leads), then shorter tasks (so more fit), then
        the earliest preferred window. Tasks without a window use
        ``datetime.time.max`` so they sort after any timed task.
        """
        window_start = (
            task.preferred_time_window.start
            if task.preferred_time_window is not None
            else datetime.time.max
        )
        return (-int(task.priority), task.duration, window_start)

    def generate_plan(self, date: datetime.date | None = None) -> "DailyAgenda":
        """Greedily fit tasks into the daily time budget for ``date``.

        Sorts the tasks by ``_order_key`` (priority, then duration, then
        window) and walks them once: completed tasks are noted and skipped,
        remaining tasks are scheduled while their ``duration`` fits the leftover
        budget and skipped otherwise. Records a reason for every decision,
        returns the chronologically sorted ``DailyAgenda``, and caches it as
        ``last_agenda``. Runs in O(n log n), dominated by the sort.
        """
        plan_date = date or datetime.date.today()
        agenda = DailyAgenda(plan_date)
        self._reasoning = []
        remaining = self.available_time

        # One pass over the tasks in greedy order. Each task takes exactly one
        # branch: skip if done, schedule if it fits the remaining budget, or
        # skip if it doesn't. Reason strings are pushed via _note so the loop
        # shows the decision, not the formatting.
        for task in sorted(self.tasks, key=self._order_key):
            if task.completed:
                # Noted for the explanation, but it belongs to neither list.
                self._note(f"'{task.name}' excluded: already completed.")
                continue

            if task.duration <= remaining:
                remaining -= task.duration
                agenda.scheduled_tasks.append(task)
                self._note(
                    f"'{task.name}' scheduled: {task.priority} priority, "
                    f"{task.duration} min fits (remaining {remaining} min)."
                )
            else:
                agenda.skipped_tasks.append(task)
                self._note(
                    f"'{task.name}' excluded: needs {task.duration} min but "
                    f"only {remaining} min left in the budget."
                )

        # Present the day in chronological order.
        agenda.sort_by_time()
        self.last_agenda = agenda
        return agenda

    def detect_conflicts(
        self, agenda: "DailyAgenda | None" = None
    ) -> list[str]:
        """Return warnings for scheduled tasks whose windows overlap.

        A lightweight, non-fatal check: it compares every pair of scheduled
        tasks that have a preferred window and collects a human-readable
        warning for each overlap. Tasks without a window can't conflict and
        are ignored. Returns an empty list when the plan is clean (or when no
        plan has been generated yet) — it never raises.
        """
        agenda = agenda if agenda is not None else self.last_agenda
        if agenda is None:
            return []

        timed = [
            t
            for t in agenda.scheduled_tasks
            if t.preferred_time_window is not None
        ]

        warnings: list[str] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                if a.preferred_time_window.overlaps(b.preferred_time_window):
                    who = (
                        f"same pet, {a.pet.name}"
                        if a.pet is b.pet
                        else f"{a.pet.name} & {b.pet.name}"
                    )
                    warnings.append(
                        f"⚠ Conflict: '{a.name}' ({a.preferred_time_window}) "
                        f"overlaps '{b.name}' ({b.preferred_time_window}) "
                        f"[{who}]."
                    )
        return warnings

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
        """Sort scheduled tasks chronologically by preferred start time.

        Uses each window's start rendered as a zero-padded ``"HH:MM"`` string,
        whose lexicographic order matches chronological order
        (``"07:00" < "08:30" < "18:00"``). Tasks without a preferred window
        use the sentinel ``"99:99"`` so they sort to the end.
        """
        self.scheduled_tasks.sort(
            key=lambda t: (
                t.preferred_time_window.start.strftime("%H:%M")
                if t.preferred_time_window is not None
                else "99:99"
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
