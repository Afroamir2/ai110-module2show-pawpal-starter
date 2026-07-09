# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

PawPal+ implements the following algorithms. The domain model and scheduling
logic live in [`pawpal_system.py`](pawpal_system.py); the interactive UI is in
[`app.py`](app.py); and a runnable command-line demo is in
[`main.py`](main.py).

- **Priority-first budget packing** — `Scheduler.generate_plan()` greedily
  fits tasks into a fixed daily time budget (in minutes), selecting
  highest-priority tasks first and breaking ties toward shorter duration (so
  more tasks fit) then the earliest preferred window. Runs in `O(n log n)`.
- **Sorting by time** — `DailyAgenda.sort_by_time()` orders the agenda
  chronologically by each task's preferred start time (zero-padded `"HH:MM"`
  so string order matches clock order; untimed tasks sort last).
- **Sorting by priority** — `DailyAgenda.sort_by_priority()` reorders the same
  agenda highest-priority-first for a triage view.
- **Conflict warnings** — `Scheduler.detect_conflicts()` (backed by
  `TimeWindow.overlaps()`) flags every pair of scheduled tasks whose preferred
  windows overlap. Advisory only: it never raises or reshuffles the plan, and
  windows that merely touch at an endpoint are not flagged.
- **Task filtering** — `Owner.filter_tasks()` returns tasks by completion
  status and/or pet name (case-insensitive), combining both as a logical AND
  without mutating the underlying list.
- **Daily / weekly recurrence** — completing a recurring task via
  `Owner.mark_task_complete()` auto-enrolls the next occurrence (`+1 day` for
  daily, `+7 days` for weekly, with correct month/year rollover).
- **Plain-language explanations** — `Scheduler.explain_plan()` records and
  returns a reason for every task that was scheduled, skipped, or excluded.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output


```
 Evening play (enrichment, 20 min, medium) @ 18:00-19:00

Plan for 2026-07-07: 3 scheduled, 0 skipped. Used 60/120 min.
- 'Feed Luna' scheduled: high priority, 10 min fits (remaining 110 min).
- 'Morning walk' scheduled: high priority, 30 min fits (remaining 80 min).
- 'Evening play' scheduled: medium priority, 20 min fits (remaining 60 min).
```

## 🧪 Testing PawPal+

Run the tests from the project root with:

```bash
python -m pytest
```

