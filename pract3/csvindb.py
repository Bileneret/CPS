# csvinDB.py
import pandas as pd
from mysql.connector import Error
from db import get_connection

# Наповнення бази даними з CSV
csv_file = 'dataexport_20250508T130923.csv'

try:
    # Завантаження CSV, вказуємо рядок із заголовками
    data = pd.read_csv(csv_file, header=9)
    print("Назви стовпців у CSV:", list(data.columns))
    if 'timestamp' not in data.columns:
        raise ValueError("Стовпець 'timestamp' не знайдено в CSV")

    print("Перші 5 значень стовпця timestamp:", data['timestamp'].head().tolist())
    data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y%m%dT%H%M')

    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO weather_data (
        timestamp, temperature, precipitation, humidity, snowfall,
        snow_depth, wind_gust, wind_speed_10m, wind_direction_10m,
        wind_speed_100m, wind_direction_100m, cloud_cover_total,
        cloud_cover_high, cloud_cover_medium, cloud_cover_low, pressure
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    count = 0
    for index, row in data.iterrows():
        print(f"Обробка рядка {index}: timestamp={row['timestamp']}, temperature={row['Basel Temperature [2 m elevation corrected]']}")
        values = (
            row['timestamp'].to_pydatetime(),
            row['Basel Temperature [2 m elevation corrected]'],
            row['Basel Precipitation Total'],
            row['Basel Relative Humidity [2 m]'],
            row['Basel Snowfall Amount'],
            row['Basel Snow Depth'],
            row['Basel Wind Gust'],
            row['Basel Wind Speed [10 m]'],
            row['Basel Wind Direction [10 m]'],
            row['Basel Wind Speed [100 m]'],
            row['Basel Wind Direction [100 m]'],
            row['Basel Cloud Cover Total'],
            row['Basel Cloud Cover High [high cld lay]'],
            row['Basel Cloud Cover Medium [mid cld lay]'],
            row['Basel Cloud Cover Low [low cld lay]'],
            row['Basel Mean Sea Level Pressure [MSL]']
        )
        cursor.execute(insert_query, values)
        count += 1

    conn.commit()
    print(f"Успішно вставлено {count} записів у таблицю weather_data.")
except Error as e:
    print(f"Помилка бази даних: {e}")
except FileNotFoundError:
    print(f"Файл {csv_file} не знайдено. Перевірте шлях до файлу.")
except ValueError as e:
    print(f"Помилка даних: {e}")
except Exception as e:
    print(f"Інша помилка: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()
        print("Підключення до MySQL закрито.")