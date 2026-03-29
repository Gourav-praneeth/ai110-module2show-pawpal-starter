from pawpal_system import Task, Pet, Owner, Scheduler

# --- Create Owner ---
owner = Owner(name="Jordan", available_minutes=120, preferred_start_time="08:00")

# --- Create Pets ---
dog = Pet(name="Mochi", species="dog", age=3, priority="high")
cat = Pet(name="Luna", species="cat", age=5, priority="medium")

# --- Add Tasks to Mochi (dog) ---
dog.add_task(Task(description="Morning walk",      time="08:00", frequency="daily",       priority="high"))
dog.add_task(Task(description="Feed breakfast",    time="08:30", frequency="twice daily",  priority="high"))
dog.add_task(Task(description="Give flea medicine",time="09:00", frequency="weekly",       priority="medium"))

# --- Add Tasks to Luna (cat) ---
cat.add_task(Task(description="Clean litter box",  time="09:30", frequency="daily",        priority="medium"))
cat.add_task(Task(description="Brush fur",         time="10:00", frequency="weekly",       priority="low"))

# --- Register Pets with Owner ---
owner.add_pet(dog)
owner.add_pet(cat)

# --- Run Scheduler ---
scheduler = Scheduler(owner=owner)
schedule = scheduler.schedule_day()

# --- Print Today's Schedule ---
print(schedule.display())
