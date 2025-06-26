---

# ПРАКТИЧНА РОБОТА №2
## Завдання: Змоделювати зчитування даних з багатофазного лічильника та обрахунок вартості електроенергії.
### Умова: Написати программу на довільній мові програмування (Java, Python, JS, C, C#, С++...), яка б на вхід отримувала дані двофазного лічильника "день-ніч" та за різним тарифом, рахувала різницю між попередніми показниками та поточними, виставляючи рахунок. 
У випадку отримання даних від нового лічильника, вони мають дописатись у масив з усіма даними. 
Після опрацювання нових даних, вони мають записатись замість старих як наступні початкові.
У випадку надходження менших даних, ніж були попередні, накрутити задане число квт (нехай, 100 день та 80 ніч) та видати рахунок.

## [Коди завдання](pract2)

## Розбір:

- Manager.py - відповідає за меню адміністратора (пароль 123123). Можливість змінювати тариф день/ніч, редагувати, додавати/видаляти лічильники, переглядати/видаляти історію будь-якого лічильника.
- User.py - відповідає за меню користувача. (Базовий лічильник id: 123, passwd: 123123). Кожен користувач може додавати нові показники, переглядати історію та змінити пароль для свого лічильника. Вихід не передбачений 😈.
- main.py - головне тіло програми. По факту відповіда лише за вибір ролі, що описані вище.
- process_queue - випадкове додавання випадкових даних до випадкових лічильників. Є можливість "накрутки" значень, бо все випадкове.
- db.py - освновний файл "зв'язник" між Базою Даних та пайтоном.

---

# ПРАКТИЧНА РОБОТА №3
## Завдання: Передбачення погоди.
### Умова: Передбачення погоди (температури) на наступний день. День потрібно вибрати один з існуючих, щоб можна було зрозуміти, чи вірне ваше передбачення.
#### Датасет: [\*Базель\*](https://www.meteoblue.com/uk/weather/archive/export?daterange=2022-09-04%20-%202024-03-19&locations%5B%5D=basel_switzerland_2661604&domain=ERA5T&min=2023-01-01&max=2024-03-19&params%5B%5D=&params%5B%5D=temp2m&params%5B%5D=&params%5B%5D=&params%5B%5D=&params%5B%5D=&params%5B%5D=&params%5B%5D=&params%5B%5D=&utc_offset=%2B00%3A00&timeResolution=hourly&temperatureunit=CELSIUS&velocityunit=KILOMETER_PER_HOUR&energyunit=watts&lengthunit=metric&degree_day_type=10%3B30&gddBase=10&gddLimit=30)

## [Коди завдання](pract3)

## Розбір:

- csvindb.py - csv in db. Завантажує дані із .csv файлу у створену базу даних. 
- db.py - освновний файл "зв'язник" між Базою Даних та пайтоном.
- main.py - основний файл програми, що і відповіда за прогнозування та візуалізацію завдання.

Використовується модель "Random Forest Regressor" - "Випадковий ліс для регресії". 

## Модель прогнозування погоди

Для прогнозу погодних параметрів (температура, опади, пориви вітру, тиск) використовується Random Forest Regressor. Пайплайн виглядає так:

1. Розподіл на тренувальний і тестовий набори. Тренувальний - для зменшення MSE (Mean Squared Error) - середнє квадратів помилок між справжніми та прогнозованими значеннями. Чим менше - тим точніше. Тестовий набір - для перевірки прогрозу.
2. **Тренування моделі**  
   ```python
   from sklearn.ensemble import RandomForestRegressor
   model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
   model.fit(X_train, y_train)
   ```
   - Ми створюємо 100 незалежних дерев прогнозу і одночасно вчимо їх на різних випадках з нашого тестового набору даних. Кожне дерево навчається окремо, щоб у сумі дати більш точний результат.

