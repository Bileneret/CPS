import os
import sys
import tempfile
import shutil
import unittest

import numpy as np
import pygame


from main import (
    generate_europe_map,
    load_map_surface,
    build_grid,
    step_fire,
    draw_fire,
    UNBURNED, BURNING, BURNT, Cell,
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, WATER_COLOR
)


class TestFireMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        # Необхідно встановити відеомодуль, щоб .convert() працював
        pygame.display.set_mode((1, 1))
        cls.tmpdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_generate_europe_map_creates_file(self):
        """generate_europe_map повинен створити файл і він не порожній"""
        fn = os.path.join(self.tmpdir, "europe_test.png")
        generate_europe_map(fn, width=400, height=300, dpi=50)
        self.assertTrue(os.path.isfile(fn), "Файл не створено")
        self.assertGreater(os.path.getsize(fn), 0, "Файл пустий")

    def test_load_map_surface_dimensions(self):
        """load_map_surface повертає Surface розміром SCREEN_WIDTH×SCREEN_HEIGHT"""
        # Створимо тимчасовий файл-картинку
        surf = pygame.Surface((100, 50))
        surf.fill((255, 0, 0))
        fn = os.path.join(self.tmpdir, "small.png")
        pygame.image.save(surf, fn)

        loaded = load_map_surface(fn)
        self.assertIsInstance(loaded, pygame.Surface)
        self.assertEqual(loaded.get_width(), SCREEN_WIDTH)
        self.assertEqual(loaded.get_height(), SCREEN_HEIGHT)

    def test_build_grid_classification(self):
        """build_grid має класифікувати хоча б одну land і одну water клітинку"""
        # Частково land, частково water: зробимо смужку
        w, h = CELL_SIZE * 4, CELL_SIZE * 2
        mixed = pygame.Surface((w, h))
        # Верхня половина – вода, нижня – чорна
        mixed.fill(tuple(WATER_COLOR), rect=pygame.Rect(0, 0, w, h//2))
        mixed.fill((0, 0, 0), rect=pygame.Rect(0, h//2, w, h//2))

        cells, rows, cols = build_grid(mixed)
        has_land  = any(c.is_land for c in cells)
        has_water = any(not c.is_land for c in cells)
        self.assertTrue(has_land,  "Не виявлено жодної land-клітинки")
        self.assertTrue(has_water, "Не виявлено жодної water-клітинки")

    def test_step_fire_spread_and_burnout(self):
        """step_fire повинен поширювати вогонь та зменшувати час горіння"""
        rows = cols = 3
        cells = [Cell(None, True) for _ in range(rows*cols)]
        state = np.zeros((rows, cols), dtype=np.int8)
        burn  = np.zeros((rows, cols), dtype=np.int8)
        state[1,1] = BURNING
        burn[1,1] = 2

        new_state, new_burn = step_fire(state, burn, cells, rows, cols, P=1.0, T=1)
        burning_neighbors = sum(
            1 for y in range(rows) for x in range(cols)
            if (y,x) != (1,1) and new_state[y,x] == BURNING
        )
        self.assertGreater(burning_neighbors, 0, "Вогонь не поширився")
        self.assertTrue(new_burn[1,1] < 2 or new_state[1,1] == BURNT,
                        "Час горіння не зменшився або центр не потух")

    def test_draw_fire_changes_pixel(self):
        """draw_fire має малювати відповідні кольори"""
        screen = pygame.Surface((CELL_SIZE*5, CELL_SIZE*5))
        cells = []
        for y in range(5):
            for x in range(5):
                is_land = (x == 2 and y == 2)
                rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cells.append(Cell(rect, is_land))

        state = np.zeros((5,5), dtype=np.int8)
        state[2,2] = BURNING

        # Без hover
        draw_fire(screen, state, cells, 5, 5, hover=None)
        # З hover
        draw_fire(screen, state, cells, 5, 5, hover=(2,2))

        px = screen.get_at((2*CELL_SIZE + CELL_SIZE//2, 2*CELL_SIZE + CELL_SIZE//2))[:3]
        self.assertNotEqual(px, (0, 0, 0), "Піксель не намальовано")

if __name__ == '__main__':
    unittest.main()
