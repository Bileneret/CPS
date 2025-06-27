# ants.py

import random
from collections import defaultdict, deque

# ── Глобальні налаштування алгоритму ────────────────────────────────────────

NUM_VEHICLES = 0

# Класичні параметри ACO
ALPHA                = 0.5    # вплив феромону. 0 - не впливає, 1 - максимальний вплив.
BETA                 = 0.5    # вплив евристики. 0 - не впилває, 1 - найкоротші шляхи.
RHO                  = 0.3    # швидкість випаровування.
Q                     = 100.0  # сума феромону, чим більше - тим швидше сходиться колонія.

# Стохастика при виборі: з ймовірністю вибираємо випадкового сусіда
EPSILON_RANDOM_CHOICE = 0.2

# Початковий феромон:
# якщо None — використовуємо 1.0. 
INITIAL_PHEROMONE     = None  

# ────────────────────────────────────────────────────────────────────────────

# Допоміжні константи
DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def bfs_path(maze, start, goal):
    """
    BFS у лабіринті (4‐сусіди), повертає найкоротший шлях як список (row,col).
    """
    q = deque([start])
    parents = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            # реконструюємо шлях
            path = []
            p = cur
            while p is not None:
                path.append(p)
                p = parents[p]
            return list(reversed(path))
        for dx, dy in DIRS:
            nxt = (cur[0]+dx, cur[1]+dy)
            if (0 <= nxt[0] < len(maze) and
                0 <= nxt[1] < len(maze[0]) and
                maze[nxt[0]][nxt[1]] == 0 and
                nxt not in parents):
                parents[nxt] = cur
                q.append(nxt)
    return []

class AntColonyVRP:
    def __init__(self,
                 maze,
                 entrance,
                 foods,
                 num_vehicles = NUM_VEHICLES,
                 num_ants=30,
                 num_iters=100,
                 alpha=ALPHA,
                 beta=BETA,
                 rho=RHO,
                 Q=Q,
                 epsilon=EPSILON_RANDOM_CHOICE,
                 init_pheromone=INITIAL_PHEROMONE):
        """
        maze          : 2D список 0/1
        entrance      : кортеж (row, col)
        foods         : список кортежів точок доставки
        num_vehicles  : кількість маршрутів/машин
        num_ants      : кількість мурах
        num_iters     : кількість ітерацій алгоритму
        alpha, beta   : вплив феромону/евристики
        rho           : коефіцієнт випаровування
        Q             : сума феромону за тур
        epsilon       : ймовірність випадкового кроку
        init_pheromone: початкове значення феромону (None → 1.0)
        """
        self.maze        = maze
        self.entrance    = entrance
        self.foods       = list(foods)
        self.K           = num_vehicles
        self.num_ants    = num_ants
        self.num_iters   = num_iters
        self.alpha       = alpha
        self.beta        = beta
        self.rho         = rho
        self.Q           = Q
        self.epsilon     = epsilon

        # Всі ключові точки: 0 = entrance, далі foods
        self.points = [entrance] + self.foods
        self.n      = len(self.points)

        # Матриці відстаней (в кроках) та фактичних шляхів між точками
        self.dist  = [[0]*self.n for _ in range(self.n)]
        self.paths = [[[] for _ in range(self.n)] for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    p = bfs_path(maze, self.points[i], self.points[j])
                    self.paths[i][j] = p
                    self.dist[i][j]  = len(p)-1

        # Ініціалізація феромонів
        init_val = init_pheromone if init_pheromone is not None else 1.0
        self.pher = [[init_val]*self.n for _ in range(self.n)]

    def _construct_route(self):
        """
        Одна мураха будує маршрути для K машин:
        1) Рандомно розбиваємо індекси food між K груп
        2) Для кожної групи будуємо тур (0 → підгрупа → 0)
        """
        # 1) випадковий розподіл точок між K машин
        idxs = list(range(1, self.n))
        random.shuffle(idxs)
        groups = [idxs[i::self.K] for i in range(self.K)]

        all_tours = []
        for group in groups:
            tour = [0]
            unvis = set(group)
            while unvis:
                cur = tour[-1]
                # ε-жадібність: з epsilon ймовірністю випадковий вибір
                if random.random() < self.epsilon:
                    nxt = random.choice(list(unvis))
                else:
                    # ACO‐вибір за τ^α * η^β
                    weights = []
                    for j in unvis:
                        τ = self.pher[cur][j] ** self.alpha
                        η = (1.0 / self.dist[cur][j]) ** self.beta if self.dist[cur][j]>0 else 0
                        weights.append(τ * η)
                    total = sum(weights) or 1e-9
                    probs = [w/total for w in weights]
                    nxt = random.choices(list(unvis), weights=probs, k=1)[0]
                tour.append(nxt)
                unvis.remove(nxt)
            tour.append(0)
            all_tours.append(tour)
        return all_tours

    def run(self):
        best_routes = None
        best_cost   = float('inf')

        for it in range(1, self.num_iters+1):
            generation = []
            costs      = []
            # Кожна мураха — один варіант розбиття+маршрутів
            for _ in range(self.num_ants):
                routes = self._construct_route()
                cost = 0
                for tour in routes:
                    for u,v in zip(tour, tour[1:]):
                        cost += self.dist[u][v]
                generation.append(routes)
                costs.append(cost)
                if cost < best_cost:
                    best_cost   = cost
                    best_routes = routes

            # 2) Випаровування
            for i in range(self.n):
                for j in range(self.n):
                    self.pher[i][j] *= (1 - self.rho)

            # 3) Внесок феромону
            for routes, cost in zip(generation, costs):
                δ = self.Q / (cost + 1e-9)
                for tour in routes:
                    for u,v in zip(tour, tour[1:]):
                        self.pher[u][v] += δ
                        self.pher[v][u] += δ

            # print(f"Iter {it}/{self.num_iters} — best cost: {best_cost}")

        # Після завершення: конструюємо реальні клітинні маршрути
        result = []
        for tour in best_routes:
            cells = []
            for u,v in zip(tour, tour[1:]):
                segment = self.paths[u][v]
                if cells:
                    segment = segment[1:]  # уникаємо дублювання
                cells += segment
            result.append(cells)

        print(f"Best cost: {best_cost:.2f}  (за {self.num_iters} ітерацій, {self.num_ants} мурах)")
        return result
