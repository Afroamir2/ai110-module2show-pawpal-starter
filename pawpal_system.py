"""PawPal+ system classes.

Skeleton generated from diagrams/uml.mmd. Attributes and method stubs only —
implement the bodies as you build out the scheduling logic.
"""

from __future__ import annotations


class Pet:
    def __init__(self, name: str, breed: str, age: int):
        self.name = name
        self.breed = breed
        self.age = age


class Task:
    def __init__(
        self,
        name: str,
        type: str,
        pet: Pet,
        duration: int,
        priority: str,
        preferred_time_window=None,
        completed: bool = False,
    ):
        self.name = name
        self.type = type
        self.pet = pet
        self.duration = duration
        self.priority = priority
        self.preferred_time_window = preferred_time_window
        self.completed = completed

    def mark_complete(self) -> None:
        pass


class Owner:
    def __init__(self, name: str):
        self.name = name
        self.pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def add_task(self, task: Task) -> None:
        pass


class Scheduler:
    def __init__(self, available_time: int):
        self.available_time = available_time
        self.tasks: list[Task] = []

    def generate_plan(self) -> "DailyAgenda":
        pass

    def explain_plan(self) -> str:
        pass


class DailyAgenda:
    def __init__(self, date):
        self.date = date
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def sort_by_time(self) -> None:
        pass

    def sort_by_priority(self) -> None:
        pass

    def display(self) -> None:
        pass