3. **Оцінка якості**  
   ```python
   from sklearn.metrics import mean_squared_error
   y_pred = model.predict(X_test)
   mse = mean_squared_error(y_test, y_pred)
   ```
   Після навчання кожне з 100 дерев робить свій прогноз. Беремо середнє значення цих прогнозів. Порівнюємо його з реальними показниками, обчислюючи середню MSE.

4. **Збереження результатів**  
   - Збереження прогнозів у `results.txt` і логування в базу через `save_prediction`.

5. **Візуалізація**

<details>
<summary><strong>Показати код</strong></summary>

   ```python
   plt.figure(figsize=(12, 6))
   plt.plot(test['timestamp'], test['temperature'], label='Реальна')
   plt.plot(test['timestamp'], models['temperature'].predict(X_test), label='Прогноз')
   plt.xlabel('Дата')
   plt.ylabel('Температура (°C)')
   plt.title('Прогноз температури на 06.03.2024')
   plt.legend()
   plt.grid(True)
   plt.show()
   ```
</details>

---

# ПРАКТИЧНА РОБОТА №4
## Завдання: Модель хаосу чи атрактор Лоренца.
### Умова: Побудувати атрактор Лоренца або іншу модель хаосу та показати, яким чином вона доводить, що велика похибка призводить до зміни показників моделі (погоди), які критично впливають на результат підрахунків та псує коректність передбачення. Unit тести необхідні.

## [Коди завдання](pract4)

## Розбір:

1. Початково програма писалась на pygame + asyncio. Фінально було перенесено на OpenGL.
OpenGL дозволяє працювати із справжнім 3D + розрахунки на GPU, замість псевдо-3D + CPU (yeah-yeah, 5 fps).
Але і без pygame не обійшлось. Використовувався для створення 2D полотна (меню). Аналог такого рішення часто використовується для інтерфесів у справжніх 3D іграх. (World of Warcraft / Minecraft 👍)

2. **Прострі 3D фігури:**
   - cube.py     - Куб.
   - pira.py     - Піраміда.
   - cylinder.py - Циліндр.

Усі фігури ідентично написані, підтримують зміну кольору та товщину ребер.

3. **Складні 3D графіки:**
   - lorenz.py   - Аттрактор Лоренза.
   - chua.py     - Аттрактор Чуа.
   - rossel.py   - Аттрактор Ро(е)/(ё)/(ьо)сселла.

- setting.txt - просто файл для зберігання налаштувань швидкості та чутливості камери.
- test_art.py - тести.

## Пояснення:

**Перехід на OpenGL спростив роботу у 3D, але реалізація руху із паралельним обертом камери - було жахіттям.**

*Код оберту камери:*

<details>
<summary><strong>Показати код</strong></summary>

```python
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
```

</details>

  - Абсолютно такий же векторний спосіб використовуються для реалізації керування камерою у 3D-просторі, обчислюючи вектори напрямку на основі кутів повороту.

*Код для руху у просторі:*

<details>
<summary><strong>Показати код</strong></summary>

```python
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
```

</details>

  - Звісно, реалізовано просто, але проблема була у синхронізації повороту камери з рухом прямо. Зараз працює: Куди дивимось, туди і йдемо прямо. Роблячи це у pygame доводилось проектувати камеру у просторі як точку на площину під користувачем і рухати її координати. Звісно, що таким способом поворот камери враховується лише відносно, і натискаючи `W` рух користувача був куди завгодно, але не туди, куди б хотілось.

**2D повéрх 3D:**

<details>
<summary><strong>Показати код</strong></summary>

```python
def update_menu_texture():
    flipped = pygame.transform.flip(menu_surface, False, True)
    data = pygame.image.tostring(flipped, "RGBA", True)
    glBindTexture(GL_TEXTURE_2D, menu_texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, MENU_W, MENU_H + TAB_H,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
```

</details>

  - Pygame - це 2D-інструмент, що тут малює меню, яке вже потім передається в OpenGL як текстура.

**Open source GLSL Шейдери:**

<details>
<summary><strong>Показати код</strong></summary>

```python
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
```
</details>

  - Старший брат усього проекту на OpenGL. Найпростіше, щоб не використовувати фікс-конвеєр як це було у старих відеоіграх.

