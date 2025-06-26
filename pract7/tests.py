import unittest
import json
import os
from maze import generate_maze, place_customers
from ants import Ant, AntColony
from main import find_entrance, save_maze, load_maze, save_paths
from unittest.mock import patch
from collections import defaultdict

class TestMazeProject(unittest.TestCase):
    def setUp(self):
        # Виконується перед кожним тестом для ініціалізації спільних даних
        self.n, self.m = 5, 7  # Невеликий лабіринт для тестів
        self.maze = generate_maze(self.n, self.m)  # Генеруємо лабіринт
        self.food_count = 2  # Кількість шматочків їжі
        self.foods = place_customers(self.maze, self.food_count)  # Розміщуємо їжу
        self.entrance = find_entrance(self.maze)  # Знаходимо вхід

    def tearDown(self):
        # Виконується після кожного тесту для очищення
        # Видаляємо тестові файли, якщо вони створені
        for file in ["maze.json", "best_ant_paths.json"]:
            if os.path.exists(file):
                os.remove(file)

    def test_generate_maze_dimensions(self):
        # Тест: Перевіряємо розмір згенерованого лабіринту
        # Очікуємо, що розміри будуть нечетними (n, m корегуються в generate_maze)
        maze = generate_maze(6, 8)  # Вводимо парні, але мають стати нечетними (5x7)
        self.assertEqual(len(maze), 5, "Висота лабіринту має бути 5")
        self.assertEqual(len(maze[0]), 7, "Ширина лабіринту має бути 7")

    def test_generate_maze_walls_and_paths(self):
        # Тест: Перевіряємо, що лабіринт містить стіни (1) та проходи (0)
        maze = self.maze
        has_walls = False
        has_paths = False
        for row in maze:
            for cell in row:
                if cell == 1:
                    has_walls = True
                elif cell == 0:
                    has_paths = True
        self.assertTrue(has_walls, "Лабіринт має містити стіни")
        self.assertTrue(has_paths, "Лабіринт має містити проходи")

    def test_generate_maze_entrance(self):
        # Тест: Перевіряємо, що лабіринт має принаймні один вхід на периметрі
        maze = self.maze
        n, m = len(maze), len(maze[0])
        has_entrance = False
        for i in range(n):
            for j in range(m):
                if (i in (0, n-1) or j in (0, m-1)) and maze[i][j] == 0:
                    has_entrance = True
                    break
            if has_entrance:
                break
        self.assertTrue(has_entrance, "Лабіринт має мати вхід на периметрі")

    def test_place_customers_count(self):
        # Тест: Перевіряємо, що кількість розміщеної їжі не перевищує задану
        foods = self.foods
        self.assertLessEqual(len(foods), self.food_count, "Кількість їжі не має перевищувати задану")
        # Перевіряємо, що їжа розміщена в прохідних клітинках
        for fx, fy in foods:
            self.assertEqual(self.maze[fx][fy], 0, "Їжа має бути в прохідній клітинці")

    def test_place_customers_no_entrance(self):
        # Тест: Перевіряємо, що їжа не розміщується у клітинці входу
        foods = self.foods
        entrance = self.entrance
        self.assertNotIn(entrance, foods, "Їжа не має бути розміщена у вході")

    def test_find_entrance(self):
        # Тест: Перевіряємо, що функція find_entrance знаходить коректний вхід
        entrance = self.entrance
        self.assertIsNotNone(entrance, "Вхід має бути знайдено")
        self.assertEqual(self.maze[entrance[0]][entrance[1]], 0, "Вхід має бути прохідною клітинкою")
        n, m = len(self.maze), len(self.maze[0])
        self.assertTrue(entrance[0] in (0, n-1) or entrance[1] in (0, m-1), "Вхід має бути на периметрі")

    def test_ant_colony_run(self):
        # Тест: Перевіряємо, що мурашина колонія повертає коректний шлях
        food = self.foods[0]
        colony = AntColony(self.maze, self.entrance, food, num_ants=5, num_iters=10)
        path, length = colony.run()
        self.assertEqual(path[0], self.entrance, "Шлях має починатися з входу")
        self.assertEqual(path[-1], food, "Шлях має закінчуватися в їжі")
        self.assertEqual(length, len(path) - 1, "Довжина шляху має відповідати кількості кроків")
        # Перевіряємо, що шлях коректний (усі клітинки — проходи)
        for x, y in path:
            self.assertEqual(self.maze[x][y], 0, "Шлях має йти через прохідні клітинки")

    def test_save_and_load_maze(self):
        # Тест: Перевіряємо збереження та завантаження лабіринту
        save_maze(self.maze, self.foods)
        loaded_maze, loaded_foods = load_maze()
        self.assertEqual(self.maze, loaded_maze, "Завантажений лабіринт має збігатися з оригіналом")
        self.assertEqual(self.foods, loaded_foods, "Завантажена їжа має збігатися з оригіналом")
        self.assertTrue(os.path.exists("maze.json"), "Файл maze.json має бути створено")

    def test_save_paths(self):
        # Тест: Перевіряємо збереження шляхів мурашиної колонії
        best_paths = {
            self.foods[0]: ([self.entrance, self.foods[0]], [self.foods[0], self.entrance], 2)
        }
        save_paths(best_paths)
        self.assertTrue(os.path.exists("best_ant_paths.json"), "Файл best_ant_paths.json має бути створено")
        with open("best_ant_paths.json", "r") as f:
            data = json.load(f)
            key = f"{self.foods[0][0]},{self.foods[0][1]}"
            self.assertIn(key, data, "Координати їжі мають бути в збереженому файлі")
            self.assertEqual(data[key]["length"], 2, "Довжина шляху має бути збережено коректно")

    @patch('builtins.input', side_effect=['20x30', '3'])
    def test_get_user_input(self, mock_input):
        # Тест: Перевіряємо введення розміру лабіринту користувачем
        from main import get_user_input
        n, m = get_user_input()
        self.assertEqual(n, 20, "Введена висота має бути 20")
        self.assertEqual(m, 30, "Введена ширина має бути 30")

    @patch('builtins.input', side_effect=['5'])
    def test_get_food_count(self, mock_input):
        # Тест: Перевіряємо введення кількості їжі користувачем
        from main import get_food_count
        count = get_food_count()
        self.assertEqual(count, 5, "Введена кількість їжі має бути 5")

if __name__ == '__main__':
    unittest.main()