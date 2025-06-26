import unittest
from db import get_connection, add_meter, get_meter, save_meter_data_and_bill
from config import DB_CONFIG
import mysql.connector

class TestElectricityDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Підключення до MySQL для створення тестової бази даних
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS test_electricity_db")
        cursor.execute("USE test_electricity_db")
        
        # Створення таблиць
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                setting_key VARCHAR(50) UNIQUE,
                setting_value FLOAT
            )
        """)
        cursor.execute("""
            INSERT INTO settings (setting_key, setting_value) VALUES
            ('day_tariff', 2.4),
            ('night_tariff', 1.2),
            ('day_fake_increment', 100),
            ('night_fake_increment', 80)
            ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                meter_id VARCHAR(20) PRIMARY KEY,
                password VARCHAR(255) NOT NULL,
                last_update DATETIME,
                day_value FLOAT,
                night_value FLOAT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings_history (
                id INT PRIMARY KEY AUTO_INCREMENT,
                meter_id VARCHAR(20),
                reading_time DATETIME,
                day_value FLOAT,
                night_value FLOAT,
                FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INT PRIMARY KEY AUTO_INCREMENT,
                meter_id VARCHAR(20),
                bill_time DATETIME,
                day_kwh_used FLOAT,
                night_kwh_used FLOAT,
                total_cost FLOAT,
                FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Налаштування тестової бази даних у конфігурації
        cls.original_db_config = DB_CONFIG.copy()
        DB_CONFIG['database'] = 'test_electricity_db'

    @classmethod
    def tearDownClass(cls):
        # Відновлення оригінальної конфігурації та видалення тестової бази
        DB_CONFIG.update(cls.original_db_config)
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()
        cursor.execute("DROP DATABASE test_electricity_db")
        conn.commit()
        conn.close()

    def setUp(self):
        # Очищення таблиць перед кожним тестом
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meter_readings_history")
        cursor.execute("DELETE FROM bills")
        cursor.execute("DELETE FROM meters")
        conn.commit()
        conn.close()

    def test_update_existing_meter(self):
        add_meter('123', '123123', 100, 50)
        result = save_meter_data_and_bill('123', 150, 70)
        
        self.assertIn("Вартість: 144.00 грн", result)  # Очікуємо правильну вартість
        meter = get_meter('123')
        self.assertEqual(meter['day_value'], 150)
        self.assertEqual(meter['night_value'], 70)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bills WHERE meter_id = '123'")
        bills = cursor.fetchall()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]['day_kwh_used'], 50)
        self.assertEqual(bills[0]['night_kwh_used'], 20)
        self.assertEqual(bills[0]['total_cost'], 144.00)  # Перевіряємо правильну суму
        conn.close()

    def test_add_new_meter(self):
        # Тест додавання нового лічильника
        result = save_meter_data_and_bill('456', 200, 100)
        
        self.assertIn("Додано новий лічильник", result)
        meter = get_meter('456')
        self.assertEqual(meter['day_value'], 200)
        self.assertEqual(meter['night_value'], 100)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bills WHERE meter_id = '456'")
        bills = cursor.fetchall()
        self.assertEqual(len(bills), 0)
        conn.close()

    def test_underreported_night(self):
        # Тест із заниженими нічними показниками
        add_meter('789', '890890', 100, 50)
        result = save_meter_data_and_bill('789', 150, 40)
        
        self.assertIn("Накручено!", result)
        self.assertIn("Вартість: 216.00 грн", result)
        meter = get_meter('789')
        self.assertEqual(meter['day_value'], 150)
        self.assertEqual(meter['night_value'], 40)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bills WHERE meter_id = '789'")
        bills = cursor.fetchall()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]['day_kwh_used'], 50)
        self.assertEqual(bills[0]['night_kwh_used'], 80)
        self.assertEqual(bills[0]['total_cost'], 216.00)
        conn.close()

    def test_underreported_day(self):
        # Тест із заниженими денними показниками
        add_meter('101', '101101', 100, 50)
        result = save_meter_data_and_bill('101', 90, 70)
        
        self.assertIn("Накручено!", result)
        self.assertIn("Вартість: 264.00 грн", result)
        meter = get_meter('101')
        self.assertEqual(meter['day_value'], 90)
        self.assertEqual(meter['night_value'], 70)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bills WHERE meter_id = '101'")
        bills = cursor.fetchall()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]['day_kwh_used'], 100)
        self.assertEqual(bills[0]['night_kwh_used'], 20)
        self.assertEqual(bills[0]['total_cost'], 264.00)
        conn.close()

    def test_underreported_both(self):
        # Тест із заниженими денними та нічними показниками
        add_meter('102', '111111', 100, 50)
        result = save_meter_data_and_bill('102', 90, 40)
        
        self.assertIn("Накручено!", result)
        self.assertIn("Вартість: 336.00 грн", result)
        meter = get_meter('102')
        self.assertEqual(meter['day_value'], 90)
        self.assertEqual(meter['night_value'], 40)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bills WHERE meter_id = '102'")
        bills = cursor.fetchall()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]['day_kwh_used'], 100)
        self.assertEqual(bills[0]['night_kwh_used'], 80)
        self.assertEqual(bills[0]['total_cost'], 336.00)
        conn.close()

if __name__ == '__main__':
    unittest.main()