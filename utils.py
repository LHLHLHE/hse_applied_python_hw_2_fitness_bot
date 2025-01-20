import datetime as dt
import io

import httpx
from googletrans import Translator
import matplotlib.pyplot as plt
from matplotlib import dates as mdates

from config import (
    OPEN_WEATHER_API_KEY,
    NUTRITIONIX_API_APP_ID,
    NUTRITIONIX_API_APP_KEY
)
from database import Database


def create_graph(data: list[dict], key: str, ylabel: str, title: str):
    dates = [
        dt.datetime.strptime(entry["date"], "%Y-%m-%d")
        for entry in data
    ]
    values = [entry[key] for entry in data]

    fig, ax = plt.subplots()
    ax.plot(dates, values, marker="o")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator())

    plt.xlabel("Дата")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer


async def user_has_profile(user_id: int):
    db = await Database.get_instance()
    return await db.get_user(user_id) is not None


async def new_day_was_begun(user_id: int):
    db = await Database.get_instance()
    return await db.get_daily_stats(user_id, str(dt.date.today())) is not None


async def translate_text(query: str):
    async with Translator() as translator:
        result = await translator.translate(query)
        return result.text


async def get_current_temperature(city: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPEN_WEATHER_API_KEY,
                "units": "metric"
            }
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            if response.status_code == 404:
                return None

        return response.json()["main"]["temp"]


async def get_food_info(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://trackapi.nutritionix.com/v2/natural/nutrients",
            headers={
                "x-app-id": NUTRITIONIX_API_APP_ID,
                "x-app-key": NUTRITIONIX_API_APP_KEY
            },
            json={"query": query},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            if response.status_code == 404:
                return None

        data = response.json()
        if not data.get("foods", []):
            return None
        return data["foods"][0]


async def get_exercise_info(
    query: str,
    weight_kg: float,
    height_cm: float,
    age: int
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://trackapi.nutritionix.com/v2/natural/exercise",
            headers={
                "x-app-id": NUTRITIONIX_API_APP_ID,
                "x-app-key": NUTRITIONIX_API_APP_KEY
            },
            json={
                "query": query,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "age": age
            },
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            if response.status_code == 404:
                return None

        data = response.json()
        if not data.get("exercises", []):
            return None
        return data["exercises"][0]


def calculate_water_goal(
    sex: str,
    weight_kg: float,
    activity_minutes: int,
    temperature: float
):
    water_goal = weight_kg * 30 + 500 * activity_minutes // 30

    if sex == "male":
        water_goal += 500
    if temperature > 25:
        water_goal += 500
    if temperature > 30:
        water_goal += 500

    return int(water_goal)


def calculate_calories_goal(
    sex: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_minutes: int
):
    calories_goal = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "male":
        calories_goal += 5
    else:
        calories_goal -= 161
    calories_goal += 12 * activity_minutes
    return int(calories_goal)
