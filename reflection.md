# PawPal+ Project Reflection

## Three Core User Actions

1. **Tell the app about yourself and your pet** — You type in your name, your pet's name, and what kind of animal it is (dog, cat, or other).
2. **Add the care tasks your pet needs** — You list things like feeding, walking, or giving medicine, and say how long each takes and how important it is.
3. **Ask the app to build a daily schedule** — You press a button and the app sorts everything into a smart plan for the day, starting with the most important tasks.

---

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

I planned the app around four building blocks: **Owner** (stores your name and free time), **Pet** (stores your pet's name and type), **Task** (stores one care job, how long it takes, and how urgent it is), and **Scheduler** (the brain that looks at all tasks and figures out the best order to do them).

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes — after reviewing the code with AI feedback, four issues were found and fixed:

1. **Skipped tasks were silently lost.** The original code had a line that did nothing when a task didn't fit in the schedule. I added a `skipped_tasks` list to `Schedule` so the user can see what got left out and why (e.g. "not enough time remaining").

2. **Two sources of truth for tasks.** The `Scheduler` was receiving both a `Pet` object (which already holds tasks) and a separate `tasks` list. This meant the same data lived in two places, which could cause them to fall out of sync. I removed the separate `tasks` parameter — now the Scheduler always gets tasks from `pet.get_tasks()`.

3. **No check on priority values.** The `Task` class accepted any string as a priority. If someone typed `"HIGH"` or `"urgent"` by mistake, it would silently sort to the very bottom of the schedule. I added a `__post_init__` check that raises a clear error if the priority is not `"low"`, `"medium"`, or `"high"`.

4. **`Task` had an unused `reason` field.** The original design gave `Task` a `reason` field, but `Schedule` already stores explanations separately. Having both was confusing and redundant, so I removed it from `Task`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler looks at **priority** (high-priority tasks like medicine go first), **time** (it only fits tasks that can be done within the available hours), and **pet type** (dogs may need active tasks earlier). Priority mattered most because missing a high-priority task has real consequences for the pet's health.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler always puts high-priority tasks first, even if a low-priority task would take less time and could be done quickly. This makes the day feel packed early on and lighter later but that is reasonable because pet health and safety should never be pushed to the end of the day just to balance the schedule.

**Additional tradeoff — exact time match vs. overlapping duration check**

The `detect_conflicts` method flags two tasks as conflicting only when they share the exact same `HH:MM` start time. It does not check whether their durations overlap (for example, a 30-minute task starting at 08:00 and a 15-minute task starting at 08:20 would overlap in reality, but the scheduler would not catch this).

*Why this is reasonable:* Tasks in PawPal+ do not carry explicit end times — durations are estimated from frequency labels (`daily` = 30 min, `weekly` = 60 min), which are rough approximations rather than precise measurements. Building a full interval-overlap check on top of approximate durations would give a false sense of accuracy. The exact-match check is honest about what the app actually knows: it warns the owner when two tasks are pinned to the same start time, letting the owner decide how to resolve the conflict manually. A future version with user-entered durations could upgrade to interval overlap detection.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI to help brainstorm the class structure at the start and to debug why the schedule button wasn't working. The most helpful prompts were simple and specific — for example: "What information does a Task need to store?" or "Why is my list not saving between button clicks?"

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

The AI once suggested making a very complex scoring system to rank tasks. I decided that was too complicated for what the app needed right now. Instead I tested a simpler rule — sort by priority level — and confirmed it gave sensible results with a few example tasks I made up by hand.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested adding tasks and checking they appear correctly, clicking "Generate Schedule" and verifying the order made sense (high priority first), and adding a task with 0 minutes to see if it caused any errors. These tests mattered because if the app shows wrong information or crashes, a pet owner could miss an important care task.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I feel fairly confident the basic flow works. If I had more time, I would test what happens when someone adds 20+ tasks, or when two tasks have the same priority level — does the app break or just pick one at random?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with how clean and simple the task-adding flow feels. Even someone who has never used an app like this could figure out what to type without any instructions.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I built this again, I would add a way to set a specific time of day for tasks (like "walk at 8am") instead of just ordering them by priority. That would make the schedule feel more like a real calendar.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest thing I learned is that planning the structure of a program on paper first — even just a simple list of what each piece does — saves a lot of confusion later. AI is a great brainstorming partner, but you still need to check its ideas against what actually makes sense for your specific problem.
