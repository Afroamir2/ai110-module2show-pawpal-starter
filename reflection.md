# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**Pet**
- Attributes: name, breed, age
- Purpose: holds basic identifying info for the pet; referenced by tasks.

**Task** (generalized — covers walks, feeding, meds, grooming, enrichment)
- Attributes: name, type, pet, duration, priority, preferred time window (optional), completed
- Methods: mark_complete()

**Owner**
- Attributes: name, list of pets, list of tasks
- Methods: add_pet(pet), add_task(task)

**Scheduler**
- Attributes: available_time, list of tasks to consider
- Methods: generate_plan() — orders and fits tasks into available time, breaking ties by priority when tasks compete for time; explain_plan() — returns the reasoning behind what was included, excluded, or reordered

**DailyAgenda**
- Attributes: date, scheduled_tasks, skipped_tasks
- Methods: sort_by_time(), sort_by_priority(), display()

**b. Design changes**

Yes, the design changed once I moved from the UML into a working skeleton and traced how the classes would actually talk to each other.

The most important change was making `Task.priority` a comparable type. In my initial design priority was just a string (`"low"`, `"medium"`, `"high"`), which read fine on paper but broke the moment I looked at `Scheduler.generate_plan()` — it needs to break ties by priority, and strings don't order the way I wanted (`"high" < "low"` alphabetically). I replaced it with a `Priority(IntEnum)` (LOW=1, MEDIUM=2, HIGH=3) so the scheduler can compare and sort priorities directly.

A second change was wiring `Owner` and `Scheduler` together. Originally the `Scheduler` only took `available_time`, so there was no path for the owner's tasks to reach it. I gave `Scheduler` an optional `tasks` list in its constructor so an owner's tasks can be handed in as the source of truth, instead of the scheduler maintaining a disconnected list.

I also made a few smaller cleanups while implementing: I typed the previously-loose "preferred time window" as a `TimeWindow` dataclass, typed `DailyAgenda.date` as `datetime.date`, and renamed `Task.type` to `task_type` so it stops shadowing Python's built-in `type`. These didn't change the structure, but they turned vague UML placeholders into things the scheduling logic can actually operate on.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
My scheduler connsiders all thos contraints listed as examples. But I placed priority as the higher weigth as I figure that would be more realistic.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The biggest tradeoff is that `Scheduler.generate_plan()` treats `available_time`
as a single pool of minutes rather than placing tasks on a real timeline. It
sorts tasks by priority (then shorter duration, then earliest preferred window)
and greedily subtracts each task's `duration` from the remaining budget — so it
only ever answers "do the total minutes fit?" It never assigns concrete start
times, which means it does **not** prevent two tasks from occupying the same
clock time. A 07:00–08:00 walk and a 07:30–08:15 vet call will both be
"scheduled" as long as their combined 45 minutes fits the budget, even though a
single owner physically can't do both at once.

I addressed the symptom rather than the root cause: conflict detection lives in
a separate, advisory `Scheduler.detect_conflicts()` method that runs *after*
planning, compares the scheduled tasks' preferred windows pairwise, and returns
warning strings instead of raising or reshuffling the plan. So overlaps are
surfaced to the owner but not automatically resolved.

This tradeoff is reasonable for the scenario because a pet owner's day has only
a handful of tasks, the plan is a human-facing suggestion rather than a
hard-committed calendar, and the owner is the one who ultimately decides when to
act. A pure minute-budget with an advisory warning keeps `generate_plan()` an
easy-to-reason-about O(n log n) greedy algorithm and avoids the complexity of
true timeline placement (packing tasks into non-overlapping slots, handling
gaps, and shifting windows) — complexity that isn't justified when the human,
not the program, makes the final call. If PawPal+ ever became an
enforce-the-calendar tool, resolving overlaps during scheduling (not just
warning about them) would become worth the added cost.

---

## 3. AI Collaboration

**a. How you used AI**

I mostly used AI as a design partner and a second set of eyes. I'd draft my own
UML and logic first, then have it help me spot where the design would break once
it hit real code, and lean on it for refactoring and wiring the classes into the
Streamlit UI. The most helpful prompts were specific ones — "does this UML still
match my final code?" and "explain how these classes talk to each other" — way
more useful than just asking it to write a class for me.

**b. Judgment and verification**

I didn't take the priority-as-string suggestion as-is. Once I saw the scheduler
had to break ties by priority, strings sorted wrong (`"high" < "low"`
alphabetically), so I switched it to a `Priority(IntEnum)` myself. In general I
verified suggestions by running `main.py` and the pytest suite and checking the
output actually matched what I expected, instead of trusting it looked right.

---

## 4. Testing and Verification

**a. What you tested**

I tested the behaviors most likely to break: `mark_complete()` flipping a task's
status, adding a task growing a pet's list, the agenda coming back in
chronological order, a daily task auto-enrolling the next day's copy, and
`detect_conflicts()` flagging overlapping windows (but not windows that just
touch at an endpoint). These are the core scheduling promises — if any of them
broke, the plan would be wrong or misleading.

**b. Confidence**

Pretty confident on the happy paths — all 6 tests pass and cover the main
behaviors. Not fully confident yet on edge cases. Next I'd test negative or zero
durations, inverted time windows, double-completing a recurring task (duplicate
follow-ups), and computing the next occurrence from `due_date` instead of today.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the scheduler's explanation logic — it doesn't just spit
out a plan, it tells you why each task was scheduled or skipped. That plus the
advisory conflict warnings made it feel like an actual assistant.

**b. What you would improve**

I'd place tasks on a real timeline instead of treating `available_time` as one
pool of minutes, so overlaps get resolved during scheduling instead of just
warned about after.

**c. Key takeaway**

A UML on paper looks fine until the classes have to actually talk to each other
— the design only got real once I traced the data flow in code. And AI is most
useful when I already have an opinion to check against, not as a replacement for
thinking through it myself.