Інша величезна частина коду побудована для роботи із аттракторами та фігурами та дуже просить розбиття на ще N файлів, але це вже чисто технічно можна назвати СУПЕР-мікродвигуном для ігор, оскільки вона має деякі риси ігрового движка, такі як рендеринг і управління камерою. Но без фізики, анімації, звуків та скриптів.

---

# ПРАКТИЧНА РОБОТА №5
## Завдання: Побудова генетичного алгоритму. Задача комівояжера (Travelling Salesman Problem): Мінімізація відстані, яку потрібно подолати продавцеві, щоб відвідати кожного клієнта точно один раз і повернутися в точку виходу.
### Умова: Запрограмувати вирішення обраної задачі за допомогою генетичного алгоритму. Дати можливість обирати кількість та якість початкової популяції чи декількох популяцій. Кількість ітерацій має теж задаватись, включно з опцією “до останнього живого”. Виводити статистику популяцій після кожної ітерації.

## Розбір: 

Початково програма писалась для лабіринту (архів maze.zip), але оскільки сама задача Комівояжера більш призначена для графів - розглянемо архів graf.zip.

- main.py - головний файл програми. Відповідає за введення початкових значень та основний зв'язуючий файл усієї програми.
- graf.py - генерує зв’язний ненаправлений зважений граф з можливістю змінити ймовірність з'єднання вершин ребрами випадковою вагою (2 < `weight` < 10).
- graph.py - візуалізатор усієї програми. Малює n-вершинний граф, у якому вершини=клієнти, а ребра=шляхи. Також малює "продавців" і вказує найкращий знайдений шлях минулого покоління.
- genetic.py - реалізація генетичного алгоритму для задачі комівояжера (TSP).

### Використано: 

**1. Звичайний генетичний алгоритм (Simple Genetic Algorithm): Заснований на базових операціях кросоверу, мутації та вибору**
Кожне покоління: відбір → кросовер → мутація → нове покоління.

<details>
<summary><strong>Показати код</strong></summary>

```python
def simple_genetic_algorithm(graph, pop_size=100, generations=200, mutation_rate=0.1):
    population = [Seller(graph, mutation_rate) for _ in range(pop_size)]
    
    for gen in range(generations):
        # Оцінка
        for s in population:
            s.evaluate_fitness()

        # Відбір: беремо кращу половину
        population.sort(key=lambda s: s.points, reverse=True)
        selected = population[:pop_size // 2]

        # Створення нової популяції
        new_population = []
        while len(new_population) < pop_size:
            parent1 = random.choice(selected)
            parent2 = random.choice(selected)
            child = parent1.clone(mutate=True, parent2=parent2)
            new_population.append(child)
        
        population = new_population
        best = max(population, key=lambda s: s.points)
        print(f"Gen {gen}: best score = {best.points}, dist = {best.distance}")
```
</details>

**2. Елітний генетичний алгоритм (Elitist Genetic Algorithm)**  
Найкращі (елітні) продавці копіюються напряму в наступне покоління.

<details>
<summary><strong>Показати код</strong></summary>

```python
def elitist_genetic_algorithm(graph, pop_size=100, generations=200, elite_size=10, mutation_rate=0.1):
    population = [Seller(graph, mutation_rate) for _ in range(pop_size)]

    for gen in range(generations):
        for s in population:
            s.evaluate_fitness()

        population.sort(key=lambda s: s.points, reverse=True)
        elite = population[:elite_size]
        selected = population[:pop_size // 2]

        new_population = elite[:]
        while len(new_population) < pop_size:
            parent1 = random.choice(selected)
            parent2 = random.choice(selected)
            child = parent1.clone(mutate=True, parent2=parent2)
            new_population.append(child)
        
        population = new_population
        best = max(population, key=lambda s: s.points)
        print(f"[Elite GA] Gen {gen}: best = {best.points}, dist = {best.distance}")
 ```
</details>
qweqwe
