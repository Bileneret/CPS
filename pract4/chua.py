import numpy as np
import ctypes
from OpenGL.GL import *
import pyrr

# Параметри за замовчуванням
alpha = 10.0
beta = 14.87
m0 = -1.143
m1 = -0.714
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

def nonlinear_function(x):
    return m1 * x + 0.5 * (m0 - m1) * (abs(x + 1) - abs(x - 1))

def update_points(x, y, z, alpha, beta, dt):
    global points
    dx_dt = alpha * (y - x - nonlinear_function(x))
    dy_dt = x - y + z
    dz_dt = -beta * y
    
    x_new = x + dx_dt * dt
    y_new = y + dy_dt * dt
    z_new = z + dz_dt * dt
    
    points.append([x_new, y_new, z_new])
    return x_new, y_new, z_new

class ChuaAttractor:
    def __init__(self, position, alpha=10.0, beta=14.87, m0=-1.143, m1=-0.714, dt=0.01, color=(0.0, 0.0, 1.0)):
        self.position = np.array(position, dtype=np.float32)
        self.alpha = alpha
        self.beta = beta
        self.m0 = m0
        self.m1 = m1
        self.dt = dt
        self.color = color
        self.x, self.y, self.z = 0.1, 0.0, 0.0  # Початкові умови
        global points
        points = []
        for _ in range(10):  # Ініціалізація початкових точок
            self.x, self.y, self.z = update_points(self.x, self.y, self.z, self.alpha, self.beta, self.dt)

    def update(self):
        self.x, self.y, self.z = update_points(self.x, self.y, self.z, self.alpha, self.beta, self.dt)

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