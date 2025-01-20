import asyncio
import datetime as dt
import aiosqlite


class Database:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None

    async def connect(self):
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.db_path)
            self.connection.row_factory = aiosqlite.Row
            await self.init_db()
        return self.connection

    async def init_db(self):
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                sex TEXT,
                weight_kg REAL,
                height_cm REAL,
                age INTEGER,
                activity_minutes INTEGER,
                city TEXT,
                calories_goal_handle INTEGER
            );
        """)
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                user_id INTEGER,
                date TEXT,
                temperature REAL,
                water_goal INTEGER,
                calories_goal INTEGER,
                logged_water INTEGER DEFAULT 0,
                logged_calories INTEGER DEFAULT 0,
                burned_calories INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        await self.connection.commit()

    @classmethod
    async def get_instance(cls, db_path: str = "database.db"):
        async with cls._lock:
            if cls._instance is None:
                cls._instance = Database(db_path)
                await cls._instance.connect()
            return cls._instance

    async def create_profile(
        self,
        user_id: int, sex: str, weight_kg: float,
        height_cm: float, age: int, activity_minutes: int,
        city: str, calories_goal_handle: int
    ):
        await self.connection.execute(
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
                user_id, sex, weight_kg,
                height_cm, age, activity_minutes,
                city, calories_goal_handle
            )
        )
        await self.connection.commit()

    async def create_day(
        self,
        user_id: int, date: str,
        temperature: float, water_goal: int,
        calories_goal: int
    ):
        await self.connection.execute(
            """
            INSERT OR IGNORE INTO daily_stats (
                user_id,
                date,
                temperature,
                water_goal,
                calories_goal
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id, date,
                temperature, water_goal,
                calories_goal
            )
        )
        await self.connection.commit()

    async def update_day_field(
        self,
        user_id: int, date: str,
        field: str, increment: int
    ):
        await self.connection.execute(
            f"""
            UPDATE daily_stats SET {field} = {field} + ?
            WHERE user_id = ? AND date = ?
            """,
            (increment, user_id, date)
        )
        await self.connection.commit()

    async def update_user_weight(self, user_id: int, weight_kg: float):
        await self.connection.execute(
            "UPDATE users SET weight_kg = ? WHERE user_id = ?",
            (weight_kg, user_id)
        )
        await self.connection.commit()

    async def get_user(self, user_id: int) -> aiosqlite.Row | None:
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row

    async def get_daily_stats(
        self,
        user_id: int,
        date: str
    ) -> aiosqlite.Row | None:
        cursor = await self.connection.execute(
            "SELECT * FROM daily_stats WHERE user_id = ? AND date = ?",
            (user_id, date)
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row

    async def get_last_days_stats(self, user_id: int, last_days_num: int):
        today = dt.date.today()
        start_date = str(today - dt.timedelta(days=last_days_num - 1))
        end_date = str(today)
        cursor = await self.connection.execute(
            """
            SELECT * FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC
            """,
            (user_id, start_date, end_date)
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
