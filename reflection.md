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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
