import datetime

import streamlit as st

from pawpal_system import (
    DailyAgenda,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    TimeWindow,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, a pet care planning assistant. Add care tasks for your
pet, give PawPal+ a daily time budget, and it will fit the highest-value tasks
into your day, flag scheduling conflicts, and explain every decision.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** helps a pet owner plan care tasks for their pet(s) based on
constraints like time, priority, and preferred time windows. The scheduling
logic lives in `pawpal_system.py`; this app is its interactive demo.
"""
    )

st.divider()

st.subheader("Owner & Pet")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. These feed directly into the scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

use_window = st.checkbox("Set a preferred time window", value=True)
wcol1, wcol2 = st.columns(2)
with wcol1:
    window_start = st.time_input(
        "Preferred start", value=datetime.time(8, 0), disabled=not use_window
    )
with wcol2:
    window_end = st.time_input(
        "Preferred end", value=datetime.time(8, 30), disabled=not use_window
    )

if st.button("Add task"):
    st.session_state.tasks.append(
        {
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "window_start": window_start if use_window else None,
            "window_end": window_end if use_window else None,
        }
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t["title"],
                "duration (min)": t["duration_minutes"],
                "priority": t["priority"],
                "window": (
                    f"{t['window_start']:%H:%M}-{t['window_end']:%H:%M}"
                    if t["window_start"] is not None
                    else "—"
                ),
            }
            for t in st.session_state.tasks
        ]
    )
    if st.button("Clear tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

available_time = st.number_input(
    "Daily time budget (minutes)",
    min_value=1,
    max_value=1440,
    value=60,
    help="Total minutes PawPal+ can allocate to tasks today.",
)
sort_mode = st.radio(
    "Order the agenda by", ["Time", "Priority"], horizontal=True
)
priority_filter = st.multiselect(
    "Show priorities",
    ["high", "medium", "low"],
    default=["high", "medium", "low"],
    help="Filter which priorities appear in the agenda tables.",
)

_PRIORITY = {
    "low": Priority.LOW,
    "medium": Priority.MEDIUM,
    "high": Priority.HIGH,
}


def build_scheduler() -> Scheduler:
    """Turn the UI's session tasks into domain objects and a Scheduler."""
    owner = Owner(owner_name)
    pet = Pet(pet_name, breed=species, age=0)
    owner.add_pet(pet)

    scheduler = Scheduler(available_time=int(available_time))
    for row in st.session_state.tasks:
        window = None
        if row["window_start"] is not None:
            window = TimeWindow(row["window_start"], row["window_end"])
        task = Task(
            name=row["title"],
            task_type=species,
            pet=pet,
            duration=row["duration_minutes"],
            priority=_PRIORITY[row["priority"]],
            preferred_time_window=window,
        )
        owner.add_task(task)
        pet.add_task(task)
        scheduler.add_task(task)
    return scheduler


def tasks_to_rows(tasks: list[Task]) -> list[dict]:
    """Render a list of tasks as table rows, applying the priority filter."""
    rows = []
    for task in tasks:
        if str(task.priority) not in priority_filter:
            continue
        rows.append(
            {
                "Task": task.name,
                "Pet": task.pet.name,
                "Duration": f"{task.duration} min",
                "Priority": str(task.priority).title(),
                "Window": (
                    str(task.preferred_time_window)
                    if task.preferred_time_window is not None
                    else "—"
                ),
            }
        )
    return rows


if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = build_scheduler()
        agenda: DailyAgenda = scheduler.generate_plan()

        # Order the agenda using the DailyAgenda sort methods.
        if sort_mode == "Priority":
            agenda.sort_by_priority()
        else:
            agenda.sort_by_time()

        used = sum(t.duration for t in agenda.scheduled_tasks)
        st.markdown(f"### Agenda for {agenda.date:%A, %B %d, %Y}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled", len(agenda.scheduled_tasks))
        m2.metric("Skipped", len(agenda.skipped_tasks))
        m3.metric("Budget used", f"{used}/{int(available_time)} min")
        st.progress(min(used / int(available_time), 1.0))

        # Conflict warnings from the scheduler.
        conflicts = scheduler.detect_conflicts(agenda)
        if conflicts:
            for warning in conflicts:
                st.warning(warning)
        else:
            st.success("✅ No scheduling conflicts detected.")

        st.markdown("#### ✅ Scheduled")
        scheduled_rows = tasks_to_rows(agenda.scheduled_tasks)
        if scheduled_rows:
            st.table(scheduled_rows)
        elif agenda.scheduled_tasks:
            st.info("Scheduled tasks are hidden by the current priority filter.")
        else:
            st.info("No tasks fit the daily budget.")

        st.markdown("#### ⏭️ Skipped")
        skipped_rows = tasks_to_rows(agenda.skipped_tasks)
        if skipped_rows:
            st.table(skipped_rows)
        elif agenda.skipped_tasks:
            st.caption("Skipped tasks are hidden by the current priority filter.")
        else:
            st.success("Nothing skipped — every task made the plan.")

        with st.expander("Why this plan?", expanded=True):
            st.text(scheduler.explain_plan())
