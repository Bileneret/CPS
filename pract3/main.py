# main.py
# Програма прогнозує погоду (температуру, опади, вітер і тиск)
# і оцінює якість прогнозу за допомогою MSE (середньоквадратичної помилки)

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from db import get_weather_data, save_prediction

# Назва файлу, куди буде збережено результат прогнозу
RESULT_FILE = 'results.txt'

# -----------------------------------------------------------------------------
# Отримуємо дані з бази даних
# get_weather_data() повертає таблицю з даними у форматі DataFrame
data = get_weather_data()
if data is None:
    print("Не вдалося завантажити дані. Перевірте підключення до бази.")
    exit()

print(f"Завантажено {len(data)} записів із бази.")

# Перетворюємо колонку з датами з рядка у формат дати
data['timestamp'] = pd.to_datetime(data['timestamp'])
print(f"Діапазон дат: {data['timestamp'].min()} - {data['timestamp'].max()}")

# -----------------------------------------------------------------------------
# Додаємо ознаки, які враховують час доби та пору року
# Це допоможе моделі краще розуміти циклічні зміни в погоді

data['hour'] = data['timestamp'].dt.hour  # година доби (0–23)
data['day_of_year'] = data['timestamp'].dt.dayofyear  # день у році (1–365)

# Перетворюємо час у циклічну форму (синус/косинус), бо 23 і 0 година – це поруч
data['sin_hour'] = np.sin(2 * np.pi * data['hour'] / 24)
data['cos_hour'] = np.cos(2 * np.pi * data['hour'] / 24)
data['sin_day'] = np.sin(2 * np.pi * data['day_of_year'] / 365)
data['cos_day'] = np.cos(2 * np.pi * data['day_of_year'] / 365)

# -----------------------------------------------------------------------------
# Створюємо "лаги" — значення погоди за попередні години
# Це потрібно, щоб модель могла вчитись на попередніх значеннях

lag_targets = ['temperature', 'precipitation', 'wind_gust', 'pressure']
lag_dict = {}

# Для кожної змінної створюємо 24 попередні значення (на 24 години назад)
for target in lag_targets:
    for lag in range(1, 25):
        lag_dict[f"{target}_lag_{lag}"] = data[target].shift(lag)

# Об'єднуємо ці лаги з основними даними
lag_df = pd.DataFrame(lag_dict)
data = pd.concat([data, lag_df], axis=1)

# -----------------------------------------------------------------------------
# Видаляємо рядки, де є пропущені значення
# Вони з’являються через лаги (на початку немає попередніх значень)
data = data.dropna()
print(f"Після очищення: {len(data)} записів")

# -----------------------------------------------------------------------------
# Готуємо список ознак (вхідних даних) і цільових змінних (що прогнозуємо)

features = [f"{t}_lag_{lag}" for t in lag_targets for lag in range(1, 25)]
features += ['sin_hour', 'cos_hour', 'sin_day', 'cos_day']
targets = lag_targets  # те, що будемо прогнозувати

# -----------------------------------------------------------------------------
# Ділимо дані на тренувальні і тестові
# Вчимо модель на всьому, що до 06.03.2024
# Перевіряємо модель на даних саме за 06.03.2024

train = data[data['timestamp'] < '2024-03-06']
test = data[data['timestamp'].dt.date == pd.to_datetime('2024-03-06').date()]

if train.empty or test.empty:
    print("Недостатньо даних для тренування або тестування.")
    exit()

X_train, X_test = train[features], test[features]

# -----------------------------------------------------------------------------
# Створюємо і навчаємо модель для кожної змінної
# Використовуємо RandomForest — популярний алгоритм машинного навчання
# Обчислюємо MSE для кожної змінної

models = {}
mse_scores = {}

