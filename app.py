import pandas as pd
import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
PRIORITY_BG    = {"high": "#ffe5e5",  "medium": "#fff8dc",   "low": "#e5f7e5"}
SPECIES_EMOJI  = {"dog": "🐕", "cat": "🐈"}
FREQ_EMOJI     = {"daily": "📅", "twice daily": "🔁", "weekly": "🗓️"}

# Keywords → task-type emoji (checked in order; first match wins)
_TASK_KEYWORDS = [
    (["walk", "run", "exercise", "jog"],           "🦮"),
    (["feed", "food", "meal", "breakfast",
      "dinner", "lunch", "snack"],                 "🍽️"),
    (["medicine", "med", "pill", "flea",
      "vaccine", "shot", "dose"],                  "💊"),
    (["groom", "brush", "bath", "wash", "trim"],   "✂️"),
    (["litter", "clean", "scoop"],                 "🧹"),
    (["play", "enrich", "toy", "game"],            "🎾"),
    (["vet", "checkup", "appointment"],            "🏥"),
    (["train", "practice", "obedience"],           "🎓"),
]

def _task_emoji(description: str) -> str:
    lower = description.lower()
    for keywords, emoji in _TASK_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return emoji
    return "📋"

def _p(priority: str) -> str:
    return PRIORITY_EMOJI.get(priority, priority)

def _species(species: str) -> str:
    return SPECIES_EMOJI.get(species, "🐾")

def _freq(frequency: str) -> str:
    icon = FREQ_EMOJI.get(frequency, "")
    return f"{icon} {frequency.title()}" if icon else frequency.title()

def _status(completed: bool) -> str:
    return "✅ Done" if completed else "⏳ Pending"

def _styled_task_df(rows: list[dict]) -> None:
    """Render a pandas DataFrame with priority-colored row backgrounds."""
    df = pd.DataFrame(rows)
    raw_priorities = [r["_priority"] for r in rows]
    df = df.drop(columns=["_priority"])

    def color_rows(row):
        idx = row.name
        bg = PRIORITY_BG.get(raw_priorities[idx], "")
        return [f"background-color: {bg}" for _ in row]

    styled = df.style.apply(color_rows, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Your personal pet care scheduling assistant.")

st.divider()

# ---------------------------------------------------------------------------
# Session State
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

st.subheader("👤 Step 1: Owner Info")

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
st.subheader("🐾 Step 2: Add a Pet")

pet_name     = st.text_input("Pet name", value="Mochi")
species      = st.selectbox("Species", ["dog", "cat", "other"])
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
        st.success(f"Added {_species(species)} {pet_name} ({species}) to {st.session_state.owner.name}'s care list.")

# Pet cards — species emoji + task count chip
if st.session_state.pets:
    st.markdown("**Registered pets:**")
    cols = st.columns(len(st.session_state.pets))
    for col, (name, pet) in zip(cols, st.session_state.pets.items()):
        pending = len(pet.get_pending_tasks())
        total   = len(pet.get_tasks())
        col.metric(
            label=f"{_species(pet.species)} {name}",
            value=f"{pending} pending",
            delta=f"{total} total task(s)",
            delta_color="off",
        )

# ---------------------------------------------------------------------------
# Section 3 — Add Tasks
# ---------------------------------------------------------------------------

st.divider()
st.subheader("📝 Step 3: Add Tasks")

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
            priority=priority,
        )
        selected_pet = st.session_state.pets[selected_pet_name]
        selected_pet.add_task(new_task)
        st.success(f"{_task_emoji(task_desc)} Added '{task_desc}' to {selected_pet_name}'s task list.")

    if st.session_state.owner and st.session_state.owner.get_all_tasks():
        scheduler_preview = Scheduler(owner=st.session_state.owner)

        all_tasks    = st.session_state.owner.get_all_tasks()
        sorted_tasks = scheduler_preview.sort_by_priority(all_tasks)   # ← priority first, then time
        pending_tasks = scheduler_preview.filter_by_status(completed=False)
        done_tasks    = scheduler_preview.filter_by_status(completed=True)

        # Quick stats
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total tasks", len(all_tasks))
        col_b.metric("⏳ Pending",  len(pending_tasks))
        col_c.metric("✅ Completed", len(done_tasks))

        st.markdown("**All tasks — sorted by priority, then time:**")
        _styled_task_df([
            {
                "":            _task_emoji(t.description),
                "Description": t.description,
                "Time":        t.time,
                "Frequency":   _freq(t.frequency),
                "Priority":    _p(t.priority),
                "Status":      _status(t.completed),
                "_priority":   t.priority,   # hidden column used for row coloring
            }
            for t in sorted_tasks
        ])

        # Conflict warnings
        expanded  = scheduler_preview.expand_recurring(all_tasks)
        conflicts = scheduler_preview.detect_conflicts(expanded)
        if conflicts:
            for c in conflicts:
                st.warning(f"⚠️ Time conflict detected: {c}")

