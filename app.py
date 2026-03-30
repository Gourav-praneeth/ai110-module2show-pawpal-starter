import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Your personal pet care scheduling assistant.")

st.divider()

# ---------------------------------------------------------------------------
# Session State — survives reruns so objects are not recreated on every click
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "pets" not in st.session_state:
    st.session_state.pets = {}

if "active_pet" not in st.session_state:
    st.session_state.active_pet = None

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------

st.subheader("Step 1: Owner Info")

owner_name = st.text_input("Your name", value="Jordan")
available_minutes = st.number_input(
    "How many minutes do you have today?", min_value=10, max_value=960, value=120
)

if st.button("Save owner"):
    if st.session_state.owner is None or st.session_state.owner.name != owner_name:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes)
        )
        st.session_state.pets = {}
    else:
        st.session_state.owner.available_minutes = int(available_minutes)

    st.success(f"Owner saved: {st.session_state.owner.name} ({available_minutes} min available today)")

# ---------------------------------------------------------------------------
# Section 2 — Add a Pet
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 2: Add a Pet")

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_priority = st.selectbox("Pet care priority", ["low", "medium", "high"], index=1)

if st.button("Add pet"):
    if st.session_state.owner is None:
        st.warning("Please save your owner info first (Step 1).")
    elif pet_name in st.session_state.pets:
        st.info(f"{pet_name} is already added.")
    else:
        new_pet = Pet(name=pet_name, species=species, priority=pet_priority)
        st.session_state.owner.add_pet(new_pet)
        st.session_state.pets[pet_name] = new_pet
        st.session_state.active_pet = pet_name
        st.success(f"Added {pet_name} ({species}) to {st.session_state.owner.name}'s care list.")

if st.session_state.pets:
    st.markdown("**Pets registered:**")
    for name, pet in st.session_state.pets.items():
        st.markdown(f"- {name} ({pet.species}, {pet.priority} priority) — {len(pet.get_tasks())} task(s)")

# ---------------------------------------------------------------------------
# Section 3 — Add Tasks  (uses scheduler.sort_tasks + filter_by_status preview)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 3: Add Tasks")

if not st.session_state.pets:
    st.info("Add a pet above before adding tasks.")
else:
    selected_pet_name = st.selectbox("Add task to which pet?", list(st.session_state.pets.keys()))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_desc = st.text_input("Description", value="Morning walk")
    with col2:
        task_time = st.text_input("Time", value="08:00")
    with col3:
        frequency = st.selectbox("Frequency", ["daily", "twice daily", "weekly"])
    with col4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        new_task = Task(
            description=task_desc,
            time=task_time,
            frequency=frequency,
            priority=priority
        )
        selected_pet = st.session_state.pets[selected_pet_name]
        selected_pet.add_task(new_task)
        st.success(f"Added '{task_desc}' to {selected_pet_name}'s task list.")

    # Show all tasks sorted chronologically using Scheduler.sort_tasks()
    if st.session_state.owner and st.session_state.owner.get_all_tasks():
        scheduler_preview = Scheduler(owner=st.session_state.owner)

        all_tasks = st.session_state.owner.get_all_tasks()
        sorted_tasks = scheduler_preview.sort_tasks(all_tasks)       # ← sort_tasks()
        pending_tasks = scheduler_preview.filter_by_status(completed=False)  # ← filter_by_status()
        done_tasks = scheduler_preview.filter_by_status(completed=True)

        # Quick stats
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total tasks", len(all_tasks))
        col_b.metric("Pending", len(pending_tasks))
        col_c.metric("Completed", len(done_tasks))

        st.markdown("**All tasks (sorted by time):**")
        st.table([
            {
                "Description": t.description,
                "Time": t.time,
                "Frequency": t.frequency,
                "Priority": t.priority,
                "Done": "✓" if t.completed else "○",
            }
            for t in sorted_tasks
        ])

        # Inline conflict check using detect_conflicts()
        expanded = scheduler_preview.expand_recurring(all_tasks)
        conflicts = scheduler_preview.detect_conflicts(expanded)      # ← detect_conflicts()
        if conflicts:
            for c in conflicts:
                st.warning(f"Time conflict detected: {c}")

# ---------------------------------------------------------------------------
# Section 3b — Weighted Priority Ranking  ← third algorithmic capability
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 3b: Weighted Priority View")
st.caption(
    "Ranks tasks by a composite score: **task priority × 2** + **pet priority** "
    "+ **morning urgency** (+1 if before noon) + **frequency rarity** "
    "(weekly=+2, daily=+1). Higher score = more urgent."
)

if st.session_state.owner and st.session_state.owner.get_all_tasks():
    sched_preview = Scheduler(owner=st.session_state.owner)
    all_tasks_raw = st.session_state.owner.get_all_tasks()
    ranked = sched_preview.rank_by_weight(all_tasks_raw)  # ← rank_by_weight()

    st.markdown("**Tasks ranked by weighted composite score:**")
    st.table([
        {
            "Rank": i,
            "Description": t.description,
            "Time": t.time,
            "Task Priority": t.priority,
            "Frequency": t.frequency,
            "Score": sched_preview.weighted_score(t),  # ← weighted_score()
        }
        for i, t in enumerate(ranked, 1)
    ])
elif st.session_state.pets:
    st.info("Add tasks in Step 3 to see the weighted ranking.")

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 4: Build Today's Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please complete Step 1 first.")
    elif not st.session_state.pets:
        st.warning("Please add at least one pet (Step 2).")
    elif not st.session_state.owner.get_all_pending_tasks():
        st.warning("Please add at least one task (Step 3).")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule = scheduler.schedule_day()

        # ── Conflict warnings ──────────────────────────────────────────────
        if schedule.conflicts:
            for c in schedule.conflicts:
                st.warning(f"⚠️ Time conflict: {c}")
        else:
            st.success(f"Schedule built for {st.session_state.owner.name} — no conflicts detected!")

        # ── Scheduled tasks table ──────────────────────────────────────────
        if schedule.ordered_tasks:
            st.markdown("### Today's Plan")
            st.table([
                {
                    "#": i,
                    "Task": task.description,
                    "Time": task.time,
                    "Frequency": task.frequency,
                    "Priority": task.priority,
                    "Why": reason,
                }
                for i, (task, reason) in enumerate(
                    zip(schedule.ordered_tasks, schedule.explanations), 1
                )
            ])

        # ── Skipped tasks ──────────────────────────────────────────────────
        if schedule.skipped_tasks:
            st.markdown("### Could Not Fit Today")
            st.table([
                {
                    "Task": task.description,
                    "Reason": reason,
                }
                for task, reason in zip(schedule.skipped_tasks, schedule.skipped_reasons)
            ])
