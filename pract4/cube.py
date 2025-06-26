# cube.py
import numpy as np
import ctypes
from OpenGL.GL import *
import pyrr

# Вершини куба 1×1×1, центр у (0,0,0)
_vertices = np.array([
    -0.5, -0.5, -0.5,  # 0
     0.5, -0.5, -0.5,  # 1
     0.5,  0.5, -0.5,  # 2
    -0.5,  0.5, -0.5,  # 3
    -0.5, -0.5,  0.5,  # 4
     0.5, -0.5,  0.5,  # 5
     0.5,  0.5,  0.5,  # 6
    -0.5,  0.5,  0.5   # 7
], dtype=np.float32)

# Індекси для трикутників
_indices = np.array([
    0,1,2, 2,3,0,  # задня грань
    4,5,6, 6,7,4,  # передня грань
    0,1,5, 5,4,0,  # низ
    2,3,7, 7,6,2,  # верх
    0,3,7, 7,4,0,  # ліво
    1,2,6, 6,5,1   # право
], dtype=np.uint32)

# Пари індексів для ребер (лінії)
_edge_indices = np.array([
    0,1, 1,2, 2,3, 3,0,
    4,5, 5,6, 6,7, 7,4,
    0,4, 1,5, 2,6, 3,7
], dtype=np.uint32)

# Буфери
_vao = None
_vbo = None
_ebo = None
_ebo_edges = None

def init_gl():
    global _vao, _vbo, _ebo, _ebo_edges
    _vao = glGenVertexArrays(1)
    glBindVertexArray(_vao)

    # VBO
    _vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, _vbo)
    glBufferData(GL_ARRAY_BUFFER, _vertices.nbytes, _vertices, GL_STATIC_DRAW)

    # EBO для трикутників
    _ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, _ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, _indices.nbytes, _indices, GL_STATIC_DRAW)

    # EBO для ребер
    _ebo_edges = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, _ebo_edges)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, _edge_indices.nbytes, _edge_indices, GL_STATIC_DRAW)

    # Атрибут позиції (location=0)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(
        0, 3, GL_FLOAT, GL_FALSE,
        3 * ctypes.sizeof(ctypes.c_float),
        ctypes.c_void_p(0)
    )

    # Скидання
    glBindVertexArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

class Cube:
    def __init__(self, position, size, color, edge_thickness):
        self.position = position  # np.array([x, y, z])
        self.size = size          # float
        self.color = color        # tuple (r, g, b)
        self.edge_thickness = edge_thickness  # int

    def draw_gl(self, view, projection, shader_program):
        # Створення модельної матриці з урахуванням позиції та масштабу
        model = pyrr.matrix44.create_from_translation(self.position)
        model = pyrr.matrix44.multiply(model, pyrr.matrix44.create_from_scale([self.size, self.size, self.size]))

        glUseProgram(shader_program)
        # Передача матриць у шейдер
        for name, mat in (("model", model), ("view", view), ("projection", projection)):
            loc = glGetUniformLocation(shader_program, name)
            glUniformMatrix4fv(loc, 1, GL_FALSE, mat)
        # Установка кольору для граней
        loc = glGetUniformLocation(shader_program, "color")
        glUniform3f(loc, *self.color)
        # Отрисовка граней куба
        glBindVertexArray(_vao)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, _ebo)
        glDrawElements(GL_TRIANGLES, len(_indices), GL_UNSIGNED_INT, None)
        # Установка кольору для ребер (чорний)
        glUniform3f(loc, 0.0, 0.0, 0.0)
        # Установка товщини ребер
        glLineWidth(self.edge_thickness)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, _ebo_edges)
        glDrawElements(GL_LINES, len(_edge_indices), GL_UNSIGNED_INT, None)
        # Скидання стану
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glUseProgram(0)