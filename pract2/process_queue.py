import time
import random
import threading
from queue import Queue
from db import save_meter_data_and_bill, get_meter, add_meter

# Створюємо чергу
message_queue = Queue()

# Функція-генератор тестових даних
def generate_test_data():
    while True:
        meter_id = str(random.randint(1, 5))  # Рандомний ID від 1 до 10
        meter = get_meter(meter_id)
        
        if meter:
            # Якщо лічильник існує, генеруємо нові показники більші за попередні
            prev_day = meter['day_value']
            prev_night = meter['night_value']
            day_value = prev_day + random.randint(-20, 50)
            night_value = prev_night + random.randint(-20, 50)
        else:
            # Якщо лічильник новий, додаємо його з початковими показниками і паролем "000000"
            day_value = random.randint(0, 50)
            night_value = random.randint(0, 50)
            add_meter(meter_id, "000000", day_value, night_value)
        
        message = {
            'meter_id': meter_id,
            'day_value': day_value,
            'night_value': night_value
        }
        message_queue.put(message)
        print(f"Sent: {message}")
        time.sleep(5)  # Відправляємо кожні 5 секунд

# Функція-обробник черги
def process_queue():
    while True:
        if not message_queue.empty():
            data = message_queue.get()
            meter_id = data['meter_id']
            day_value = data['day_value']
            night_value = data['night_value']
            result = save_meter_data_and_bill(meter_id, day_value, night_value)
            print(f"Processed: {data} -> {result}")
        time.sleep(1)  # Перевіряємо чергу кожну секунду

# Запускаємо генератор і обробник у окремих потоках
if __name__ == "__main__":
    generator_thread = threading.Thread(target=generate_test_data)
    processor_thread = threading.Thread(target=process_queue)

    generator_thread.start()
    processor_thread.start()

    generator_thread.join()
    processor_thread.join()