# ants.py

import random
from collections import defaultdict

class Ant:
    def __init__(self, start, goal, maze, pheromones, alpha=1.0, beta=2.0):
        self.start = start
        self.goal = goal
        self.maze = maze
        self.pheromones = pheromones
        self.alpha = alpha
        self.beta = beta
        self.path = [start]
        self.visited = {start}

    def _neighbors(self, u):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        nbs = []
        x, y = u
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(self.maze) and 0 <= ny < len(self.maze[0]) and self.maze[nx][ny] == 0:
                nbs.append((nx, ny))
        return nbs

    def build_path(self):
        current = self.start
        while current != self.goal:
            # спочатку ходимо по не відвіданим сусідам, інакше — по всім
            nbs = [v for v in self._neighbors(current) if v not in self.visited]
            if not nbs:
                nbs = self._neighbors(current)
            # обчислюємо ймовірності за феромонами та евристикою
            weights = []
            for v in nbs:
                τ = self.pheromones[(current, v)]
                η = 1.0  # можна модифікувати під евристичну інформацію
                weights.append((τ ** self.alpha) * (η ** self.beta))
            total = sum(weights)
            probs = [w / total for w in weights]
            # вибір наступної клітинки
            nxt = random.choices(nbs, weights=probs)[0]
            self.path.append(nxt)
            self.visited.add(nxt)
            current = nxt
        return self.path

    def path_length(self):
        # кількість кроків — довжина шляху мінус 1
        return len(self.path) - 1


class AntColony:
    def __init__(self, maze, start, goal,
                 num_ants=50, num_iters=100,
                 alpha=1.0, beta=2.0, rho=0.1, Q=100.0):
        self.maze = maze
        self.start = start
        self.goal = goal
        self.num_ants = num_ants
        self.num_iters = num_iters
        self.alpha = alpha
        self.beta = beta
        self.rho = rho  # коефіцієнт випаровування
        self.Q = Q      # кількість стартового феромону
        # словник феромонів із початковим значенням 1.0 на кожному ребрі
        self.pheromones = defaultdict(lambda: 1.0)
        self.best_path = None
        self.best_len = float('inf')

    def run(self):
        for _ in range(self.num_iters):
            all_paths = []
            # кожна ітерація — рух num_ants мурах
            for _ in range(self.num_ants):
                ant = Ant(self.start, self.goal, self.maze, self.pheromones,
                          alpha=self.alpha, beta=self.beta)
                path = ant.build_path()
                L = ant.path_length()
                all_paths.append((path, L))
                # оновлюємо найкращий знайдений шлях
                if L < self.best_len:
                    self.best_len = L
                    self.best_path = path
            # випаровування феромону
            for edge in list(self.pheromones.keys()):
                self.pheromones[edge] *= (1.0 - self.rho)
            # нові веромони на всі шляхи
            for path, L in all_paths:
                δ = self.Q / L
                for i in range(len(path) - 1):
                    u = path[i]
                    v = path[i + 1]
                    self.pheromones[(u, v)] += δ
                    self.pheromones[(v, u)] += δ
        return self.best_path, self.best_len
