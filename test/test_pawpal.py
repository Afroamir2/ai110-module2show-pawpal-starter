"""Tests for the PawPal+ domain model."""

import datetime
import os
import sys

# Make the project root importable when running from the test/ directory.
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from pawpal_system import (  # noqa: E402
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    TimeWindow,
)


def _make_task(pet: Pet, completed: bool = False) -> Task:
    return Task(
        name="Morning walk",
        task_type="walk",
        pet=pet,
        duration=30,
        priority=Priority.HIGH,
        preferred_time_window=TimeWindow(
            datetime.time(7, 0), datetime.time(8, 0)
        ),
        completed=completed,
    )


def test_mark_complete_changes_status():
    """Task completion: mark_complete() flips the task's status to done."""
    pet = Pet("Mochi", "Shiba Inu", 3)
    task = _make_task(pet, completed=False)

    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_to_pet_increases_count():
    """Task addition: adding a task to a Pet grows that pet's task count."""
    pet = Pet("Luna", "Tabby Cat", 5)

    assert len(pet.tasks) == 0

    pet.add_task(_make_task(pet))

    assert len(pet.tasks) == 1

    pet.add_task(_make_task(pet))

    assert len(pet.tasks) == 2


def _timed_task(
    name: str,
    pet: Pet,
    start: datetime.time,
    end: datetime.time,
    duration: int = 10,
    priority: Priority = Priority.MEDIUM,
) -> Task:
    return Task(
        name=name,
        task_type="care",
        pet=pet,
        duration=duration,
        priority=priority,
        preferred_time_window=TimeWindow(start, end),
    )


def test_agenda_sorted_chronologically():
    """Sorting: generate_plan returns scheduled tasks in start-time order.

    Tasks are added deliberately out of chronological order (evening, then
    morning, then midday); the resulting agenda must list them earliest
    window first.
    """
    pet = Pet("Mochi", "Shiba Inu", 3)
    evening = _timed_task(
        "Evening play", pet, datetime.time(18, 0), datetime.time(19, 0)
    )
    morning = _timed_task(
        "Morning walk", pet, datetime.time(7, 0), datetime.time(8, 0)
    )
    midday = _timed_task(
        "Midday feed", pet, datetime.time(12, 0), datetime.time(12, 30)
    )

    scheduler = Scheduler(
        available_time=120, tasks=[evening, morning, midday]
    )
    agenda = scheduler.generate_plan()

    names = [t.name for t in agenda.scheduled_tasks]
    assert names == ["Morning walk", "Midday feed", "Evening play"]

    starts = [
        t.preferred_time_window.start for t in agenda.scheduled_tasks
    ]
    assert starts == sorted(starts)


def test_completing_daily_task_enrolls_next_day():
    """Recurrence: completing a daily task auto-creates tomorrow's task.

    The owner should gain a fresh, uncompleted copy of the task whose
    due_date is one day after today.
    """
    owner = Owner("Jordan")
    pet = Pet("Mochi", "Shiba Inu", 3)
    owner.add_pet(pet)

    walk = Task(
        name="Morning walk",
        task_type="walk",
        pet=pet,
        duration=30,
        priority=Priority.HIGH,
        recurrence="daily",
        due_date=datetime.date.today(),
    )
    owner.add_task(walk)

    next_walk = owner.mark_task_complete(walk)

    # A follow-up task was actually produced and enrolled.
    assert next_walk is not None
    assert next_walk is not walk
    assert next_walk in owner.tasks

    # It is a pending copy scheduled for the following day.
    assert next_walk.completed is False
    assert next_walk.recurrence == "daily"
    assert next_walk.name == walk.name
    assert next_walk.due_date == datetime.date.today() + datetime.timedelta(
        days=1
    )


def test_scheduler_flags_overlapping_times():
    """Conflicts: detect_conflicts warns when two scheduled windows overlap.

    Two tasks share the same clock time, so the scheduler must surface
    exactly one conflict warning naming both tasks.
    """
    owner_pet = Pet("Mochi", "Shiba Inu", 3)
    other_pet = Pet("Luna", "Tabby Cat", 5)

    walk = _timed_task(
        "Morning walk", owner_pet, datetime.time(7, 0), datetime.time(8, 0)
    )
    vet_call = _timed_task(
        "Vet phone call", other_pet, datetime.time(7, 30), datetime.time(8, 15)
    )

    scheduler = Scheduler(available_time=120, tasks=[walk, vet_call])
    scheduler.generate_plan()
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "Morning walk" in conflicts[0]
    assert "Vet phone call" in conflicts[0]


def test_touching_windows_do_not_conflict():
    """Conflicts: windows that only touch at an endpoint are not a conflict."""
    pet = Pet("Mochi", "Shiba Inu", 3)
    first = _timed_task(
        "Walk", pet, datetime.time(7, 0), datetime.time(8, 0)
    )
    second = _timed_task(
        "Feed", pet, datetime.time(8, 0), datetime.time(8, 30)
    )

    scheduler = Scheduler(available_time=120, tasks=[first, second])
    scheduler.generate_plan()

    assert scheduler.detect_conflicts() == []
