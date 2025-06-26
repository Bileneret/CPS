import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import lorenz
import rossler
import chua
import game_minGL
import pygame

class TestAttractors(unittest.TestCase):
    def setUp(self):
        # Ініціалізація атракторів з початковими значеннями
        self.lorenz_attractor = lorenz.LorenzAttractor(
            position=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            sigma=10.0, rho=28.0, beta=8.0/3.0, dt=0.01, color=(1.0, 0.0, 0.0)
        )
        self.rossler_attractor = rossler.RosslerAttractor(
            position=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            a=0.2, b=0.2, c=5.7, dt=0.01, color=(0.0, 1.0, 0.0)
        )
        self.chua_attractor = chua.ChuaAttractor(
            position=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            alpha=10.0, beta=14.87, m0=-1.143, m1=-0.714, dt=0.01, color=(0.0, 0.0, 1.0)
        )

    def test_lorenz_update(self):
        # Перевірка оновлення координат для атрактора Лоренца
        initial_x, initial_y, initial_z = self.lorenz_attractor.x, self.lorenz_attractor.y, self.lorenz_attractor.z
        self.lorenz_attractor.update()
        self.assertNotEqual(initial_x, self.lorenz_attractor.x, "Координата x не оновилася")
        self.assertNotEqual(initial_y, self.lorenz_attractor.y, "Координата y не оновилася")
        self.assertNotEqual(initial_z, self.lorenz_attractor.z, "Координата z не оновилася")

    def test_rossler_update(self):
        # Перевірка оновлення координат для атрактора Рьослера
        initial_x, initial_y, initial_z = self.rossler_attractor.x, self.rossler_attractor.y, self.rossler_attractor.z
        self.rossler_attractor.update()
        self.assertNotEqual(initial_x, self.rossler_attractor.x, "Координата x не оновилася")
        self.assertNotEqual(initial_y, self.rossler_attractor.y, "Координата y не оновилася")
        self.assertNotEqual(initial_z, self.rossler_attractor.z, "Координата z не оновилася")

    def test_chua_update(self):
        # Перевірка оновлення координат для атрактора Чуа
        initial_x, initial_y, initial_z = self.chua_attractor.x, self.chua_attractor.y, self.chua_attractor.z
        self.chua_attractor.update()
        self.assertNotEqual(initial_x, self.chua_attractor.x, "Координата x не оновилася")
        self.assertNotEqual(initial_y, self.chua_attractor.y, "Координата y не оновилася")
        self.assertNotEqual(initial_z, self.chua_attractor.z, "Координата z не оновилася")

    def test_lorenz_points_length(self):
        # Перевірка, що кількість точок у списку points збільшується після оновлення
        initial_length = len(lorenz.points)
        self.lorenz_attractor.update()
        self.assertEqual(len(lorenz.points), initial_length + 1, "Список точок не збільшився")

    def test_rossler_points_length(self):
        # Перевірка, що кількість точок у списку points збільшується після оновлення
        initial_length = len(rossler.points)
        self.rossler_attractor.update()
        self.assertEqual(len(rossler.points), initial_length + 1, "Список точок не збільшився")

    def test_chua_points_length(self):
        # Перевірка, що кількість точок у списку points збільшується після оновлення
        initial_length = len(chua.points)
        self.chua_attractor.update()
        self.assertEqual(len(chua.points), initial_length + 1, "Список точок не збільшився")

    def test_lorenz_init_gl(self):
        # Перевірка ініціалізації OpenGL для атрактора Лоренца
        with patch.object(lorenz, 'glGenVertexArrays', return_value=1) as mock_gen_arrays, \
             patch.object(lorenz, 'glGenBuffers', return_value=1) as mock_gen_buffers, \
            patch.object(lorenz, 'glBindVertexArray') as mock_bind_vao, \
            patch.object(lorenz, 'glBindBuffer') as mock_bind_buffer, \
            patch.object(lorenz, 'glBufferData') as mock_buffer_data, \
            patch.object(lorenz, 'glVertexAttribPointer') as mock_vertex_attrib, \
            patch.object(lorenz, 'glEnableVertexAttribArray') as mock_enable_attrib:
            lorenz._vao = None
            lorenz._vbo = None
            lorenz.init_gl()
            self.assertEqual(lorenz._vao, 1, "VAO не ініціалізоване коректно")
            self.assertEqual(lorenz._vbo, 1, "VBO не ініціалізоване коректно")
            mock_gen_arrays.assert_called_once_with(1)
            mock_gen_buffers.assert_called_once_with(1)

    def test_rossler_init_gl(self):
        # Перевірка ініціалізації OpenGL для атрактора Рьослера
        with patch.object(rossler, 'glGenVertexArrays', return_value=1) as mock_gen_arrays, \
            patch.object(rossler, 'glGenBuffers', return_value=1) as mock_gen_buffers, \
            patch.object(rossler, 'glBindVertexArray') as mock_bind_vao, \
            patch.object(rossler, 'glBindBuffer') as mock_bind_buffer, \
            patch.object(rossler, 'glBufferData') as mock_buffer_data, \
            patch.object(rossler, 'glVertexAttribPointer') as mock_vertex_attrib, \
            patch.object(rossler, 'glEnableVertexAttribArray') as mock_enable_attrib:
            rossler._vao = None
            rossler._vbo = None
            rossler.init_gl()
            self.assertEqual(rossler._vao, 1, "VAO не ініціалізоване коректно")
            self.assertEqual(rossler._vbo, 1, "VBO не ініціалізоване коректно")
            mock_gen_arrays.assert_called_once_with(1)
            mock_gen_buffers.assert_called_once_with(1)

    def test_chua_init_gl(self):
    # Перевірка ініціалізації OpenGL для атрактора Чуа
        with patch.object(chua, 'glGenVertexArrays', return_value=1) as mock_gen_arrays, \
            patch.object(chua, 'glGenBuffers', return_value=1) as mock_gen_buffers, \
            patch.object(chua, 'glBindVertexArray') as mock_bind_vao, \
            patch.object(chua, 'glBindBuffer') as mock_bind_buffer, \
            patch.object(chua, 'glBufferData') as mock_buffer_data, \
            patch.object(chua, 'glVertexAttribPointer') as mock_vertex_attrib, \
            patch.object(chua, 'glEnableVertexAttribArray') as mock_enable_attrib:
            chua._vao = None
            chua._vbo = None
            chua.init_gl()
            self.assertEqual(chua._vao, 1, "VAO не ініціалізоване коректно")
            self.assertEqual(chua._vbo, 1, "VBO не ініціалізоване коректно")
            mock_gen_arrays.assert_called_once_with(1)
            mock_gen_buffers.assert_called_once_with(1)

