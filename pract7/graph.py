# graph.py

import tkinter as tk

class GraphWindow:
    def __init__(self, maze, entrance, foods, all_routes, update_callback, margin=5):
        self.maze            = maze
        self.entrance        = entrance
        self.foods           = list(foods)
        self.routes          = all_routes
        self.update_callback = update_callback

        self.rows = len(maze)
        self.cols = len(maze[0])
        self.margin    = margin
        self.cell_size = 1
        self.offset_x  = margin
        self.offset_y  = margin
        self.hover_cell = None

        self.root   = tk.Tk()
        self.root.title("Vehicle Routing ACO")
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Події
        self.canvas.bind("<Configure>",   self._on_resize)
        self.canvas.bind("<Motion>",      self._on_motion)
        self.canvas.bind("<Leave>",       self._on_leave)
        self.canvas.bind("<Button-1>",    self._on_left_click)
        self.canvas.bind("<Button-3>",    self._on_right_click)

        self._draw_all()

    def _cell_from_xy(self, x, y):
        col = (x - self.offset_x) // self.cell_size
        row = (y - self.offset_y) // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None

    def _on_left_click(self, event):
        cell = self._cell_from_xy(event.x, event.y)
        if cell and self.maze[cell[0]][cell[1]] == 0 and cell not in self.foods:
            self.foods.append(cell)
            self.routes = self.update_callback(self.maze, self.foods)
            self._draw_all()

    def _on_right_click(self, event):
        cell = self._cell_from_xy(event.x, event.y)
        if cell and cell in self.foods:
            self.foods.remove(cell)
            self.routes = self.update_callback(self.maze, self.foods)
            self._draw_all()

    def _on_motion(self, event):
        new_hover = self._cell_from_xy(event.x, event.y)
        if new_hover != self.hover_cell:
            self.hover_cell = new_hover
            self._draw_all()

    def _on_leave(self, event):
        if self.hover_cell is not None:
            self.hover_cell = None
            self._draw_all()

    def _on_resize(self, event):
        w = event.width  - 2 * self.margin
        h = event.height - 2 * self.margin
        self.cell_size = min(w // self.cols, h // self.rows)
        self.offset_x  = (event.width  - self.cell_size * self.cols) // 2
        self.offset_y  = (event.height - self.cell_size * self.rows) // 2
        self._draw_all()

    def _draw_all(self):
        self.canvas.delete("all")
        cs = self.cell_size

        # Малюємо лабіринт
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = self.offset_x + c * cs
                y1 = self.offset_y + r * cs
                x2, y2 = x1 + cs, y1 + cs
                color = "white" if self.maze[r][c] == 0 else "black"

                # підсвітка під курсором
                if self.hover_cell == (r, c):
                    color = "#cccccc" if color=="white" else "#333333"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        # Точки доставки
        for fx, fy in self.foods:
            x1 = self.offset_x + fy * cs
            y1 = self.offset_y + fx * cs
            self.canvas.create_rectangle(x1, y1, x1 + cs, y1 + cs, fill="yellow", outline="")

        # Вхід
        er, ec = self.entrance
        x1 = self.offset_x + ec * cs
        y1 = self.offset_y + er * cs
        self.canvas.create_rectangle(x1, y1, x1 + cs, y1 + cs, fill="green", outline="")

        # Маршрути
        colors = ["red", "blue", "cyan", "magenta", "orange", "lime"]
        for k, route in enumerate(self.routes):
            col = colors[k % len(colors)]
            for (r1, c1), (r2, c2) in zip(route, route[1:]):
                x1 = self.offset_x + c1 * cs + cs//2
                y1 = self.offset_y + r1 * cs + cs//2
                x2 = self.offset_x + c2 * cs + cs//2
                y2 = self.offset_y + r2 * cs + cs//2
                self.canvas.create_line(x1, y1, x2, y2, fill=col, width=2)

    def run(self):
        self.root.mainloop()
