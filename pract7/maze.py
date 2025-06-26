#maze.py
import random
from collections import deque

def generate_maze(n, m):
    if n % 2 == 0: n -= 1
    if m % 2 == 0: m -= 1

    maze = [[1]*m for _ in range(n)]

    def carve(x, y, visited):
        dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < n-1 and 1 <= ny < m-1 and (nx, ny) not in visited:
                maze[nx][ny] = 0
                maze[x + dx//2][y + dy//2] = 0
                visited.add((nx, ny))
                carve(nx, ny, visited)

        if random.random() < 0.3:
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < n-1 and 1 <= ny < m-1 and maze[nx][ny] == 1:
                    next_nx, next_ny = nx + dx, ny + dy
                    if 0 <= next_nx < n and 0 <= next_ny < m and maze[next_nx][next_ny] == 0:
                        maze[nx][ny] = 0
                        maze[x + dx//2][y + dy//2] = 0

    sx = random.randrange(1, n-1, 2)
    sy = random.randrange(1, m-1, 2)
    maze[sx][sy] = 0
    carve(sx, sy, {(sx, sy)})

    walls = []
    for i in range(1, n-1):
        for j in range(1, m-1):
            if maze[i][j] == 1:
                neighbors = [(i+di, j+dj) for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
                open_neighbors = sum(1 for ni, nj in neighbors if 0 <= ni < n and 0 <= nj < m and maze[ni][nj] == 0)
                if open_neighbors == 2:
                    walls.append((i, j))
    random.shuffle(walls)
    for i, j in walls[:len(walls)//6]:
        maze[i][j] = 0

    perimeter = [(0,j) for j in range(1,m-1)] + [(n-1,j) for j in range(1,m-1)] + \
                [(i,0) for i in range(1,n-1)] + [(i,m-1) for i in range(1,n-1)]
    random.shuffle(perimeter)
    for ex, ey in perimeter:
        dx = 1 if ex == 0 else -1 if ex == n-1 else 0
        dy = 1 if ey == 0 else -1 if ey == m-1 else 0
        if maze[ex+dx][ey+dy] == 0:
            maze[ex][ey] = 0
            break

    return maze

def place_customers(maze, count):
    n, m = len(maze), len(maze[0])
    entrance = None
    for i in range(n):
        for j in range(m):
            if (i in (0, n-1) or j in (0, m-1)) and maze[i][j] == 0:
                entrance = (i, j)
                break
        if entrance:
            break

    reachable = set()
    queue = deque([entrance])
    visited = {entrance}
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        x, y = queue.popleft()
        reachable.add((x, y))
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and maze[nx][ny] == 0 and (nx, ny) not in visited:
                queue.append((nx, ny))
                visited.add((nx, ny))

    # Виключаємо клітинку входу зі списку можливих позицій для їжі
    free = [cell for cell in reachable if cell != entrance]
    random.shuffle(free)
    # Повертаємо не більше, ніж count клітинок, і не більше, ніж є доступних
    return free[:min(count, len(free))]