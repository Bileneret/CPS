import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pygame
from pygame.locals import *

# Константи
MAP_FILENAME = 'europe_map.png'
#MAP_FILENAME = 'russia.png'
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
CELL_SIZE = 10           # Розмір клітинки
GRID_LINE_WIDTH = 1      # Товщина лінії сітки
WATER_COLOR = np.array([173, 216, 230])   # #ADD8E6 для моря
WATER_THRESHOLD = 0.7   # поріг для води
FPS = 60

# Стани клітини
UNBURNED = 0
BURNING = 1
BURNT = 2

class Cell:
    def __init__(self, rect, is_land):
        self.rect = rect
        self.is_land = is_land

# Генерація карти
def generate_europe_map(filename, width, height, dpi=100):
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = fig.add_subplot(1,1,1,projection=ccrs.PlateCarree())
    ax.set_extent([-25,40,35,75], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=1)
    ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=1)
    ax.add_feature(cfeature.LAKES, facecolor='lightblue', edgecolor='black', linewidth=1)
    ax.add_feature(cfeature.RIVERS, edgecolor='black', linewidth=0.5)
    plt.tight_layout(pad=0)
    fig.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

# Завантаження карти
def load_map_surface(filename):
    if not os.path.isfile(filename):
        generate_europe_map(filename, SCREEN_WIDTH, SCREEN_HEIGHT)
    surf = pygame.image.load(filename).convert()
    return pygame.transform.smoothscale(surf,(SCREEN_WIDTH,SCREEN_HEIGHT))

# Побудова сітки
def build_grid(map_surf):
    arr = pygame.surfarray.array3d(map_surf)
    cols = SCREEN_WIDTH//CELL_SIZE
    rows = SCREEN_HEIGHT//CELL_SIZE
    cells=[]
    total=CELL_SIZE*CELL_SIZE
    for y in range(rows):
        for x in range(cols):
            rect=pygame.Rect(x*CELL_SIZE,y*CELL_SIZE,CELL_SIZE,CELL_SIZE)
            tile=arr[x*CELL_SIZE:(x+1)*CELL_SIZE, y*CELL_SIZE:(y+1)*CELL_SIZE]
            flat=tile.reshape(-1,3)
            water=np.sum(np.all(flat==WATER_COLOR,axis=1))
            is_land=(water< WATER_THRESHOLD*total)
            cells.append(Cell(rect,is_land))
    return cells, rows, cols

# Крок моделі пожежі
def step_fire(state,burn,cells,rows,cols,P,T):
    new_s=state.copy(); new_b=burn.copy()
    for y in range(rows):
        for x in range(cols):
            idx=y*cols+x
            if not cells[idx].is_land: continue
            if state[y,x]==UNBURNED:
                neigh=state[max(y-1,0):min(y+2,rows), max(x-1,0):min(x+2,cols)]
                if np.any(neigh==BURNING) and np.random.rand()<P:
                    new_s[y,x]=BURNING; new_b[y,x]=T
            elif state[y,x]==BURNING:
                new_b[y,x]-=1
                if new_b[y,x]<=0: new_s[y,x]=BURNT
    return new_s,new_b

# Малювання станів
def draw_fire(scr,state,cells,rows,cols,hover):
    cmap={UNBURNED:(34,139,34),BURNING:(255,0,0),BURNT:(0,0,0)}
    for y in range(rows):
        for x in range(cols):
            idx=y*cols+x
            if not cells[idx].is_land: continue
            r=cells[idx].rect; c=cmap[state[y,x]]
            if hover==(x,y): c=tuple(min(255,v+50) for v in c)
            scr.fill(c,r); pygame.draw.rect(scr,(0,0,0),r,GRID_LINE_WIDTH)

# Вибір параметрів
def choose_parameters():
    print('Обрати готові варіанти ймовірності загоряння та час горіння? (+ / -)')
    choice=input().strip()
    presets=[
        (0.9,9),(0.7,7),(0.5,5),(0.3,3),(0.1,1),
        (0.9,3),(0.7,5),(0.5,7),(0.3,9),(0.1,1)
    ]
    if choice=='+':
        for i,(p,t) in enumerate(presets[:9],1):
            print(f"{i}. P_burn={p}, T_burn={t}")
        idx=int(input('Виберіть номер: ').strip())
        return presets[idx-1]
    else:
        while True:
            try:
                p=float(input('Введіть P_burn (0.01–1.00): '))
                if 0.01<=p<=1: break
            except: pass
        while True:
            try:
                t=int(input('Введіть T_burn (1–50): '))
                if 1<=t<=50: break
            except: pass
        return p,t

# Головна функція
def main():
    # Вибір параметрів перед стартом
    P,T=choose_parameters()
    pygame.init(); screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    pygame.display.set_caption('Модель лісової пожежі')
    font=pygame.font.SysFont(None,24)

    map_surf=load_map_surface(MAP_FILENAME)
    cells,rows,cols=build_grid(map_surf)
    state=np.zeros((rows,cols),dtype=np.int8)
    burn=np.zeros((rows,cols),dtype=np.int8)
    fire=False; clock=pygame.time.Clock()

    while True:
        hover=None; mx,my=pygame.mouse.get_pos(); cx,cy=mx//CELL_SIZE,my//CELL_SIZE
        if 0<=cx<cols and 0<=cy<rows: hover=(cx,cy)
        for e in pygame.event.get():
            if e.type==QUIT or (e.type==KEYDOWN and e.key==K_ESCAPE): pygame.quit(); sys.exit()
            if e.type==MOUSEBUTTONDOWN and e.button==1 and hover:
                if cells[cy*cols+cx].is_land and state[cy,cx]!=BURNT:
                    state[cy,cx]=BURNING; burn[cy,cx]=T; fire=True
        if fire: state,burn=step_fire(state,burn,cells,rows,cols,P,T)
        screen.blit(map_surf,(0,0)); draw_fire(screen,state,cells,rows,cols,hover)
        # відобразити параметри
        txt=font.render(f"P_burn={P:.2f}  T_burn={T}",True,(255,255,255))
        screen.blit(txt,(10,10))
        pygame.display.flip(); clock.tick(FPS)

if __name__=='__main__': main()