# Проходимося по кожній змінній, яку потрібно прогнозувати
for target in targets:
    # Витягуємо правильні (реальні) значення для навчання і тестування
    y_train, y_test = train[target], test[target]

    # Створюємо модель Random Forest з 100 деревами
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)

    # Навчаємо модель: намагається знайти залежності між ознаками (X_train) та ціллю (y_train)
    model.fit(X_train, y_train)

    # Робимо прогноз для тестових даних (на 06.03.2024)
    preds = model.predict(X_test)

    # Оцінюємо точність моделі: рахуємо середньоквадратичну помилку
    mse_scores[target] = mean_squared_error(y_test, preds)

    # Зберігаємо навчену модель у словник
    models[target] = model

    # Виводимо точність (MSE) на екран
    print(f"MSE для {target}: {mse_scores[target]:.2f}")

# -----------------------------------------------------------------------------
# Малюємо графік: як модель передбачила температуру
# Порівнюємо прогнозовані значення з реальними

plt.figure(figsize=(12, 6))
plt.plot(test['timestamp'], test['temperature'], label='Реальна')
plt.plot(test['timestamp'], models['temperature'].predict(X_test), label='Прогноз')
plt.xlabel('Дата')
plt.ylabel('Температура (°C)')
plt.title('Прогноз температури на 06.03.2024')
plt.legend()
plt.grid(True)
plt.show()

# -----------------------------------------------------------------------------
# Робимо прогноз на наступний день — 07.03.2024

last_day = pd.to_datetime('2024-03-06').date()
last_data = data[data['timestamp'].dt.date == last_day].tail(1).copy()
if last_data.empty:
    print("Немає даних за 06.03.2024 для прогнозу.")
    exit()

# Оновлюємо лаги: зсуваємо кожен лаг на одну позицію вперед
for t in lag_targets:
    for lag in range(1, 24):
        last_data[f"{t}_lag_{lag}"] = last_data[f"{t}_lag_{lag+1}"]
    last_data[f"{t}_lag_24"] = last_data[t]  # останній лаг — поточне значення

# Оновлюємо циклічні ознаки для 00:00 07.03.2024
last_data['hour'] = 0
last_data['day_of_year'] = pd.to_datetime('2024-03-07').dayofyear
last_data['sin_hour'] = np.sin(2 * np.pi * last_data['hour'] / 24)
last_data['cos_hour'] = np.cos(2 * np.pi * last_data['hour'] / 24)
last_data['sin_day'] = np.sin(2 * np.pi * last_data['day_of_year'] / 365)
last_data['cos_day'] = np.cos(2 * np.pi * last_data['day_of_year'] / 365)

# Формуємо вхідні дані для прогнозу
X_future = last_data[features]
# Отримуємо прогнозовані значення для кожної змінної
predictions = {t: models[t].predict(X_future)[0] for t in targets}
for t, val in predictions.items():
    print(f"Прогноз для {t} на 07.03.2024: {val:.2f}")

# -----------------------------------------------------------------------------
# Зберігаємо прогноз у текстовий файл

forecast_str = (
    f"07.03.2024 00:00\t"
    + ", ".join([f"{t}: {predictions[t]:.2f}" for t in targets])
    + "\n"
)
with open(RESULT_FILE, 'w', encoding='utf-8') as f:
    f.write(forecast_str)
print(f"Прогноз збережено у {RESULT_FILE}")

# -----------------------------------------------------------------------------
# Зберігаємо прогноз у базу даних
# Частину значень, які не прогнозуються, заповнюємо нулями (0.0)

save_prediction(
    '2024-03-07 00:00:00',
    predictions['temperature'],
    0.0,                        # GDD не прогнозується
    predictions['precipitation'],
    0.0,                        # Вологість не прогнозується
    0.0, 0.0,                   # Сніг та його глибина не прогнозуються
    predictions['wind_gust'],
    0.0, 0.0, 0.0, 0.0,         # Інші характеристики вітру не прогнозуються
    0.0, 0.0, 0.0, 0.0,         # Хмарність не прогнозується
    predictions['pressure']
)
