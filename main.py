"""Demo script for PawPal+.

Creates an owner with two pets, adds several tasks *out of chronological
order* (and marks one complete), then demonstrates the filtering and
time-sorting methods before building and printing today's plan.
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

    # Tasks added deliberately OUT of time order (evening first, then a
    # late-morning feed, then the early-morning walk) so the sorting method
    # has real work to do. One task is already completed.
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
            completed=True,
        )
    )
    # Overlaps the 07:00-08:00 morning walk (different pet) to exercise
    # conflict detection.
    owner.add_task(
        Task(
            "Vet phone call",
            "health",
            luna,
            duration=15,
            priority=Priority.HIGH,
            preferred_time_window=TimeWindow(
                datetime.time(7, 30), datetime.time(8, 15)
            ),
        )
    )
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
            recurrence="daily",
            due_date=datetime.date.today(),
        )
    )

    # --- Filtering demo (Owner.filter_tasks) ---------------------------------
    print("Filtering")
    print("=" * 40)
    print("Insertion order:", [t.name for t in owner.tasks])
    print("Pending only:   ", [t.name for t in owner.filter_tasks(completed=False)])
    print("Completed only: ", [t.name for t in owner.filter_tasks(completed=True)])
    print("Luna's tasks:   ", [t.name for t in owner.filter_tasks(pet_name="Luna")])
    print()

    # --- Sorting demo (DailyAgenda.sort_by_time) -----------------------------
    # Build today's plan from only the pending tasks so completed work is
    # not re-scheduled, then let the agenda sort itself chronologically.
    scheduler = Scheduler(
        available_time=120, tasks=owner.filter_tasks(completed=False)
    )
    agenda = scheduler.generate_plan()

    print("Today's Schedule (sorted by time)")
    print("=" * 40)
    agenda.display()
    print()
    print(scheduler.explain_plan())
    print()

    # --- Conflict detection (Scheduler.detect_conflicts) ---------------------
    print("Conflicts")
    print("=" * 40)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(warning)
    else:
        print("No scheduling conflicts detected.")
    print()

    # --- Recurrence demo (Owner.mark_task_complete) --------------------------
    # Completing the daily "Morning walk" should auto-enroll tomorrow's walk.
    print("Recurrence")
    print("=" * 40)
    walk = owner.filter_tasks(pet_name="Mochi")[0]
    print(f"Completing '{walk.name}' (recurrence={walk.recurrence}, "
          f"due {walk.due_date})...")
    next_walk = owner.mark_task_complete(walk)
    print(f"Original now completed: {walk.completed}")
    print(f"Next occurrence auto-added, due: {next_walk.due_date}")
    print("Pending tasks after completion:",
          [t.name for t in owner.filter_tasks(completed=False)])


if __name__ == "__main__":
    main()
