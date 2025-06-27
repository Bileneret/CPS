import os
import pygame
import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import pyrr
import cube  # cube.init_gl() та cube.Cube
import pira  # pira.init_gl() та pira.Pira
import cylinder  # cylinder.init_gl() та cylinder.Cylinder
import lorenz  # lorenz.init_gl() та lorenz.LorenzAttractor
import rossler  # rossler.init_gl() та rossler.RosslerAttractor
import chua  # chua.init_gl() та chua.ChuaAttractor

# Модельні змінні
selected_model = None
model_color_idx = 0
model_size = 50
model_edge_thickness = 1
dragging_model_slider = None

# Параметри атракторів
lorenz_sigma = 10.0
lorenz_rho = 28.0
lorenz_beta = 8.0 / 3.0
lorenz_dt = 0.01
lorenz_x0, lorenz_y0, lorenz_z0 = 1.0, 1.0, 1.0
lorenz_color_idx = 0
dragging_lorenz_slider = None

rossler_a = 0.2
rossler_b = 0.2
rossler_c = 5.7
rossler_dt = 0.01
rossler_x0, rossler_y0, rossler_z0 = 1.0, 1.0, 1.0
rossler_color_idx = 1
dragging_rossler_slider = None

chua_alpha = 10.0
chua_beta = 14.87
chua_m0 = -1.143
chua_m1 = -0.714
chua_dt = 0.01
chua_x0, chua_y0, chua_z0 = 0.1, 0.0, 0.0
chua_color_idx = 2
dragging_chua_slider = None

MODEL_COLORS = [
    ("Червоний",   (1.0, 0.0, 0.0)),
    ("Зелений",    (0.0, 1.0, 0.0)),
    ("Синій",      (0.0, 0.0, 1.0)),
    ("Жовтий",     (1.0, 1.0, 0.0)),
    ("Фіолетовий", (1.0, 0.0, 1.0)),
    ("Білий",      (1.0, 1.0, 1.0)),
]

