import mysql.connector
from datetime import datetime
from config import DB_CONFIG


def get_all_meters():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM meters")
    result = cursor.fetchall()
    conn.close()
    return result

def delete_meter(meter_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meters WHERE meter_id = %s", (meter_id,))
    conn.commit()
    conn.close()
    return "Лічильник видалено."

def add_meter(meter_id, password, day_value=0.0, night_value=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    try:
        cursor.execute("""
            INSERT INTO meters (meter_id, password, day_value, night_value, last_update)
            VALUES (%s, %s, %s, %s, %s)
        """, (meter_id, password, day_value, night_value, now))
        conn.commit()
        return "Лічильник додано."
    except mysql.connector.IntegrityError:
        return "Такий лічильник вже існує."
    finally:
        conn.close()


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_settings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT setting_key, setting_value FROM settings")
    result = {row["setting_key"]: row["setting_value"] for row in cursor.fetchall()}
    conn.close()
    return result


def get_meter(meter_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM meters WHERE meter_id = %s", (meter_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def save_meter_data_and_bill(meter_id, new_day, new_night):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    settings = get_settings()

    day_tariff = float(settings["day_tariff"])
    night_tariff = float(settings["night_tariff"])
    day_fake = float(settings["day_fake_increment"])
    night_fake = float(settings["night_fake_increment"])
    now = datetime.now()

    cursor.execute("SELECT * FROM meters WHERE meter_id = %s", (meter_id,))
    existing = cursor.fetchone()

    if existing:
        last_day = existing["day_value"]
        last_night = existing["night_value"]

        day_diff = new_day - last_day
        night_diff = new_night - last_night
        fake_used = False

        if day_diff < 0:
            day_diff = day_fake
            fake_used = True
        if night_diff < 0:
            night_diff = night_fake
            fake_used = True

        total_cost = day_diff * day_tariff + night_diff * night_tariff

        cursor.execute("""
            INSERT INTO meter_readings_history (meter_id, reading_time, day_value, night_value)
            VALUES (%s, %s, %s, %s)
        """, (meter_id, now, new_day, new_night))

        cursor.execute("""
            INSERT INTO bills (meter_id, bill_time, day_kwh_used, night_kwh_used, total_cost)
            VALUES (%s, %s, %s, %s, %s)
        """, (meter_id, now, day_diff, night_diff, total_cost))

        cursor.execute("""
            UPDATE meters SET day_value=%s, night_value=%s, last_update=%s WHERE meter_id=%s
        """, (new_day, new_night, now, meter_id))

        conn.commit()
        conn.close()

        return f"Вартість: {total_cost:.2f} грн\n(День: {day_diff} кВт, Ніч: {night_diff} кВт)\n{'Накручено!' if fake_used else ''}"
    else:
        password = '000000' #def pass
        cursor.execute("""
            INSERT INTO meters (meter_id, password, last_update, day_value, night_value)
            VALUES (%s, %s, %s, %s, %s)
        """, (meter_id, password, now, new_day, new_night))

        cursor.execute("""
            INSERT INTO meter_readings_history (meter_id, reading_time, day_value, night_value)
            VALUES (%s, %s, %s, %s)
        """, (meter_id, now, new_day, new_night))

        conn.commit()
        conn.close()

        return "Додано новий лічильник. Початкові дані збережено."


def get_all_meter_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM meter_readings_history ORDER BY reading_time DESC")
    result = cursor.fetchall()
    conn.close()
    return result


def update_tariffs(day_tariff, night_tariff):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE settings
        SET setting_value = %s
        WHERE setting_key = 'day_tariff'
    """, (day_tariff,))

    cursor.execute("""
        UPDATE settings
        SET setting_value = %s
        WHERE setting_key = 'night_tariff'
    """, (night_tariff,))

    conn.commit()
    conn.close()


def get_meter_history(meter_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT reading_time, day_value, night_value
        FROM meter_readings_history
        WHERE meter_id = %s
        ORDER BY reading_time DESC
    """, (meter_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def update_password(meter_id, old_password, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    # Перевірка старого паролю
    cursor.execute("SELECT password FROM meters WHERE meter_id = %s", (meter_id,))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return "Користувача не знайдено."

    if record[0] != old_password:
        conn.close()
        return "Старий пароль невірний."

    # Оновлення пароля
    cursor.execute("UPDATE meters SET password = %s WHERE meter_id = %s", (new_password, meter_id))
    conn.commit()
    conn.close()
    return "Пароль успішно змінено."

def clear_meter_history(meter_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Знайти найновішу дату запису
    cursor.execute("""
        SELECT id FROM meter_readings_history 
        WHERE meter_id = %s 
        ORDER BY reading_time DESC 
        LIMIT 1
    """, (meter_id,))
    last_record = cursor.fetchone()

    if last_record:
        last_id = last_record[0]

        # Видалити всі інші записи крім найновішого
        cursor.execute("""
            DELETE FROM meter_readings_history 
            WHERE meter_id = %s AND id != %s
        """, (meter_id, last_id))
        conn.commit()

    conn.close()
    
def get_tariffs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT setting_key, setting_value FROM settings WHERE setting_key IN ('day_tariff', 'night_tariff')")
    results = cursor.fetchall()
    conn.close()
    return {row["setting_key"]: row["setting_value"] for row in results}

def update_tariff(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET setting_value = %s WHERE setting_key = %s", (value, key))
    conn.commit()
    conn.close()