@patch('pygame.event.get')
@patch('game_minGL.clock')
def test_game_minGL_camera_movement(self, mock_clock, mock_event_get):
    # Налаштування мокового clock
    mock_clock.get_time.return_value = 1000  # 1 секунда

    # Ініціалізація
    game_minGL.setup()
    game_minGL.is_paused = False
    game_minGL.camera_pos = np.array([0.0, 0.0, 5.0], dtype=np.float32)
    game_minGL.forward = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    game_minGL.right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    game_minGL.move_speed = 5.0

    # Симуляція натискання клавіші W (рух вперед)
    mock_event_get.return_value = []
    keys = {
        pygame.K_w: True,      # Рух вперед
        pygame.K_s: False,     # Рух назад
        pygame.K_a: False,     # Рух ліворуч
        pygame.K_d: False,     # Рух праворуч
        pygame.K_SPACE: False, # Рух вгору
        pygame.K_LCTRL: False, # Рух вниз (ліва Ctrl)
        pygame.K_RCTRL: False  # Рух вниз (права Ctrl)
    }
    with patch('pygame.key.get_pressed', return_value=keys):
        # Виконуємо один цикл main_loop
        for _ in range(1):  # Обмежуємо цикл однією ітерацією
            game_minGL.main_loop()

    # Перевірка, що камера перемістилася вперед
    expected_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # 5.0 - 5.0 * 1.0
    np.testing.assert_array_almost_equal(game_minGL.camera_pos, expected_pos, decimal=5)

if __name__ == '__main__':
    unittest.main()