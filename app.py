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
    st.session_state.owner = None       # Owner object, created when user saves their info

if "pets" not in st.session_state:
    st.session_state.pets = {}          # dict of pet_name → Pet object (supports multiple pets)

if "active_pet" not in st.session_state:
    st.session_state.active_pet = None  # which pet tasks are currently being added to

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------

st.subheader("Step 1: Owner Info")

owner_name = st.text_input("Your name", value="Jordan")
available_minutes = st.number_input(
    "How many minutes do you have today?", min_value=10, max_value=960, value=120
)

if st.button("Save owner"):
    # Call Owner() — creates a new Owner or updates available time if name changed
    if st.session_state.owner is None or st.session_state.owner.name != owner_name:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes)
        )
        st.session_state.pets = {}   # reset pets when owner changes
    else:
        # Owner already exists — just update available time
        st.session_state.owner.available_minutes = int(available_minutes)

    st.success(f"Owner saved: {st.session_state.owner.name} ({available_minutes} min available today)")

# ---------------------------------------------------------------------------
# Section 2 — Add a Pet  →  calls owner.add_pet()
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
        # Create a Pet object and register it with the Owner using add_pet()
        new_pet = Pet(name=pet_name, species=species, priority=pet_priority)
        st.session_state.owner.add_pet(new_pet)             # ← calls owner.add_pet()
        st.session_state.pets[pet_name] = new_pet
        st.session_state.active_pet = pet_name
        st.success(f"Added {pet_name} ({species}) to {st.session_state.owner.name}'s care list.")

# Show all pets currently registered with the owner
if st.session_state.pets:
    st.markdown("**Pets registered:**")
    for name, pet in st.session_state.pets.items():
        st.markdown(f"- {name} ({pet.species}, {pet.priority} priority) — {len(pet.get_tasks())} task(s)")

# ---------------------------------------------------------------------------
# Section 3 — Add Tasks to a Pet  →  calls pet.add_task()
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 3: Add Tasks")

if not st.session_state.pets:
    st.info("Add a pet above before adding tasks.")
else:
    # Let the user choose which pet to add tasks to
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
        # Create a Task object and add it to the selected pet using pet.add_task()
        new_task = Task(
            description=task_desc,
            time=task_time,
            frequency=frequency,
            priority=priority
        )
        selected_pet = st.session_state.pets[selected_pet_name]
        selected_pet.add_task(new_task)                     # ← calls pet.add_task()
        st.success(f"Added '{task_desc}' to {selected_pet_name}'s task list.")

    # Display all tasks for every pet
    for name, pet in st.session_state.pets.items():
        tasks = pet.get_tasks()                             # ← calls pet.get_tasks()
        if tasks:
            st.markdown(f"**{name}'s tasks:**")
            st.table([t.to_dict() for t in tasks])

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule  →  calls Scheduler.schedule_day()
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
        # Hand the Owner to the Scheduler — it pulls tasks from all pets automatically
        scheduler = Scheduler(owner=st.session_state.owner)     # ← Scheduler(owner)
        schedule = scheduler.schedule_day()                      # ← schedule_day()

        st.success(f"Schedule built for {st.session_state.owner.name}!")

        # Scheduled tasks
        if schedule.ordered_tasks:
            st.markdown("### Today's Plan")
            for i, (task, reason) in enumerate(
                zip(schedule.ordered_tasks, schedule.explanations), 1
            ):
                st.markdown(f"**{i}. {task.description}**")
                st.caption(f"🕐 {task.time} | {task.frequency} | {task.priority} priority")
                st.caption(f"Why: {reason}")

        # Skipped tasks
        if schedule.skipped_tasks:
            st.markdown("### Could Not Fit Today")
            for task, reason in zip(schedule.skipped_tasks, schedule.skipped_reasons):
                st.markdown(f"- **{task.description}** — {reason}")
