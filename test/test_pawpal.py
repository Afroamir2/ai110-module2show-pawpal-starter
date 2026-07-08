"""Tests for the PawPal+ domain model."""

import datetime
import os
import sys

# Make the project root importable when running from the test/ directory.
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from pawpal_system import Pet, Priority, Task, TimeWindow  # noqa: E402


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
