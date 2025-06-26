# graph.py

import tkinter as tk

class GraphWindow:
    def __init__(self, maze, entrance, foods, best_paths, update_callback, margin=20):
        self.maze = maze
        self.entrance = entrance
        self.foods = foods
        self.best_paths = best_paths
        self.update_callback = update_callback
        self.rows = len(maze)
        self.cols = len(maze[0])
        self.margin = margin
        self.cell_size = 1
        self.offset_x = margin
        self.offset_y = margin
        self.hover_cell = None

        self.root = tk.Tk()
        self.root.title("ACO Maze")
        self.canvas = tk.Canvas(self.root, bg="lightgrey")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)

    def _get_cell(self, x, y):
        """Повертає (row, col) клітинку під координатами миші або None."""
        col = (x - self.offset_x) // self.cell_size
        row = (y - self.offset_y) // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None

    def _on_left_click(self, event):
        cell = self._get_cell(event.x, event.y)
        if cell and self.maze[cell[0]][cell[1]] == 0 and cell not in self.foods:
            self.foods.append(cell)
            self.best_paths, self.entrance = self.update_callback(self.maze, self.foods)
            self._redraw()

    def _on_right_click(self, event):
        cell = self._get_cell(event.x, event.y)
        if cell and cell in self.foods:
            self.foods.remove(cell)
            self.best_paths, self.entrance = self.update_callback(self.maze, self.foods)
            self._redraw()

    def _on_motion(self, event):
        cell = self._get_cell(event.x, event.y)
        if cell != self.hover_cell:
            self.hover_cell = cell
            self._redraw()

    def _on_leave(self, event):
        self.hover_cell = None
        self._redraw()

    def _on_resize(self, event):
        w = event.width - 2 * self.margin
        h = event.height - 2 * self.margin
        self.cell_size = min(w // self.cols, h // self.rows)
        self.offset_x = (event.width - self.cell_size * self.cols) // 2
        self.offset_y = (event.height - self.cell_size * self.rows) // 2
        self._redraw()

    def _redraw(self):
        self.canvas.delete("all")
        self._draw_static()
        self._draw_paths()

    def _draw_static(self):
        cs = self.cell_size
        for i in range(self.rows):
            for j in range(self.cols):
                x1 = self.offset_x + j * cs
                y1 = self.offset_y + i * cs
                x2 = x1 + cs
                y2 = y1 + cs
                base_color = "black" if self.maze[i][j] else "white"
                # затемнення при наведенні
                if self.hover_cell == (i, j):
                    if base_color == "white":
                        base_color = "#cccccc"
                    elif base_color == "black":
                        base_color = "#333333"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=base_color, outline="")

        # малюємо їжу
        for fx, fy in self.foods:
            x1 = self.offset_x + fy * cs
            y1 = self.offset_y + fx * cs
            x2 = x1 + cs
            y2 = y1 + cs
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", outline="")

        # малюємо вхід
        ex, ey = self.entrance
        x1 = self.offset_x + ey * cs
        y1 = self.offset_y + ex * cs
        x2 = x1 + cs
        y2 = y1 + cs
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="green", outline="")

    def _draw_paths(self):
        cs = self.cell_size
        colors = ["blue", "red", "purple", "orange", "cyan", "magenta"]
        for idx, food in enumerate(self.foods):
            p_up, p_down, _ = self.best_paths.get(food, ([], [], 0))
            col = colors[idx % len(colors)]
            # шлях туди
            for i in range(len(p_up) - 1):
                u = p_up[i]
                v = p_up[i + 1]
                x1 = self.offset_x + u[1] * cs + cs // 2
                y1 = self.offset_y + u[0] * cs + cs // 2
                x2 = self.offset_x + v[1] * cs + cs // 2
                y2 = self.offset_y + v[0] * cs + cs // 2
                self.canvas.create_line(x1, y1, x2, y2, fill=col, width=2)
            # шлях назад (пунктир)
            for i in range(len(p_down) - 1):
                u = p_down[i]
                v = p_down[i + 1]
                x1 = self.offset_x + u[1] * cs + cs // 2
                y1 = self.offset_y + u[0] * cs + cs // 2
                x2 = self.offset_x + v[1] * cs + cs // 2
                y2 = self.offset_y + v[0] * cs + cs // 2
                self.canvas.create_line(x1, y1, x2, y2, dash=(4, 2), fill=col, width=2)

    def run(self):
        self.root.mainloop()
