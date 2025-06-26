# main.py

import json
from maze import generate_maze, place_customers
from ants import AntColony
from graph import GraphWindow

MAZE_FILE = "maze.json"
SAVE_FILE = "best_ant_paths.json"

def get_user_input():
    while True:
        try:
            txt = input("Введіть розмір лабіринту NxM (наприклад 20x30): ").lower()
            n, m = map(int, txt.replace('*','x').split('x'))
            return n, m
        except:
            print("Некоректне введення. Спробуйте знову.")

def get_food_count():
    while True:
        try:
            cnt = int(input("Введіть кількість шматочків їжі: "))
            return cnt
        except:
            print("Некоректне введення. Спробуйте знову.")

def find_entrance(maze):
    n, m = len(maze), len(maze[0])
    # перевіряємо верхній і нижній ряд
    for j in range(m):
        if maze[0][j] == 0:
            return (0, j)
        if maze[n-1][j] == 0:
            return (n-1, j)
    # лівий і правий стовпець
    for i in range(n):
        if maze[i][0] == 0:
            return (i, 0)
        if maze[i][m-1] == 0:
            return (i, m-1)
    raise ValueError("Вхід не знайдено")

def load_maze():
    try:
        with open(MAZE_FILE, "r") as f:
            data = json.load(f)
            return data["maze"], [tuple(c) for c in data.get("customers", [])]
    except:
        return None, None

def save_maze(maze, foods):
    with open(MAZE_FILE, "w") as f:
        json.dump({"maze": maze, "customers": foods}, f)

def save_paths(best_paths):
    out = {}
    for food, (p_up, p_down, L) in best_paths.items():
        key = f"{food[0]},{food[1]}"
        out[key] = {"up": p_up, "down": p_down, "length": L}
    with open(SAVE_FILE, "w") as f:
        json.dump(out, f)

def run_ant_colony_for_all(maze, foods):
    entrance = find_entrance(maze)
    best_paths = {}
    for food in foods:
        colony = AntColony(maze, entrance, food)
        path_up, length = colony.run()
        path_down = path_up[::-1]
        full_length = length * 2
        best_paths[food] = (path_up, path_down, full_length)
        print(f"Їжа {food} — туди {length} кроків, назад ще {length}, всього {full_length}")
    save_paths(best_paths)
    return best_paths, entrance

def main():
    choice = input("Завантажити готовий лабіринт? (+/-): ").strip()
    if choice == "+":
        maze, foods = load_maze()
        if maze is None:
            print("Файл не знайдено, згенеруємо заново.")
            choice = "-"

    if choice == "-":
        n, m = get_user_input()
        cnt = get_food_count()
        maze = generate_maze(n, m)
        foods = place_customers(maze, cnt)

    print(f"Лабіринт розміром {len(maze)}×{len(maze[0])}, їжі: {len(foods)}")
    save_maze(maze, foods)

    best_paths, entrance = run_ant_colony_for_all(maze, foods)

    app = GraphWindow(maze, entrance, foods, best_paths, update_callback=run_ant_colony_for_all)
    app.run()

if __name__ == "__main__":
    main()