The test suite in [`test/test_pawpal.py`](test/test_pawpal.py) covers the core
domain model (marking a task complete flips its status, and adding a task grows
a pet's task list) plus the three highest-value scheduling behaviors:
tasks are returned in **chronological order**, completing a **daily recurring
task** auto-enrolls a copy due the next day, and the scheduler **flags
overlapping time windows** (while leaving windows that merely touch at an
endpoint alone). Test by test:

| Test | What it verifies |
|------|------------------|
| `test_mark_complete_changes_status` | `mark_complete()` flips a task's `completed` flag |
| `test_adding_task_to_pet_increases_count` | Adding a task grows the pet's task list |
| `test_agenda_sorted_chronologically` | Tasks added out of order are returned earliest-window-first |
| `test_completing_daily_task_enrolls_next_day` | Completing a daily task auto-enrolls a pending copy due the next day |
| `test_scheduler_flags_overlapping_times` | `detect_conflicts()` flags two tasks whose windows overlap |
| `test_touching_windows_do_not_conflict` | Windows that only touch at an endpoint are **not** flagged |

Other useful variations:

```bash
# Run verbosely (one line per test):
python -m pytest -v

# Run with coverage:
python -m pytest --cov
```

Sample test output:

```
plugins: anyio-4.2.0
collected 6 items

test/test_pawpal.py ......                                                                                        [100%]

=================================================== 6 passed in 0.01s ===================================================
```

### Confidence Level: ⭐⭐⭐⭐☆ (4 / 5)

All 6 tests pass, and they exercise the behaviors most likely to break:
chronological ordering, daily recurrence, and conflict detection (including the
endpoint-touching boundary case). That's solid coverage of the happy paths.

It is **not** yet 5 stars because the suite doesn't cover known edge cases that
the current code handles ambiguously — the next occurrence being computed from
`today()` rather than the task's `due_date`, double-completion spawning
duplicate follow-ups, non-positive or negative task durations, inverted time
windows, and budget-exhaustion skip logic. Adding tests (and guards) for those
would raise confidence to 5.

## 📐 Smarter Scheduling

Beyond fitting tasks into a time budget, PawPal+ adds four scheduling features.
Each is summarized below and documented in detail after the table.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `DailyAgenda.sort_by_time()`, `Scheduler._order_key()` | Chronological display order; priority/duration/window selection order |
| Filtering | `Owner.filter_tasks()` | By pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()`, `TimeWindow.overlaps()` | Advisory warnings for overlapping time windows |
| Recurring tasks | `Task.mark_complete()`, `Owner.mark_task_complete()` | Daily/weekly auto-enrollment of the next occurrence |

### Sorting behavior — `DailyAgenda.sort_by_time()`

After a plan is built, the agenda is displayed in chronological order.
`sort_by_time()` sorts the scheduled tasks by each task's preferred start time
rendered as a zero-padded `"HH:MM"` string; because that format is
zero-padded, lexicographic string order matches clock order
(`"07:00" < "08:30" < "18:00"`). Tasks with no preferred window use the
sentinel `"99:99"` so they sort to the end.

A separate **selection** order is defined by `Scheduler._order_key()`, the sort
key used inside `generate_plan()`: highest priority first, then shorter
duration (so more tasks fit), then earliest window. Sorting *what to schedule*
and *how to display it* are intentionally two different orders.

### Filtering behavior — `Owner.filter_tasks(completed=None, pet_name=None)`

Returns the subset of the owner's tasks matching the given filters. Both
arguments are optional and default to `None` (ignore that filter), so:

- `filter_tasks()` → every task
- `filter_tasks(completed=False)` → the pending to-do list
- `filter_tasks(completed=True)` → finished tasks
- `filter_tasks(pet_name="Luna")` → everything for Luna (case-insensitive)
- `filter_tasks(pet_name="Luna", completed=True)` → both filters combine (logical AND)

The method builds and returns a new list; it never mutates `Owner.tasks`.

### Conflict detection — `Scheduler.detect_conflicts()`

A lightweight, **non-fatal** check that runs after planning. It compares every
pair of scheduled tasks that have a preferred window and returns a list of
warning strings for any overlap — it never raises and never reshuffles the
plan. The overlap test itself lives in `TimeWindow.overlaps()`, using the
standard interval rule `start1 < end2 and start2 < end1`, so windows that only
touch at an endpoint (e.g. `07:00-08:00` and `08:00-08:30`) are *not* treated
as conflicts. Warnings distinguish a same-pet clash from two different pets,
since a solo owner can only be in one place at a time. An empty list means the
plan is clean (or no plan has been generated yet).

### Recurring task logic — `Task.mark_complete()` / `Owner.mark_task_complete()`

A task may repeat via `recurrence="daily"` or `"weekly"` (validated at
construction). When a recurring task is completed, `Task.mark_complete()` flips
its `completed` flag and returns a fresh, uncompleted copy for the next
occurrence, built by `Task._create_next_occurrence()`. The new `due_date` is
computed from **today** using `datetime.timedelta` — `+1 day` for daily, `+7
days` for weekly — which handles month/year rollover correctly (e.g.
`Jul 31 → Aug 1`). A one-off task (no recurrence) returns `None`.

`Owner.mark_task_complete(task)` is the convenience wrapper: it calls
`mark_complete()` and automatically adds any returned follow-up back into the
owner's task list, so the next occurrence shows up in future plans without any
manual bookkeeping.

## 📸 Demo Walkthrough

### Main UI features

Launch the interactive app with `streamlit run app.py`. The page is organized
top-to-bottom into the actions a user performs:

- **Owner & Pet** — enter the owner name, pet name, and species.
- **Tasks** — for each task, set a title, duration (minutes), and priority
  (low / medium / high), and optionally a preferred time window (start/end).
  **Add task** appends it to a running table; **Clear tasks** empties the list.
- **Build Schedule** — set the **daily time budget** (minutes), choose whether
  to order the agenda by **Time** or **Priority**, and filter which
  **priorities** are shown. **Generate schedule** runs the scheduler and
  renders the results.
- **Results** — KPI metrics (scheduled / skipped / budget used) and a progress
  bar, conflict warnings (`st.warning`) or a clean-plan confirmation
  (`st.success`), a **Scheduled** table and a **Skipped** table, and a
  **"Why this plan?"** panel with the scheduler's reasoning.

### Example workflow

1. Enter the owner (**Jordan**) and pet (**Mochi**, a dog).
2. Add a task: **Morning walk**, 30 min, high priority, window 07:00–08:00.
3. Add another: **Evening play**, 20 min, medium priority, window 18:00–19:00.
4. Set the daily budget to **120 min** and leave sorting on **Time**.
5. Click **Generate schedule** to view today's plan — tasks appear in
   chronological order with a reason for each.

### Key Scheduler behaviors shown

- **Sorting by time** — tasks added out of order are displayed earliest-first.
- **Conflict warnings** — overlapping windows (e.g. a 07:00–08:00 walk and a
  07:30–08:15 vet call) surface an advisory ⚠ warning without changing the plan.
- **Budget packing & explanations** — higher-priority tasks are packed first
  until the budget runs out, and each decision is explained in plain language.
- **Recurrence** — completing a daily task auto-enrolls tomorrow's copy.

### Sample CLI output

The same logic can be exercised without the UI by running the demo script:

```bash
python main.py
```

```
Filtering
========================================
Insertion order: ['Evening play', 'Feed Luna', 'Vet phone call', 'Morning walk']
Pending only:    ['Evening play', 'Vet phone call', 'Morning walk']
Completed only:  ['Feed Luna']
Luna's tasks:    ['Evening play', 'Feed Luna', 'Vet phone call']

Today's Schedule (sorted by time)
========================================
=== Daily Agenda for 2026-07-08 ===
Scheduled:
  • Morning walk (walk, 30 min, high) @ 07:00-08:00
  • Vet phone call (health, 15 min, high) @ 07:30-08:15
  • Evening play (enrichment, 20 min, medium) @ 18:00-19:00

Plan for 2026-07-08: 3 scheduled, 0 skipped. Used 65/120 min.
- 'Vet phone call' scheduled: high priority, 15 min fits (remaining 105 min).
- 'Morning walk' scheduled: high priority, 30 min fits (remaining 75 min).
- 'Evening play' scheduled: medium priority, 20 min fits (remaining 55 min).

Conflicts
========================================
⚠ Conflict: 'Morning walk' (07:00-08:00) overlaps 'Vet phone call' (07:30-08:15) [Mochi & Luna].

Recurrence
========================================
Completing 'Morning walk' (recurrence=daily, due 2026-07-08)...
Original now completed: True
Next occurrence auto-added, due: 2026-07-09
Pending tasks after completion: ['Evening play', 'Vet phone call', 'Morning walk']
```
