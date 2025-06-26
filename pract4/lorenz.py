import numpy as np
import ctypes
from OpenGL.GL import *
import pyrr

# Параметри за замовчуванням
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0
dt = 0.01
points = []

# Ініціалізація OpenGL
_vao = None
_vbo = None

def init_gl():
    global _vao, _vbo
    _vao = glGenVertexArrays(1)
    glBindVertexArray(_vao)

    _vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, _vbo)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * ctypes.sizeof(ctypes.c_float), ctypes.c_void_p(0))

    glBindVertexArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

def update_points(x, y, z, sigma, rho, beta, dt):
    global points
    k1x, k1y, k1z = lorenz_equations(x, y, z, sigma, rho, beta)
    k2x, k2y, k2z = lorenz_equations(x + 0.5 * dt * k1x, y + 0.5 * dt * k1y, z + 0.5 * dt * k1z, sigma, rho, beta)
    k3x, k3y, k3z = lorenz_equations(x + 0.5 * dt * k2x, y + 0.5 * dt * k2y, z + 0.5 * dt * k2z, sigma, rho, beta)
    k4x, k4y, k4z = lorenz_equations(x + dt * k3x, y + dt * k3y, z + dt * k3z, sigma, rho, beta)
    
    x_new = x + (dt / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
    y_new = y + (dt / 6.0) * (k1y + 2 * k2y + 2 * k3y + k4y)
    z_new = z + (dt / 6.0) * (k1z + 2 * k2z + 2 * k3z + k4z)
    
    points.append([x_new, y_new, z_new])
    # Видалено обмеження max_points
    return x_new, y_new, z_new

def lorenz_equations(x, y, z, sigma, rho, beta):
    dx_dt = sigma * (y - x)
    dy_dt = x * (rho - z) - y
    dz_dt = x * y - beta * z
    return dx_dt, dy_dt, dz_dt

class LorenzAttractor:
    def __init__(self, position, sigma=10.0, rho=28.0, beta=8.0/3.0, dt=0.01, max_points=None, color=(1.0, 0.0, 0.0)):
        self.position = np.array(position, dtype=np.float32)
        self.sigma = sigma
        self.rho = rho
        self.beta = beta
        self.dt = dt
        self.max_points = max_points  # max_points більше не використовується як обмеження
        self.color = color
        self.x, self.y, self.z = 1.0, 1.0, 1.0  # Початкові умови
        global points
        points = []
        for _ in range(10):  # Ініціалізація початкових точок
            self.x, self.y, self.z = update_points(self.x, self.y, self.z, self.sigma, self.rho, self.beta, self.dt)

    def update(self):
        self.x, self.y, self.z = update_points(self.x, self.y, self.z, self.sigma, self.rho, self.beta, self.dt)

    def draw_gl(self, view, projection, shader_program):
        global points
        model = pyrr.matrix44.create_from_translation(self.position)
        glUseProgram(shader_program)
        for name, mat in (("model", model), ("view", view), ("projection", projection)):
            loc = glGetUniformLocation(shader_program, name)
            glUniformMatrix4fv(loc, 1, GL_FALSE, mat)
        loc = glGetUniformLocation(shader_program, "color")
        glUniform3f(loc, *self.color)

        if points:
            vertices = np.array(points, dtype=np.float32).flatten()
            glBindVertexArray(_vao)
            glBindBuffer(GL_ARRAY_BUFFER, _vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
            glDrawArrays(GL_LINE_STRIP, 0, len(points))
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

        glUseProgram(0)