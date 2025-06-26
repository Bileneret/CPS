# test_main.py
import unittest
import pandas as pd
import numpy as np
from main import get_weather_data, save_prediction

class TestWeatherPrediction(unittest.TestCase):
    def test_data_loading(self):
        """Тест завантаження даних з бази"""
        data = get_weather_data()
        self.assertIsNotNone(data, "Дані не завантажилися з бази")
        self.assertGreater(len(data), 0, "Дані порожні")
        self.assertIn('temperature', data.columns, "Відсутній стовпець temperature")

    def test_lag_creation(self):
        """Тест створення лагів"""
        data = get_weather_data()
        lag_dict = {}
        for target in ['temperature']:
            for lag in range(1, 3):
                lag_dict[f'{target}_lag_{lag}'] = data[target].shift(lag)
        lag_df = pd.DataFrame(lag_dict)
        data = pd.concat([data, lag_df], axis=1)
        self.assertIn('temperature_lag_1', data.columns, "Лаги не створені")

    def test_save_prediction(self):
        """Тест збереження прогнозу"""
        save_prediction(
            '2024-03-07 00:00:00', 5.0, 0.0, 0.1, 90.0, 0.0, 0.0, 7.0,
            2.0, 200.0, 3.0, 250.0, 80.0, 20.0, 70.0, 80.0, 1020.0
        )
        # Перевіряємо, що запис є в базі
        data = get_weather_data()
        self.assertTrue(any(data['timestamp'] == '2024-03-07 00:00:00'), "Прогноз не зберігся")

if __name__ == '__main__':
    unittest.main()