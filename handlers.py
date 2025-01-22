import datetime as dt

from aiogram import Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BufferedInputFile
)
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from database import Database
from states import Profile
from string_constants import (
    START_MSG, HELP_MSG, ENTER_NUM_ERROR_MSG, ENTER_INT_ERROR_MSG,
    PROFILE_NOT_EXISTS_MSG, NEW_DAY_NOT_BEGIN, ENTER_SEX_MSG, ENTER_WEIGHT_MSG,
    ENTER_HEIGHT_MSG, ENTER_AGE_MSG, ENTER_ACTIVITY_MSG, ENTER_CITY_MSG,
    ENTER_CALORIES_GOAL_MSG, ENTER_INT_ML_ERROR_MSG, LOG_FOOD_ARGS_ERROR_MSG,
    PRODUCT_NOT_FOUND_MSG, LOG_WORKOUT_ARGS_ERROR_MSG,
    LOG_WORKOUT_DURATION_ERROR_MSG, WORKOUT_NOT_FOUND_MSG,
    NEW_DAY_ALREADY_BEGUN, CITY_NOT_FOUND_MSG, DATA_FOR_GRAPH_NOT_FOUND_MSG,
    ENTER_INT_DAYS_ERROR_MSG,
)

from utils import (
    get_current_temperature,
    calculate_water_goal,
    calculate_calories_goal,
    get_food_info,
    get_exercise_info,
    translate_text,
    user_has_profile,
    new_day_was_begun,
    create_graph,
)

router = Router()

SEX_CHOICES = {
    "male": "Мужчина",
    "female": "Женщина",
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(START_MSG)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(HELP_MSG)


@router.message(Command("set_profile"))
async def start_profile_form(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мужчина", callback_data="male")],
            [InlineKeyboardButton(text="Женщина", callback_data="female")],
        ]
    )
    await message.reply(ENTER_SEX_MSG, reply_markup=keyboard)
    await state.set_state(Profile.sex)


