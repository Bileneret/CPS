# db.py
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine
from mysql.connector import Error
from config import DB_CONFIG

def get_connection():
    """Повертає з'єднання з базою даних через mysql-connector."""
    return mysql.connector.connect(**DB_CONFIG)

def get_weather_data():
    """Повертає всі дані з таблиці weather_data через SQLAlchemy."""
    try:
        db_uri = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(db_uri)
        query = "SELECT * FROM weather_data ORDER BY timestamp"
        data = pd.read_sql(query, engine)
        return data
    except Exception as e:
        print(f"Помилка: {e}")
        return None
    finally:
        engine.dispose()

def save_prediction(forecast_date, predicted_temperature, predicted_gdd, predicted_precipitation,
                   predicted_humidity, predicted_snowfall, predicted_snow_depth, predicted_wind_gust,
                   predicted_wind_speed_10m, predicted_wind_direction_10m, predicted_wind_speed_100m,
                   predicted_wind_direction_100m, predicted_cloud_cover_total, predicted_cloud_cover_high,
                   predicted_cloud_cover_medium, predicted_cloud_cover_low, predicted_pressure):
    """Зберігає прогноз у таблицю predictions."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Створення таблиці predictions, якщо не існує
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            forecast_date DATETIME NOT NULL,
            predicted_temperature FLOAT,
            predicted_gdd FLOAT,
            predicted_precipitation FLOAT,
            predicted_humidity FLOAT,
            predicted_snowfall FLOAT,
            predicted_snow_depth FLOAT,
            predicted_wind_gust FLOAT,
            predicted_wind_speed_10m FLOAT,
            predicted_wind_direction_10m FLOAT,
            predicted_wind_speed_100m FLOAT,
            predicted_wind_direction_100m FLOAT,
            predicted_cloud_cover_total FLOAT,
            predicted_cloud_cover_high FLOAT,
            predicted_cloud_cover_medium FLOAT,
            predicted_cloud_cover_low FLOAT,
            predicted_pressure FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Конвертація всіх параметрів у float
        params = (
            forecast_date,
            float(predicted_temperature),
            float(predicted_gdd),
            float(predicted_precipitation),
            float(predicted_humidity),
            float(predicted_snowfall),
            float(predicted_snow_depth),
            float(predicted_wind_gust),
            float(predicted_wind_speed_10m),
            float(predicted_wind_direction_10m),
            float(predicted_wind_speed_100m),
            float(predicted_wind_direction_100m),
            float(predicted_cloud_cover_total),
            float(predicted_cloud_cover_high),
            float(predicted_cloud_cover_medium),
            float(predicted_cloud_cover_low),
            float(predicted_pressure)
        )

        # Вставка прогнозу
        cursor.execute("""
        INSERT INTO predictions (
            forecast_date, predicted_temperature, predicted_gdd, predicted_precipitation,
            predicted_humidity, predicted_snowfall, predicted_snow_depth, predicted_wind_gust,
            predicted_wind_speed_10m, predicted_wind_direction_10m, predicted_wind_speed_100m,
            predicted_wind_direction_100m, predicted_cloud_cover_total, predicted_cloud_cover_high,
            predicted_cloud_cover_medium, predicted_cloud_cover_low, predicted_pressure
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, params)

        conn.commit()
        print("Прогноз збережено в таблиці predictions.")
    except Error as e:
        print(f"Помилка: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
            print("Підключення до MySQL закрито.")