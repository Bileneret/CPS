import unittest
import os
import json
from maze import generate_maze, place_customers
from ants import AntColonyVRP, bfs_path
from main import find_entrance, save_maze, load_maze, save_paths

class TestAntColonyVRP(unittest.TestCase):
    def setUp(self):
        self.n, self.m = 9, 9
        self.maze = generate_maze(self.n, self.m)
        self.foods = place_customers(self.maze, 3)
        self.entrance = find_entrance(self.maze)
        self.colony = AntColonyVRP(
            self.maze,
            self.entrance,
            self.foods,
            num_vehicles=2,
            num_ants=5,
            num_iters=10
        )

    def tearDown(self):
        for file in ["maze.json", "best_vrp_paths.json"]:
            if os.path.exists(file):
                os.remove(file)

    def test_initial_pheromone_matrix(self):
        """Тест 1: Ініціалізація феромонів — всі значення повинні бути позитивними"""
        for row in self.colony.pher:
            for value in row:
                self.assertGreater(value, 0, "Феромон повинен бути додатнім числом")

    def test_path_construction(self):
        """Тест 2: Мураха будує маршрут, який починається і закінчується у вході"""
        routes = self.colony._construct_route()
        for tour in routes:
            self.assertEqual(tour[0], 0, "Кожен маршрут має починатися у вході (індекс 0)")
            self.assertEqual(tour[-1], 0, "Кожен маршрут має закінчуватися у вході (індекс 0)")

    def test_valid_path_cells(self):
        """Тест 3: Усі шляхи прокладаються по прохідним клітинкам"""
        for i in range(len(self.colony.points)):
            for j in range(len(self.colony.points)):
                if i != j:
                    path = self.colony.paths[i][j]
                    for x, y in path:
                        self.assertEqual(self.maze[x][y], 0, "Шлях має йти по прохідних клітинках")

    def test_pheromone_update(self):
        """Тест 4: Після виконання run феромони оновлюються"""
        before = [row[:] for row in self.colony.pher]
        self.colony.run()
        after = self.colony.pher
        different = any(before[i][j] != after[i][j] for i in range(len(before)) for j in range(len(before)))
        self.assertTrue(different, "Матриця феромонів має оновлюватися після run()")

    def test_run_returns_valid_routes(self):
        """Тест 5: Результат run — це список списків координат, що формують допустимі маршрути"""
        routes = self.colony.run()
        self.assertIsInstance(routes, list)
        for route in routes:
            self.assertIsInstance(route, list)
            for cell in route:
                x, y = cell
                self.assertTrue(0 <= x < self.n and 0 <= y < self.m, "Координати мають бути в межах лабіринту")

    def test_save_and_load_maze(self):
        """Тест 6: Перевірка збереження та завантаження лабіринту"""
        save_maze(self.maze, self.foods)
        loaded_maze, loaded_foods = load_maze()
        self.assertEqual(self.maze, loaded_maze, "Збережений лабіринт має збігатися з завантаженим")
        self.assertEqual(self.foods, loaded_foods, "Їжа має збігатися з завантаженою")

    def test_save_paths(self):
        """Тест 7: Збереження результатів"""
        all_routes = self.colony.run()
        save_paths(all_routes)
        self.assertTrue(os.path.exists("best_vrp_paths.json"), "Файл best_vrp_paths.json має бути створено")

if __name__ == "__main__":
    unittest.main()
