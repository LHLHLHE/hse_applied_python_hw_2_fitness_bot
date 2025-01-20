from aiogram.fsm.state import State, StatesGroup


class Profile(StatesGroup):
    sex = State()
    weight_kg = State()
    height_cm = State()
    age = State()
    activity_minutes = State()
    city = State()
    calories_goal = State()