# ---------------------------------------------------------------------------
# Section 3b — Weighted Priority Ranking
# ---------------------------------------------------------------------------

st.divider()
st.subheader("⚖️ Step 3b: Weighted Priority View")
st.caption(
    "Ranks tasks by a composite score: **task priority × 2** + **pet priority** "
    "+ **morning urgency** (+1 if before noon) + **frequency rarity** "
    "(weekly=+2, daily=+1). Higher score = more urgent."
)

if st.session_state.owner and st.session_state.owner.get_all_tasks():
    sched_preview  = Scheduler(owner=st.session_state.owner)
    all_tasks_raw  = st.session_state.owner.get_all_tasks()
    ranked         = sched_preview.rank_by_weight(all_tasks_raw)   # ← rank_by_weight()

    st.markdown("**Tasks ranked by weighted composite score:**")
    _styled_task_df([
        {
            "Rank":          i,
            "":              _task_emoji(t.description),
            "Description":   t.description,
            "Time":          t.time,
            "Task Priority": _p(t.priority),
            "Frequency":     _freq(t.frequency),
            "Score":         sched_preview.weighted_score(t),
            "_priority":     t.priority,
        }
        for i, t in enumerate(ranked, 1)
    ])
elif st.session_state.pets:
    st.info("Add tasks in Step 3 to see the weighted ranking.")

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("📅 Step 4: Build Today's Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please complete Step 1 first.")
    elif not st.session_state.pets:
        st.warning("Please add at least one pet (Step 2).")
    elif not st.session_state.owner.get_all_pending_tasks():
        st.warning("Please add at least one task (Step 3).")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule  = scheduler.schedule_day()

        # ── Conflict warnings ──────────────────────────────────────────────
        if schedule.conflicts:
            for c in schedule.conflicts:
                st.warning(f"⚠️ Time conflict: {c}")
        else:
            st.success(f"✅ Schedule built for {st.session_state.owner.name} — no conflicts detected!")

        # ── Time-budget progress bar ───────────────────────────────────────
        total_avail  = st.session_state.owner.available_minutes
        minutes_used = sum(
            30 if t.frequency == "daily" else 15 if t.frequency == "twice daily" else 60
            for t in schedule.ordered_tasks
        )
        pct = min(minutes_used / total_avail, 1.0) if total_avail > 0 else 0
        st.markdown(f"**⏱️ Time budget:** {minutes_used} / {total_avail} min used")
        st.progress(pct)

        # ── Scheduled tasks table ──────────────────────────────────────────
        if schedule.ordered_tasks:
            st.markdown("### 🗓️ Today's Plan")
            _styled_task_df([
                {
                    "#":         i,
                    "":          _task_emoji(task.description),
                    "Task":      task.description,
                    "Time":      task.time,
                    "Frequency": _freq(task.frequency),
                    "Priority":  _p(task.priority),
                    "Why":       reason,
                    "_priority": task.priority,
                }
                for i, (task, reason) in enumerate(
                    zip(schedule.ordered_tasks, schedule.explanations), 1
                )
            ])

        # ── Skipped tasks ──────────────────────────────────────────────────
        if schedule.skipped_tasks:
            st.markdown("### ⏭️ Could Not Fit Today")
            st.dataframe(
                pd.DataFrame([
                    {
                        "":       _task_emoji(task.description),
                        "Task":   task.description,
                        "Reason": reason,
                    }
                    for task, reason in zip(schedule.skipped_tasks, schedule.skipped_reasons)
                ]),
                use_container_width=True,
                hide_index=True,
            )
