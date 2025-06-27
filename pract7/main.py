# main.py

import json
from maze import generate_maze, place_customers
from ants import AntColonyVRP
from graph import GraphWindow

MAZE_FILE    = "maze.json"
SAVE_FILE    = "best_vrp_paths.json"
NUM_VEHICLES = 1  # кількість машин для задачі

def get_user_input():
    while True:
        try:
            txt = input("Розмір лабіринту NxM (наприклад 20x30): ")
            n, m = map(int, txt.replace('*','x').split('x'))
            return n, m
        except:
            print("Некоректне введення. Спробуйте ще раз.")

def get_food_count():
    while True:
        try:
            cnt = int(input("Кількість точок доставки (їжі): "))
            return cnt
        except:
            print("Некоректне введення. Спробуйте ще раз.")

def get_ants_iters():
    while True:
        try:
            a = int(input("Кількість мурах (num_ants): "))
            i = int(input("Кількість ітерацій (num_iters): "))
            return a, i
        except:
            print("Некоректно, введіть два цілих числа.")

def find_entrance(maze):
    n, m = len(maze), len(maze[0])
    # шукаємо будь–яку клітинку 0 по периметру
    for j in range(m):
        if maze[0][j] == 0:    return (0, j)
        if maze[n-1][j] == 0:  return (n-1, j)
    for i in range(n):
        if maze[i][0] == 0:    return (i, 0)
        if maze[i][m-1] == 0:  return (i, m-1)
    raise RuntimeError("Вхід не знайдено")

def load_maze():
    try:
        with open(MAZE_FILE, "r") as f:
            data = json.load(f)
        maze = data["maze"]
        # конвертуємо списки у кортежі, щоб вони були hashable
        foods = [tuple(c) for c in data.get("customers", [])]
        return maze, foods
    except:
        return None, None

def save_maze(maze, foods):
    with open(MAZE_FILE, "w") as f:
        # зберігаємо кортежі як списки
        json.dump({"maze": maze, "customers": [list(c) for c in foods]}, f)

def save_paths(all_routes):
    """
    all_routes: список маршрутів клітинок для кожного автомобіля
    """
    with open(SAVE_FILE, "w") as f:
        json.dump({"routes": all_routes}, f)

def main():
    # 1) Завантаж чи згенеруй лабіринт + точки доставки
    choice = input("Завантажити готовий лабіринт? (+/-): ").strip()
    if choice == "+":
        maze, foods = load_maze()
        if maze is None:
            print("Файл не знайдено, генеруємо новий.")
            choice = "-"
    if choice == "-":
        n, m = get_user_input()
        cnt = get_food_count()
        maze = generate_maze(n, m)
        foods = place_customers(maze, cnt)
        save_maze(maze, foods)

    entrance = find_entrance(maze)
    print(f"Лабіринт: {len(maze)}×{len(maze[0])}, точок доставки: {len(foods)}")

    # 1а) Запитуємо параметри мурашиного алгоритму
    num_ants, num_iters = get_ants_iters()
    print(f"Запуск ACO: мурах={num_ants}, ітерацій={num_iters}, машин={NUM_VEHICLES}")

    # 2) Запускаємо VRP через ACO
    vrp = AntColonyVRP(
        maze, entrance, foods,
        num_vehicles=NUM_VEHICLES,
        num_ants=num_ants,
        num_iters=num_iters
    )
    all_routes = vrp.run()
    save_paths(all_routes)

    # 3) Візуалізація з інтерактивним додаванням/видаленням точок
    app = GraphWindow(
        maze,
        entrance,
        foods,
        all_routes,
        update_callback=lambda mz, fs: AntColonyVRP(
            mz, entrance, fs,
            num_vehicles=NUM_VEHICLES,
            num_ants=num_ants,
            num_iters=num_iters
        ).run()
    )
    app.run()

if __name__ == "__main__":
    main()