# GLSL шейдери
VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec3 aPos;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main(){
    gl_Position = projection * view * model * vec4(aPos,1.0);
}
"""
FRAGMENT_SHADER_SRC = """
#version 330 core
out vec4 FragColor;
uniform vec3 color;
void main(){
    FragColor = vec4(color,1.0);
}
"""

# Файл налаштувань
SETTINGS_FILE = "settings_gl.txt"

# Початкові параметри
FPS = 60
move_speed = 5.0
sensitivity = 0.005
SENSITIVITY_MIN, SENSITIVITY_MAX = 0.001, 0.01
MOVE_SPEED_MIN, MOVE_SPEED_MAX = 1.0, 20.0

# Стан повзунків (0.0–1.0)
sensitivity_slider_pos = (sensitivity - SENSITIVITY_MIN) / (SENSITIVITY_MAX - SENSITIVITY_MIN)
move_speed_slider_pos = (move_speed - MOVE_SPEED_MIN) / (MOVE_SPEED_MAX - MOVE_SPEED_MIN)
dragging_slider = None  # "sens" або "speed"

# Стан камери
camera_pos = np.array([0.0, 0.0, 5.0], dtype=np.float32)
yaw = 0.0
pitch = 0.0
forward = right = up = None

# Стан UI
show_cube = True
is_paused = False
settings_open = False
active_tab = "Налаштування"  # Вкладка за замовчуванням

# Глобальні змінні вікна
SCREEN_WIDTH = SCREEN_HEIGHT = 0
shader_program = None
screen = None
clock = None
font = None

# Текстура меню (змінено розміри на 250x250)
MENU_W, MENU_H = 550, 550
TAB_H = 40
menu_surface = pygame.Surface((MENU_W, MENU_H + TAB_H), pygame.SRCALPHA)
menu_texture_id = None

# Список для зберігання всіх моделей
models = []

# Збереження налаштувань
def load_settings():
    global sensitivity, move_speed, sensitivity_slider_pos, move_speed_slider_pos
    try:
        if os.path.exists(SETTINGS_FILE) and os.path.getsize(SETTINGS_FILE) > 0:
            with open(SETTINGS_FILE, "r") as f:
                for line in f:
                    k, v = line.strip().split("=")
                    if k == "sensitivity": sensitivity = float(v)
                    elif k == "move_speed": move_speed = float(v)
        else:
            save_settings(sensitivity, move_speed)
    except:
        pass
    sensitivity_slider_pos = (sensitivity - SENSITIVITY_MIN) / (SENSITIVITY_MAX - SENSITIVITY_MIN)
    move_speed_slider_pos = (move_speed - MOVE_SPEED_MIN) / (MOVE_SPEED_MAX - MOVE_SPEED_MIN)

def save_settings(sens, speed):
    try:
        with open(SETTINGS_FILE, "w") as f:
            f.write(f"sensitivity={sens}\n")
            f.write(f"move_speed={speed}\n")
    except:
        pass

# Обчислення векторів камери
def get_camera_vectors(yaw, pitch):
    f = np.array([
        math.cos(pitch)*math.sin(yaw),
        math.sin(pitch),
        math.cos(pitch)*math.cos(yaw)
    ], dtype=np.float32)
    f /= np.linalg.norm(f)
    r = np.cross(f, np.array([0.0,1.0,0.0], dtype=np.float32))
    r /= np.linalg.norm(r)
    u = np.cross(r,f)
    return f, r, u

# Малювання та інтерактивність UI
def draw_menu_to_surface():
    global active_tab, selected_model
    global sensitivity_slider_pos, move_speed_slider_pos
    global model_color_idx, model_size, model_edge_thickness
    global lorenz_sigma, lorenz_rho, lorenz_beta, lorenz_dt, lorenz_x0, lorenz_y0, lorenz_z0, lorenz_color_idx, dragging_lorenz_slider
    global rossler_a, rossler_b, rossler_c, rossler_dt, rossler_x0, rossler_y0, rossler_z0, rossler_color_idx, dragging_rossler_slider
    global chua_alpha, chua_beta, chua_m0, chua_m1, chua_dt, chua_x0, chua_y0, chua_z0, chua_color_idx, dragging_chua_slider

    offset_x = (SCREEN_WIDTH - MENU_W) // 2
    offset_y = (SCREEN_HEIGHT - (MENU_H + TAB_H)) // 2

    # Очистка та фон
    menu_surface.fill((0, 0, 0, 180))
    pygame.draw.rect(menu_surface, (50, 50, 50, 230), (0, TAB_H, MENU_W, MENU_H))

    # Локальна позиція миші
    gm_x, gm_y = pygame.mouse.get_pos()
    local_mouse = (gm_x - offset_x, gm_y - offset_y)

    # Вкладки
    tabs = ["Налаштування", "Прості моделі", "Складні моделі"]
    tab_w = MENU_W // len(tabs)
    tab_rects = []
    for i, tab in enumerate(tabs):
        r = pygame.Rect(i * tab_w, 0, tab_w, TAB_H)
        base = (120, 120, 120) if tab == active_tab else (80, 80, 80)
        color = tuple(min(c+30,255) if r.collidepoint(local_mouse) else c for c in base)
        pygame.draw.rect(menu_surface, color, r)
        menu_surface.blit(font.render(tab, True, (255, 255, 255)), (r.x + 10, r.y + 8))
        tab_rects.append(r)

    # Повзунки «Налаштування»
    slider_rects = {}
    if active_tab == "Налаштування":
        sensitivity_slider_pos = (sensitivity - SENSITIVITY_MIN) / (SENSITIVITY_MAX - SENSITIVITY_MIN)
        move_speed_slider_pos = (move_speed - MOVE_SPEED_MIN) / (MOVE_SPEED_MAX - MOVE_SPEED_MIN)
        
        labels = ["Чутливість:", "Швидкість:"]
        for i, label in enumerate(labels):
            y = TAB_H + 20 + i * 80
            menu_surface.blit(font.render(label, True, (255,255,255)), (10, y))
            sx, sy, sw, sh = 90, y+20, 150, 10
            pygame.draw.rect(menu_surface, (100,100,100), (sx, sy, sw, sh))
            pos = sensitivity_slider_pos if i == 0 else move_speed_slider_pos
            mxp = sx + int(pos * sw)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp, sy+5), 8)
            val = sensitivity if i == 0 else move_speed
            fmt = f"{val:.3f}" if i == 0 else f"{val:.1f}"
            menu_surface.blit(font.render(fmt, True, (255,255,255)), (sx + sw + 5, sy - 8))
            slider_rects["sens" if i==0 else "speed"] = pygame.Rect(sx, sy, sw, sh)

    # Кнопки "Вийти" / "Зберегти" лише на вкладці "Налаштування"
    exit_rect = save_rect = None
    if active_tab == "Налаштування":
        exit_rect = pygame.Rect(10, TAB_H + MENU_H - 60, 100, 40)
        save_rect = pygame.Rect(MENU_W - 110, TAB_H + MENU_H - 60, 100, 40)
        def draw_btn(r, base, text):
            c = tuple(max(b-30,0) if r.collidepoint(local_mouse) else b for b in base)
            pygame.draw.rect(menu_surface, c, r)
            t = font.render(text, True, (255,255,255))
            menu_surface.blit(t, (r.x + (r.w - t.get_width())//2, r.y + (r.h - t.get_height())//2))
        draw_btn(exit_rect, (200,0,0), "Вийти")
        draw_btn(save_rect, (0,150,0), "Зберегти")

    # Вкладка "Прості моделі"
    model_button_rects = {}
    if active_tab == "Прості моделі":
        model_types = ["Куб", "Піраміда", "Циліндр"]
        for i, model_type in enumerate(model_types):
            btn = pygame.Rect(10, TAB_H + 20 + i*50, 150, 40)
            c = (120,120,120) if selected_model == model_type else (80,80,80)
            if btn.collidepoint(local_mouse):
                c = tuple(min(cj+30,255) for cj in c)
            pygame.draw.rect(menu_surface, c, btn)
            menu_surface.blit(font.render(model_type, True, (255,255,255)), (btn.x+10, btn.y+8))
            model_button_rects[model_type] = btn

        if selected_model in model_types:
            y0 = TAB_H + 20 + len(model_types)*50
            menu_surface.blit(font.render("Колір:", True, (255,255,255)), (10, y0))
            name,_ = MODEL_COLORS[model_color_idx]
            clr_r = pygame.Rect(80, y0, 150, 30)
            cc = (140,140,140) if clr_r.collidepoint(local_mouse) else (100,100,100)
            pygame.draw.rect(menu_surface, cc, clr_r)
            menu_surface.blit(font.render(name, True, (255,255,255)), (clr_r.x+10, clr_r.y+5))

            y1 = y0 + 50
            menu_surface.blit(font.render("Розмір:", True, (255,255,255)), (10, y1))
            sx, sy, sw = 80, y1+10, 150
            pygame.draw.rect(menu_surface, (80,80,80), (sx, sy, sw, 8))
            mxp = sx + int((model_size-5)/(100-5) * sw)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp, sy+4), 6)
            menu_surface.blit(font.render(str(model_size), True, (255,255,255)), (sx+sw+10, sy-8))

            y2 = y1 + 60
            menu_surface.blit(font.render("Товщина:", True, (255,255,255)), (10, y2))
            sx2, sy2, sw2 = 80, y2+10, 150
            pygame.draw.rect(menu_surface, (80,80,80), (sx2, sy2, sw2, 8))
            mxp2 = sx2 + int((model_edge_thickness-1)/(10-1) * sw2)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp2, sy2+4), 6)
            menu_surface.blit(font.render(str(model_edge_thickness), True, (255,255,255)), (sx2+sw2+10, sy2-8))

            create_r = pygame.Rect(10, y2+60, 150, 40)
            cc2 = (50,200,50) if create_r.collidepoint(local_mouse) else (0,150,0)
            pygame.draw.rect(menu_surface, cc2, create_r)
            menu_surface.blit(font.render(f"Створити", True, (255,255,255)), (create_r.x+10, create_r.y+8))

            delete_last_r = pygame.Rect(10, y2+110, 150, 40)
            cc3 = (200,50,50) if delete_last_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc3, delete_last_r)
            menu_surface.blit(font.render("Видалити", True, (255,255,255)), (delete_last_r.x+10, delete_last_r.y+8))

            delete_all_r = pygame.Rect(10, y2+160, 150, 40)
            cc4 = (200,50,50) if delete_all_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc4, delete_all_r)
            menu_surface.blit(font.render("Очистити", True, (255,255,255)), (delete_all_r.x+10, delete_all_r.y+8))

            model_button_rects.update({
                "color": clr_r,
                "size": pygame.Rect(sx, sy, sw, 8),
                "thickness": pygame.Rect(sx2, sy2, sw2, 8),
                "create": create_r,
                "delete_last": delete_last_r,
                "delete_all": delete_all_r
            })

    # Вкладка "Складні моделі"
    if active_tab == "Складні моделі":
        model_types = ["Атрактор Лоренца", "Атрактор Рьослера", "Атрактор Чуа"]
        for i, model_type in enumerate(model_types):
            btn = pygame.Rect(10, TAB_H + 20 + i*50, 230, 40)
            c = (120,120,120) if selected_model == model_type else (80,80,80)
            if btn.collidepoint(local_mouse):
                c = tuple(min(cj+30,255) for cj in c)
            pygame.draw.rect(menu_surface, c, btn)
            menu_surface.blit(font.render(model_type, True, (255,255,255)), (btn.x+10, btn.y+8))
            model_button_rects[model_type] = btn

        if selected_model == "Атрактор Лоренца":
            y0 = TAB_H + 20 + len(model_types)*50
            menu_surface.blit(font.render("Колір:", True, (255,255,255)), (10, y0))
            name, _ = MODEL_COLORS[lorenz_color_idx]
            clr_r = pygame.Rect(80, y0, 150, 30)
            cc = (140,140,140) if clr_r.collidepoint(local_mouse) else (100,100,100)
            pygame.draw.rect(menu_surface, cc, clr_r)
            menu_surface.blit(font.render(name, True, (255,255,255)), (clr_r.x+10, clr_r.y+5))

            y1 = y0 + 50
            menu_surface.blit(font.render("x0:", True, (255,255,255)), (10, y1))
            sx1, sy1, sw1 = 80, y1+10, 150
            mxp1 = sx1 + int((lorenz_x0 - 0.0)/(5.0 - 0.0) * sw1)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp1, sy1+4), 6)
            menu_surface.blit(font.render(f"{lorenz_x0:.1f}", True, (255,255,255)), (sx1+sw1+10, sy1-8))

            y2 = y1 + 30
            menu_surface.blit(font.render("y0:", True, (255,255,255)), (10, y2))
            sx2, sy2, sw2 = 80, y2+10, 150
            mxp2 = sx2 + int((lorenz_y0 - 0.0)/(5.0 - 0.0) * sw2)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp2, sy2+4), 6)
            menu_surface.blit(font.render(f"{lorenz_y0:.1f}", True, (255,255,255)), (sx2+sw2+10, sy2-8))

            y3 = y2 + 30
            menu_surface.blit(font.render("z0:", True, (255,255,255)), (10, y3))
            sx3, sy3, sw3 = 80, y3+10, 150
            mxp3 = sx3 + int((lorenz_z0 - 0.0)/(5.0 - 0.0) * sw3)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp3, sy3+4), 6)
            menu_surface.blit(font.render(f"{lorenz_z0:.1f}", True, (255,255,255)), (sx3+sw3+10, sy3-8))

            y4 = y3 + 50
            menu_surface.blit(font.render("Швидкість:", True, (255,255,255)), (10, y4))
            sx4, sy4, sw4 = 80, y4+10, 150
            mxp4 = sx4 + int((lorenz_dt - 0.001)/(0.1 - 0.001) * sw4)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp4, sy4+4), 6)
            menu_surface.blit(font.render(f"{lorenz_dt:.3f}", True, (255,255,255)), (sx4+sw4+10, sy4-8))

            create_r = pygame.Rect(10, y4+60, 150, 40)
            cc2 = (50,200,50) if create_r.collidepoint(local_mouse) else (0,150,0)
            pygame.draw.rect(menu_surface, cc2, create_r)
            menu_surface.blit(font.render(f"Створити", True, (255,255,255)), (create_r.x+10, create_r.y+8))

            delete_last_r = pygame.Rect(10, y4+110, 150, 40)
            cc3 = (200,50,50) if delete_last_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc3, delete_last_r)
            menu_surface.blit(font.render("Видалити", True, (255,255,255)), (delete_last_r.x+10, delete_last_r.y+8))

            delete_all_r = pygame.Rect(10, y4+160, 150, 40)
            cc4 = (200,50,50) if delete_all_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc4, delete_all_r)
            menu_surface.blit(font.render("Очистити", True, (255,255,255)), (delete_all_r.x+10, delete_all_r.y+8))

            model_button_rects.update({
                "color": clr_r,
                "x0": pygame.Rect(sx1, sy1, sw1, 8),
                "y0": pygame.Rect(sx2, sy2, sw2, 8),
                "z0": pygame.Rect(sx3, sy3, sw3, 8),
                "dt": pygame.Rect(sx4, sy4, sw4, 8),
                "create": create_r,
                "delete_last": delete_last_r,
                "delete_all": delete_all_r
            })

        elif selected_model == "Атрактор Рьослера":
            y0 = TAB_H + 20 + len(model_types)*50
            menu_surface.blit(font.render("Колір:", True, (255,255,255)), (10, y0))
            name, _ = MODEL_COLORS[rossler_color_idx]
            clr_r = pygame.Rect(80, y0, 150, 30)
            cc = (140,140,140) if clr_r.collidepoint(local_mouse) else (100,100,100)
            pygame.draw.rect(menu_surface, cc, clr_r)
            menu_surface.blit(font.render(name, True, (255,255,255)), (clr_r.x+10, clr_r.y+5))

            y1 = y0 + 50
            menu_surface.blit(font.render("x0:", True, (255,255,255)), (10, y1))
            sx1, sy1, sw1 = 80, y1+10, 150
            mxp1 = sx1 + int((rossler_x0 - 0.0)/(5.0 - 0.0) * sw1)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp1, sy1+4), 6)
            menu_surface.blit(font.render(f"{rossler_x0:.1f}", True, (255,255,255)), (sx1+sw1+10, sy1-8))

            y2 = y1 + 30
            menu_surface.blit(font.render("y0:", True, (255,255,255)), (10, y2))
            sx2, sy2, sw2 = 80, y2+10, 150
            mxp2 = sx2 + int((rossler_y0 - 0.0)/(5.0 - 0.0) * sw2)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp2, sy2+4), 6)
            menu_surface.blit(font.render(f"{rossler_y0:.1f}", True, (255,255,255)), (sx2+sw2+10, sy2-8))

            y3 = y2 + 30
            menu_surface.blit(font.render("z0:", True, (255,255,255)), (10, y3))
            sx3, sy3, sw3 = 80, y3+10, 150
            mxp3 = sx3 + int((rossler_z0 - 0.0)/(5.0 - 0.0) * sw3)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp3, sy3+4), 6)
            menu_surface.blit(font.render(f"{rossler_z0:.1f}", True, (255,255,255)), (sx3+sw3+10, sy3-8))

            y4 = y3 + 50
            menu_surface.blit(font.render("Швидкість:", True, (255,255,255)), (10, y4))
            sx4, sy4, sw4 = 80, y4+10, 150
            mxp4 = sx4 + int((rossler_dt - 0.001)/(0.1 - 0.001) * sw4)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp4, sy4+4), 6)
            menu_surface.blit(font.render(f"{rossler_dt:.3f}", True, (255,255,255)), (sx4+sw4+10, sy4-8))

            create_r = pygame.Rect(10, y4+60, 150, 40)
            cc2 = (50,200,50) if create_r.collidepoint(local_mouse) else (0,150,0)
            pygame.draw.rect(menu_surface, cc2, create_r)
            menu_surface.blit(font.render(f"Створити", True, (255,255,255)), (create_r.x+10, create_r.y+8))

            delete_last_r = pygame.Rect(10, y4+110, 150, 40)
            cc3 = (200,50,50) if delete_last_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc3, delete_last_r)
            menu_surface.blit(font.render("Видалити", True, (255,255,255)), (delete_last_r.x+10, delete_last_r.y+8))

            delete_all_r = pygame.Rect(10, y4+160, 150, 40)
            cc4 = (200,50,50) if delete_all_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc4, delete_all_r)
            menu_surface.blit(font.render("Очистити", True, (255,255,255)), (delete_all_r.x+10, delete_all_r.y+8))

            model_button_rects.update({
                "color": clr_r,
                "x0": pygame.Rect(sx1, sy1, sw1, 8),
                "y0": pygame.Rect(sx2, sy2, sw2, 8),
                "z0": pygame.Rect(sx3, sy3, sw3, 8),
                "dt": pygame.Rect(sx4, sy4, sw4, 8),
                "create": create_r,
                "delete_last": delete_last_r,
                "delete_all": delete_all_r
            })

        elif selected_model == "Атрактор Чуа":
            y0 = TAB_H + 20 + len(model_types)*50
            menu_surface.blit(font.render("Колір:", True, (255,255,255)), (10, y0))
            name, _ = MODEL_COLORS[chua_color_idx]
            clr_r = pygame.Rect(80, y0, 150, 30)
            cc = (140,140,140) if clr_r.collidepoint(local_mouse) else (100,100,100)
            pygame.draw.rect(menu_surface, cc, clr_r)
            menu_surface.blit(font.render(name, True, (255,255,255)), (clr_r.x+10, clr_r.y+5))

            y1 = y0 + 50
            menu_surface.blit(font.render("x0:", True, (255,255,255)), (10, y1))
            sx1, sy1, sw1 = 80, y1+10, 150
            mxp1 = sx1 + int((chua_x0 - 0.0)/(5.0 - 0.0) * sw1)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp1, sy1+4), 6)
            menu_surface.blit(font.render(f"{chua_x0:.1f}", True, (255,255,255)), (sx1+sw1+10, sy1-8))

            y2 = y1 + 30
            menu_surface.blit(font.render("y0:", True, (255,255,255)), (10, y2))
            sx2, sy2, sw2 = 80, y2+10, 150
            mxp2 = sx2 + int((chua_y0 - 0.0)/(5.0 - 0.0) * sw2)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp2, sy2+4), 6)
            menu_surface.blit(font.render(f"{chua_y0:.1f}", True, (255,255,255)), (sx2+sw2+10, sy2-8))

            y3 = y2 + 30
            menu_surface.blit(font.render("z0:", True, (255,255,255)), (10, y3))
            sx3, sy3, sw3 = 80, y3+10, 150
            mxp3 = sx3 + int((chua_z0 - 0.0)/(5.0 - 0.0) * sw3)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp3, sy3+4), 6)
            menu_surface.blit(font.render(f"{chua_z0:.1f}", True, (255,255,255)), (sx3+sw3+10, sy3-8))

            y4 = y3 + 50
            menu_surface.blit(font.render("Швидкість:", True, (255,255,255)), (10, y4))
            sx4, sy4, sw4 = 80, y4+10, 150
            mxp4 = sx4 + int((chua_dt - 0.001)/(0.1 - 0.001) * sw4)
            pygame.draw.circle(menu_surface, (180,180,255), (mxp4, sy4+4), 6)
            menu_surface.blit(font.render(f"{chua_dt:.3f}", True, (255,255,255)), (sx4+sw4+10, sy4-8))

            create_r = pygame.Rect(10, y4+60, 150, 40)
            cc2 = (50,200,50) if create_r.collidepoint(local_mouse) else (0,150,0)
            pygame.draw.rect(menu_surface, cc2, create_r)
            menu_surface.blit(font.render(f"Створити", True, (255,255,255)), (create_r.x+10, create_r.y+8))

            delete_last_r = pygame.Rect(10, y4+110, 150, 40)
            cc3 = (200,50,50) if delete_last_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc3, delete_last_r)
            menu_surface.blit(font.render("Видалити", True, (255,255,255)), (delete_last_r.x+10, delete_last_r.y+8))

            delete_all_r = pygame.Rect(10, y4+160, 150, 40)
            cc4 = (200,50,50) if delete_all_r.collidepoint(local_mouse) else (150,0,0)
            pygame.draw.rect(menu_surface, cc4, delete_all_r)
            menu_surface.blit(font.render("Очистити", True, (255,255,255)), (delete_all_r.x+10, delete_all_r.y+8))

            model_button_rects.update({
                "color": clr_r,
                "x0": pygame.Rect(sx1, sy1, sw1, 8),
                "y0": pygame.Rect(sx2, sy2, sw2, 8),
                "z0": pygame.Rect(sx3, sy3, sw3, 8),
                "dt": pygame.Rect(sx4, sy4, sw4, 8),
                "create": create_r,
                "delete_last": delete_last_r,
                "delete_all": delete_all_r
            })

    return exit_rect, save_rect, tab_rects, slider_rects, model_button_rects

# Створення/Оновлення текстури OpenGL із menu_surface
def update_menu_texture():
    global menu_texture_id
    flipped = pygame.transform.flip(menu_surface, False, True)
    data = pygame.image.tostring(flipped, "RGBA", True)
    if menu_texture_id is None:
        menu_texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, menu_texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, MENU_W, MENU_H + TAB_H,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Малювання текстурованого квадрата по центру екрана
def draw_menu_quad():
    w, h = menu_surface.get_width(), menu_surface.get_height()
    x = (SCREEN_WIDTH - w) // 2
    y = (SCREEN_HEIGHT - h) // 2

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, menu_texture_id)
    glDisable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x,   y)
    glTexCoord2f(1, 0); glVertex2f(x+w, y)
    glTexCoord2f(1, 1); glVertex2f(x+w, y+h)
    glTexCoord2f(0, 1); glVertex2f(x,   y+h)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glDisable(GL_TEXTURE_2D)

# Налаштування OpenGL та Pygame
def setup():
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen, clock, font, shader_program, forward, right, up

    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF
    )
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.1, 0.1, 1.0)

    shader_program = compileProgram(
        compileShader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER),
        compileShader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER)
    )

    cube.init_gl()
    pira.init_gl()
    cylinder.init_gl()
    lorenz.init_gl()
    rossler.init_gl()
    chua.init_gl()

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    load_settings()
    forward, right, up = get_camera_vectors(yaw, pitch)

# Головний цикл
def main_loop():
    global yaw, pitch, forward, right, up, camera_pos
    global is_paused, settings_open, active_tab
    global sensitivity, move_speed
    global selected_model, model_color_idx, model_size, model_edge_thickness, dragging_model_slider, dragging_slider
    global lorenz_sigma, lorenz_rho, lorenz_beta, lorenz_dt, lorenz_x0, lorenz_y0, lorenz_z0, lorenz_color_idx, dragging_lorenz_slider
    global rossler_a, rossler_b, rossler_c, rossler_dt, rossler_x0, rossler_y0, rossler_z0, rossler_color_idx, dragging_rossler_slider
    global chua_alpha, chua_beta, chua_m0, chua_m1, chua_dt, chua_x0, chua_y0, chua_z0, chua_color_idx, dragging_chua_slider

    exit_rect = save_rect = None
    tab_rects = []
    slider_rects = {}
    model_button_rects = {}

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                is_paused    = not is_paused
                settings_open = is_paused
                pygame.event.set_grab(not is_paused)
                pygame.mouse.set_visible(is_paused)
                if settings_open:
                    cx = (SCREEN_WIDTH - MENU_W)//2 + MENU_W//2
                    cy = (SCREEN_HEIGHT - (MENU_H+TAB_H))//2 + (MENU_H+TAB_H)//2
                    pygame.mouse.set_pos((cx, cy))
                    pygame.mouse.get_rel()

            if settings_open:
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    mx, my = e.pos
                    ox = (SCREEN_WIDTH - MENU_W)//2
                    oy = (SCREEN_HEIGHT - (MENU_H+TAB_H))//2
                    local = (mx - ox, my - oy)

                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in enumerate(tab_rects):
                        if r.collidepoint(local):
                            active_tab = ["Налаштування", "Прості моделі", "Складні моделі"][i]
                            selected_model = None

                    if active_tab == "Налаштування":
                        if exit_rect and exit_rect.collidepoint(local):
                            pygame.quit()
                            return
                        if save_rect and save_rect.collidepoint(local):
                            save_settings(sensitivity, move_speed)
                        for slider_type in ["sens", "speed"]:
                            if slider_type in slider_rects and slider_rects[slider_type].collidepoint(local):
                                dragging_slider = slider_type

                    if active_tab == "Прості моделі":
                        for model_type in ["Куб", "Піраміда", "Циліндр"]:
                            if model_type in model_button_rects and model_button_rects[model_type].collidepoint(local):
                                selected_model = model_type

                        if selected_model:
                            if "color" in model_button_rects and model_button_rects["color"].collidepoint(local):
                                model_color_idx = (model_color_idx + 1) % len(MODEL_COLORS)
                            if "size" in model_button_rects and model_button_rects["size"].collidepoint(local):
                                dragging_model_slider = "size"
                            if "thickness" in model_button_rects and model_button_rects["thickness"].collidepoint(local):
                                dragging_model_slider = "thickness"
                            if "create" in model_button_rects and model_button_rects["create"].collidepoint(local):
                                color_name, color_rgb = MODEL_COLORS[model_color_idx]
                                size = model_size / 50.0
                                edge_thickness = model_edge_thickness
                                position = np.array([len(models) * 2.0, 0.0, 0.0], dtype=np.float32)
                                if selected_model == "Куб":
                                    new_model = cube.Cube(position, size, color_rgb, edge_thickness)
                                elif selected_model == "Піраміда":
                                    new_model = pira.Pira(position, size, color_rgb, edge_thickness)
                                elif selected_model == "Циліндр":
                                    new_model = cylinder.Cylinder(position, size, color_rgb, edge_thickness)
                                models.append(new_model)
                            if "delete_last" in model_button_rects and model_button_rects["delete_last"].collidepoint(local):
                                if models:
                                    models.pop()
                            if "delete_all" in model_button_rects and model_button_rects["delete_all"].collidepoint(local):
                                models.clear()

                    if active_tab == "Складні моделі":
                        for model_type in ["Атрактор Лоренца", "Атрактор Рьослера", "Атрактор Чуа"]:
                            if model_type in model_button_rects and model_button_rects[model_type].collidepoint(local):
                                selected_model = model_type

                        if selected_model == "Атрактор Лоренца":
                            if "color" in model_button_rects and model_button_rects["color"].collidepoint(local):
                                lorenz_color_idx = (lorenz_color_idx + 1) % len(MODEL_COLORS)
                            if "x0" in model_button_rects and model_button_rects["x0"].collidepoint(local):
                                dragging_lorenz_slider = "x0"
                            if "y0" in model_button_rects and model_button_rects["y0"].collidepoint(local):
                                dragging_lorenz_slider = "y0"
                            if "z0" in model_button_rects and model_button_rects["z0"].collidepoint(local):
                                dragging_lorenz_slider = "z0"
                            if "dt" in model_button_rects and model_button_rects["dt"].collidepoint(local):
                                dragging_lorenz_slider = "dt"
                            if "create" in model_button_rects and model_button_rects["create"].collidepoint(local):
                                color_name, color_rgb = MODEL_COLORS[lorenz_color_idx]
                                position = np.array([len(models) * 2.0, 0.0, 0.0], dtype=np.float32)
                                new_model = lorenz.LorenzAttractor(position, lorenz_sigma, lorenz_rho, lorenz_beta, lorenz_dt, None, color_rgb)
                                new_model.x, new_model.y, new_model.z = lorenz_x0, lorenz_y0, lorenz_z0
                                models.append(new_model)
                            if "delete_last" in model_button_rects and model_button_rects["delete_last"].collidepoint(local):
                                if models:
                                    models.pop()
                            if "delete_all" in model_button_rects and model_button_rects["delete_all"].collidepoint(local):
                                models.clear()

                        elif selected_model == "Атрактор Рьослера":
                            if "color" in model_button_rects and model_button_rects["color"].collidepoint(local):
                                rossler_color_idx = (rossler_color_idx + 1) % len(MODEL_COLORS)
                            if "x0" in model_button_rects and model_button_rects["x0"].collidepoint(local):
                                dragging_rossler_slider = "x0"
                            if "y0" in model_button_rects and model_button_rects["y0"].collidepoint(local):
                                dragging_rossler_slider = "y0"
                            if "z0" in model_button_rects and model_button_rects["z0"].collidepoint(local):
                                dragging_rossler_slider = "z0"
                            if "dt" in model_button_rects and model_button_rects["dt"].collidepoint(local):
                                dragging_rossler_slider = "dt"
                            if "create" in model_button_rects and model_button_rects["create"].collidepoint(local):
                                color_name, color_rgb = MODEL_COLORS[rossler_color_idx]
                                position = np.array([len(models) * 2.0, 0.0, 0.0], dtype=np.float32)
                                new_model = rossler.RosslerAttractor(position, rossler_a, rossler_b, rossler_c, rossler_dt, color_rgb)
                                new_model.x, new_model.y, new_model.z = rossler_x0, rossler_y0, rossler_z0
                                models.append(new_model)
                            if "delete_last" in model_button_rects and model_button_rects["delete_last"].collidepoint(local):
                                if models:
                                    models.pop()
                            if "delete_all" in model_button_rects and model_button_rects["delete_all"].collidepoint(local):
                                models.clear()

                        elif selected_model == "Атрактор Чуа":
                            if "color" in model_button_rects and model_button_rects["color"].collidepoint(local):
                                chua_color_idx = (chua_color_idx + 1) % len(MODEL_COLORS)
                            if "x0" in model_button_rects and model_button_rects["x0"].collidepoint(local):
                                dragging_chua_slider = "x0"
                            if "y0" in model_button_rects and model_button_rects["y0"].collidepoint(local):
                                dragging_chua_slider = "y0"
                            if "z0" in model_button_rects and model_button_rects["z0"].collidepoint(local):
                                dragging_chua_slider = "z0"
                            if "dt" in model_button_rects and model_button_rects["dt"].collidepoint(local):
                                dragging_chua_slider = "dt"
                            if "create" in model_button_rects and model_button_rects["create"].collidepoint(local):
                                color_name, color_rgb = MODEL_COLORS[chua_color_idx]
                                position = np.array([len(models) * 2.0, 0.0, 0.0], dtype=np.float32)
                                new_model = chua.ChuaAttractor(position, chua_alpha, chua_beta, chua_m0, chua_m1, chua_dt, color_rgb)
                                new_model.x, new_model.y, new_model.z = chua_x0, chua_y0, chua_z0
                                models.append(new_model)
                            if "delete_last" in model_button_rects and model_button_rects["delete_last"].collidepoint(local):
                                if models:
                                    models.pop()
                            if "delete_all" in model_button_rects and model_button_rects["delete_all"].collidepoint(local):
                                models.clear()

                if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    dragging_model_slider = None
                    dragging_slider = None
                    dragging_lorenz_slider = None
                    dragging_rossler_slider = None
                    dragging_chua_slider = None

                if e.type == pygame.MOUSEMOTION:
                    lx, ly = local
                    if dragging_model_slider:
                        if dragging_model_slider == "size" and "size" in model_button_rects:
                            r = model_button_rects["size"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            model_size = int(5 + rel * (100 - 5))
                        if dragging_model_slider == "thickness" and "thickness" in model_button_rects:
                            r = model_button_rects["thickness"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            model_edge_thickness = int(1 + rel * (10 - 1))
                    if dragging_slider:
                        if dragging_slider == "sens" and "sens" in slider_rects:
                            r = slider_rects["sens"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            sensitivity_slider_pos = rel
                            sensitivity = SENSITIVITY_MIN + rel * (SENSITIVITY_MAX - SENSITIVITY_MIN)
                        if dragging_slider == "speed" and "speed" in slider_rects:
                            r = slider_rects["speed"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            move_speed_slider_pos = rel
                            move_speed = MOVE_SPEED_MIN + rel * (MOVE_SPEED_MAX - MOVE_SPEED_MIN)
                    if dragging_lorenz_slider:
                        if dragging_lorenz_slider == "x0" and "x0" in model_button_rects:
                            r = model_button_rects["x0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            lorenz_x0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_lorenz_slider == "y0" and "y0" in model_button_rects:
                            r = model_button_rects["y0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            lorenz_y0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_lorenz_slider == "z0" and "z0" in model_button_rects:
                            r = model_button_rects["z0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            lorenz_z0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_lorenz_slider == "dt" and "dt" in model_button_rects:
                            r = model_button_rects["dt"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            lorenz_dt = 0.001 + rel * (0.1 - 0.001)
                    if dragging_rossler_slider:
                        if dragging_rossler_slider == "x0" and "x0" in model_button_rects:
                            r = model_button_rects["x0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            rossler_x0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_rossler_slider == "y0" and "y0" in model_button_rects:
                            r = model_button_rects["y0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            rossler_y0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_rossler_slider == "z0" and "z0" in model_button_rects:
                            r = model_button_rects["z0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            rossler_z0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_rossler_slider == "dt" and "dt" in model_button_rects:
                            r = model_button_rects["dt"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            rossler_dt = 0.001 + rel * (0.1 - 0.001)
                    if dragging_chua_slider:
                        if dragging_chua_slider == "x0" and "x0" in model_button_rects:
                            r = model_button_rects["x0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            chua_x0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_chua_slider == "y0" and "y0" in model_button_rects:
                            r = model_button_rects["y0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            chua_y0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_chua_slider == "z0" and "z0" in model_button_rects:
                            r = model_button_rects["z0"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            chua_z0 = 0.0 + rel * (5.0 - 0.0)
                        if dragging_chua_slider == "dt" and "dt" in model_button_rects:
                            r = model_button_rects["dt"]
                            rel = (lx - r.x) / r.w
                            rel = max(0.0, min(1.0, rel))
                            chua_dt = 0.001 + rel * (0.1 - 0.001)

            else:
                if e.type == pygame.MOUSEMOTION:
                    dx, dy = e.rel
                    yaw -= dx * sensitivity
                    pitch = max(-math.pi/2+0.01, min(math.pi/2-0.01, pitch - dy * sensitivity))
                    forward, right, up = get_camera_vectors(yaw, pitch)

        if not is_paused:
            dt = clock.get_time() / 1000.0
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                camera_pos += forward * move_speed * dt
            if keys[pygame.K_s]:
                camera_pos -= forward * move_speed * dt
            if keys[pygame.K_a]:
                camera_pos -= right * move_speed * dt
            if keys[pygame.K_d]:
                camera_pos += right * move_speed * dt
            if keys[pygame.K_SPACE]:
                camera_pos[1] += move_speed * dt
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                camera_pos[1] -= move_speed * dt

            # Оновлення всіх атракторів
            for model in models:
                if isinstance(model, (lorenz.LorenzAttractor, rossler.RosslerAttractor, chua.ChuaAttractor)):
                    model.update()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        view  = pyrr.matrix44.create_look_at(
            eye=pyrr.Vector3(camera_pos),
            target=pyrr.Vector3(camera_pos + forward),
            up=pyrr.Vector3(up),
            dtype=np.float32
        )
        proj = pyrr.matrix44.create_perspective_projection(
            fovy=45.0,
            aspect=SCREEN_WIDTH / SCREEN_HEIGHT,
            near=0.1,
            far=100.0,
            dtype=np.float32
        )
        for m in models:
            m.draw_gl(view, proj, shader_program)

        if settings_open:
            exit_rect, save_rect, tab_rects, slider_rects, model_button_rects = draw_menu_to_surface()
            update_menu_texture()
            draw_menu_quad()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    setup()
    main_loop()