@router.callback_query(Profile.sex)
async def process_sex(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(sex=SEX_CHOICES[callback_query.data])
    await callback_query.message.reply(ENTER_WEIGHT_MSG)
    await state.set_state(Profile.weight_kg)


@router.message(Profile.weight_kg)
async def process_weight(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await message.reply(ENTER_NUM_ERROR_MSG)
        return

    await state.update_data(weight_kg=message.text)
    await message.reply(ENTER_HEIGHT_MSG)
    await state.set_state(Profile.height_cm)


@router.message(Profile.height_cm)
async def process_height(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await message.reply(ENTER_NUM_ERROR_MSG)
        return

    await state.update_data(height_cm=message.text)
    await message.reply(ENTER_AGE_MSG)
    await state.set_state(Profile.age)


@router.message(Profile.age)
async def process_age(message: Message, state: FSMContext):
    try:
        int(message.text)
    except ValueError:
        await message.reply(ENTER_INT_ERROR_MSG)
        return

    await state.update_data(age=message.text)
    await message.reply(ENTER_ACTIVITY_MSG)
    await state.set_state(Profile.activity_minutes)


@router.message(Profile.activity_minutes)
async def process_activity_minutes(message: Message, state: FSMContext):
    try:
        int(message.text)
    except ValueError:
        await message.reply(ENTER_INT_ERROR_MSG)
        return

    await state.update_data(activity_minutes=message.text)
    await message.reply(ENTER_CITY_MSG)
    await state.set_state(Profile.city)


@router.message(Profile.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply(ENTER_CALORIES_GOAL_MSG)
    await state.set_state(Profile.calories_goal)


@router.message(Profile.calories_goal)
async def process_calories_goal(message: Message, state: FSMContext):
    try:
        calories_goal_handle = int(message.text)
    except ValueError:
        await message.reply(ENTER_INT_ERROR_MSG)
        return

    data = await state.get_data()
    sex = data.get("sex")
    weight_kg = float(data.get("weight_kg", "0"))
    height_cm = float(data.get("height_cm", "0"))
    age = int(data.get("age", "0"))
    activity_minutes = int(data.get("activity_minutes", "0"))
    city = data.get("city")

    curr_temp = await get_current_temperature(data.get("city"))
    if not curr_temp:
        await message.reply(CITY_NOT_FOUND_MSG)
        await state.set_state(Profile.city)
        return

    water_goal = calculate_water_goal(
        sex,
        weight_kg,
        activity_minutes,
        curr_temp
    )
    calories_goal = calories_goal_handle or calculate_calories_goal(
        sex,
        weight_kg,
        height_cm,
        age,
        activity_minutes
    )

    user_id = message.from_user.id
    db = await Database.get_instance()
    await db.create_profile(
        user_id, sex, weight_kg,
        height_cm, age, activity_minutes,
        city, calories_goal_handle
    )
    await db.create_day(
        user_id,
        str(dt.date.today()),
        curr_temp,
        water_goal,
        calories_goal
    )

    await message.reply(f"""
    Ваши данные:
    Пол: {sex}
    Вес: {weight_kg} кг
    Рост: {height_cm} см
    Возраст: {age}
    Активность: {activity_minutes} мин
    Город: {city}
    Температура: {curr_temp}ºC
    Цель по калориям: {calories_goal} ккал
    Норма воды: {water_goal} мл
    Выпито воды: 0 мл из {water_goal} мл
    Потреблено калорий: 0 ккал из {calories_goal} ккал
    Сожжено калорий: 0 ккал
    """)

    await state.clear()


@router.message(Command("log_water"))
async def log_water(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return
    if not await new_day_was_begun(user_id):
        await message.reply(NEW_DAY_NOT_BEGIN)
        return

    try:
        amount = int(command.args.split(" ")[0])
    except (ValueError, AttributeError):
        await message.reply(ENTER_INT_ML_ERROR_MSG)
        return

    db = await Database.get_instance()
    await db.update_day_field(
        user_id,
        str(dt.date.today()),
        "logged_water",
        amount
    )

    await message.reply(f"Записано: {amount} мл.")


@router.message(Command("log_food"))
async def log_food(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return
    if not await new_day_was_begun(user_id):
        await message.reply(NEW_DAY_NOT_BEGIN)
        return

    try:
        command.args.split(" ")
    except AttributeError:
        await message.reply(LOG_FOOD_ARGS_ERROR_MSG)
        return

    product_info = await get_food_info(await translate_text(command.args))
    if not product_info:
        await message.reply(PRODUCT_NOT_FOUND_MSG)
        return

    new_calories = product_info["nf_calories"]

    db = await Database.get_instance()
    await db.update_day_field(
        user_id,
        str(dt.date.today()),
        "logged_calories",
        new_calories
    )

    await message.reply(f"Записано: {new_calories} ккал.")


@router.message(Command("log_workout"))
async def log_workout(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return
    if not await new_day_was_begun(user_id):
        await message.reply(NEW_DAY_NOT_BEGIN)
        return

    try:
        args = command.args.split(" ")
    except AttributeError:
        await message.reply(LOG_WORKOUT_ARGS_ERROR_MSG)
        return

    if len(args) < 2:
        await message.reply(LOG_WORKOUT_ARGS_ERROR_MSG)
        return

    workout_type = " ".join(args[:-1])
    try:
        workout_duration = int(args[-1].strip())
    except ValueError:
        await message.reply(LOG_WORKOUT_DURATION_ERROR_MSG)
        return

    db = await Database.get_instance()
    user_info = await db.get_user(user_id)

    exercise_info = await get_exercise_info(
        await translate_text(f"{command.args} мин"),
        user_info["weight_kg"],
        user_info["height_cm"],
        user_info["age"]
    )
    if not exercise_info:
        await message.reply(WORKOUT_NOT_FOUND_MSG)

    burned_calories = exercise_info["nf_calories"]
    await db.update_day_field(
        user_id,
        str(dt.date.today()),
        "burned_calories",
        burned_calories
    )

    msg = (
        f"{workout_type.capitalize()} {workout_duration} мин "
        f"- {burned_calories} ккал."
    )
    extra_water = workout_duration // 30 * 200
    if extra_water > 0:
        await db.update_day_field(
            user_id,
            str(dt.date.today()),
            "water_goal",
            extra_water
        )
        msg += f" Дополнительно: выпейте {extra_water} мл воды."

    await message.reply(msg)


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return
    if not await new_day_was_begun(user_id):
        await message.reply(NEW_DAY_NOT_BEGIN)
        return

    db = await Database.get_instance()
    daily_stats = await db.get_daily_stats(
        user_id,
        str(dt.date.today())
    )

    logged_water = daily_stats["logged_water"]
    water_goal = daily_stats["water_goal"]
    remaining_water = max(water_goal - logged_water, 0)

    logged_calories = daily_stats["logged_calories"]
    calories_goal = daily_stats["calories_goal"]
    burned_calories = daily_stats["burned_calories"]
    calorie_balance = logged_calories - burned_calories

    await message.reply(f"""
    Прогресс:
    Вода:
    - Выпито: {logged_water} мл из {water_goal} мл.
    - Осталось: {remaining_water} мл.
    Калории:
    - Потреблено: {logged_calories} ккал из {calories_goal} ккал.
    - Сожжено: {burned_calories} ккал.
    - Баланс: {calorie_balance} ккал.
    """)


@router.message(Command("new_day"))
async def new_day(message: Message):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return
    if await new_day_was_begun(user_id):
        await message.reply(NEW_DAY_ALREADY_BEGUN)
        return

    db = await Database.get_instance()
    user_info = await db.get_user(user_id)

    curr_temp = await get_current_temperature(user_info["city"])
    water_goal = calculate_water_goal(
        user_info["sex"],
        user_info["weight_kg"],
        user_info["activity_minutes"],
        curr_temp
    )

    calories_goal = (
        user_info["calories_goal_handle"]
        or calculate_calories_goal(
            user_info["sex"],
            user_info["weight_kg"],
            user_info["height_cm"],
            user_info["age"],
            user_info["activity_minutes"],
        )
    )

    await db.create_day(
        user_id,
        str(dt.date.today()),
        curr_temp,
        water_goal,
        calories_goal
    )

    await message.reply(f"""
    Цели на сегодня:
        - Выпить: {water_goal} мл.
        - Потребить: {calories_goal} ккал.
    """)


@router.message(Command("set_weight"))
async def set_weight(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return

    try:
        weight_kg = float(command.args.split(" ")[0])
    except (ValueError, AttributeError):
        await message.reply(ENTER_NUM_ERROR_MSG)
        return

    db = await Database.get_instance()
    await db.update_user_weight(user_id, weight_kg)

    await message.reply(f"Вес установлен: {weight_kg} кг.")


@router.message(Command("progress_graphs"))
async def send_progress_graphs(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not await user_has_profile(user_id):
        await message.reply(PROFILE_NOT_EXISTS_MSG)
        return

    try:
        days_num = int(command.args.split(" ")[0])
    except AttributeError:
        days_num = 7
    except ValueError:
        await message.reply(ENTER_INT_DAYS_ERROR_MSG)
        return

    db = await Database.get_instance()
    rows = await db.get_last_days_stats(user_id, days_num)
    if not rows:
        await message.reply(DATA_FOR_GRAPH_NOT_FOUND_MSG)
        return

    water_data = [
        {"date": row["date"], "logged_water": row["logged_water"]}
        for row in rows
    ]
    calories_data = [
        {"date": row["date"], "logged_calories": row["logged_calories"]} for
        row in rows
    ]

    water_graph = create_graph(
        water_data,
        "logged_water",
        "Вода (мл)",
        "Прогресс выпитой воды (за последние 7 дней)"
    )

    calories_graph = create_graph(
        calories_data,
        "logged_calories",
        "Калории",
        "Прогресс потребленных калорий (за последние 7 дней)"
    )

    water_file = BufferedInputFile(
        water_graph.read(),
        filename="water_graph.png"
    )
    await message.reply_document(
        document=water_file,
        mimetype='image/png'
    )

    calories_file = BufferedInputFile(
        calories_graph.read(),
        filename="calories_graph.png"
    )
    await message.reply_document(
        document=calories_file,
        mimetype='image/png'
    )


def setup_handlers(dp):
    dp.include_router(router)
