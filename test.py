async def generate_dummy_daily_stats(db: Database, user_id: int, start_date: str, end_date: str):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    current_date = start

    await db.connection.execute(
        """
        INSERT OR REPLACE INTO users (
            user_id,
            sex,
            weight_kg,
            height_cm,
            age,
            activity_minutes,
            city,
            calories_goal_handle
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "Мужчина",
            65,
            177,
            21,
            30,
            "Москва",
            0
        )
    )
    await db.connection.commit()
    while current_date <= end:
        temperature = round(random.uniform(0.0, 2.0), 2)
        water_goal = random.randint(1800, 3000)
        calories_goal = random.randint(2100, 2500)
        logged_water = random.randint(0, water_goal)
        logged_calories = random.randint(0, calories_goal)
        burned_calories = random.randint(0, 500)

        await db.connection.execute(
            """
            INSERT OR REPLACE INTO daily_stats (
                user_id, 
                date, 
                temperature, 
                water_goal, 
                calories_goal,
                logged_water,
                logged_calories,
                burned_calories
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                str(current_date),
                temperature,
                water_goal,
                calories_goal,
                logged_water,
                logged_calories,
                burned_calories
            )
        )
        current_date += datetime.timedelta(days=1)
        await db.connection.commit()

    print(f"Данные с {start_date} по {end_date} для user_id={user_id} успешно сгенерированы.")


async def on_startup():
    # Инициализируем подключение к базе данных и создаём таблицы
    db = await Database.get_instance()
    await generate_dummy_daily_stats(db, 350933706, "2025-01-15",
                                     "2025-01-19")
    logger.info("База данных инициализирована.")