"""Demo script for PawPal+.

Creates an owner with two pets, adds several tasks scheduled at different
times, builds today's plan, and prints it to the terminal.
"""

import datetime

from pawpal_system import Owner, Pet, Priority, Scheduler, Task, TimeWindow


def main() -> None:
    # Owner and pets
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "Shiba Inu", 3)
    luna = Pet("Luna", "Tabby Cat", 5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks at different times of day, split across the two pets
    owner.add_task(
        Task(
            "Morning walk",
            "walk",
            mochi,
            duration=30,
            priority=Priority.HIGH,
            preferred_time_window=TimeWindow(
                datetime.time(7, 0), datetime.time(8, 0)
            ),
        )
    )
    owner.add_task(
        Task(
            "Feed Luna",
            "feeding",
            luna,
            duration=10,
            priority=Priority.HIGH,
            preferred_time_window=TimeWindow(
                datetime.time(8, 0), datetime.time(8, 30)
            ),
        )
    )
    owner.add_task(
        Task(
            "Evening play",
            "enrichment",
            luna,
            duration=20,
            priority=Priority.MEDIUM,
            preferred_time_window=TimeWindow(
                datetime.time(18, 0), datetime.time(19, 0)
            ),
        )
    )

    # Build today's plan from the owner's tasks
    scheduler = Scheduler(available_time=120, tasks=owner.tasks)
    agenda = scheduler.generate_plan()

    print("Today's Schedule")
    print("=" * 40)
    agenda.display()
    print()
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
