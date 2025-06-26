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

```python
def update_menu_texture():
    flipped = pygame.transform.flip(menu_surface, False, True)
    data = pygame.image.tostring(flipped, "RGBA", True)
    glBindTexture(GL_TEXTURE_2D, menu_texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, MENU_W, MENU_H + TAB_H,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
```

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

```python
# в блоці побудови нового покоління:
for _ in range(self.pop_size - self.elite_size):
    parent1 = random.choice(elite)
    parent2 = random.choice(elite)
    # у clone() відбувається і кросовер (часткове схрещення з parent2), і мутація
    new_pop.append(parent1.clone(mutate=True, parent2=parent2))

```

**2. Елітний генетичний алгоритм (Elitist Genetic Algorithm)**  
Найкращі (елітні) продавці копіюються напряму в наступне покоління.

```python
# після оцінки фітнесу, сортування за points:
elite = sorted(self.population, key=lambda s: s.points, reverse=True)[:self.elite_size]
# напряму копіюємо цих “елітних” у нову популяцію
new_pop.extend(elite)
 ```


**3. Паралельний генетичний алгоритм (Parallel Genetic Algorithm)**  
fitnes кожного продавця обчислюється паралельно (через 'multiprocessing.Pool'), що Це значно пришвидшує обчислення для великих популяцій. Але, звісно, популяція у 1000 осіб - занадто 🥲.

```python
# створюємо пул процесів
self.pool = Pool(cpu_count())

# у тренувальному циклі — одночасно викликаємо evaluate_seller для всієї population
self.population = self.pool.map(evaluate_seller, self.population)

# по завершенню тренування закриваємо пул
self.pool.close()
self.pool.join()
```

### Обов'язкові етапи
##### Все показано у кодах нижче:

<details>
<summary><strong>GeneticTSP</strong></summary>

```python
class GeneticTSP:
    def __init__(…):
        # 1) Ініціалізація популяції
        # Створюємо початкову популяцію випадкових маршрутів
        self.population = self._initialize_population(loaded_genome)

    def _initialize_population(self, loaded_genome):
        """1) Ініціалізація популяції: повертає список Seller’ів."""
        population = []
        if loaded_genome and self._is_valid_genome(loaded_genome):
            population.append(Seller(..., genome=loaded_genome))
        while len(population) < self.pop_size:
            population.append(Seller(self.graf, self.mutation_rate))
        return population

    def train(self):
        def loop():
            for gen in range(1, self.generations + 1):
                # 2) Оцінка придатності (fitness evaluation)
                self._evaluate_population()

                # 7) Умова зупинки
                if self._check_termination():
                    break

                # 3) Вибір батьків
                elite, selected = self._select_parents()

                # 4) Створення нащадків
                new_offspring = self._crossover_and_mutate(elite)

                # 6) Вибір для наступної популяції (елітність + нащадки)
                self._form_next_population(elite, new_offspring)

            # 8) Вивід результатів
            return self.get_best()

        threading.Thread(target=loop, daemon=True).start()


    def _evaluate_population(self):
        """2) Оцінка придатності: паралельно рахуємо fitness кожного."""
        self.population = self.pool.map(evaluate_seller, self.population)


    def _check_termination(self):
        """7) Умова зупинки: досягли оптимуму чи пройшли всі покоління."""
        return any(self._compare_paths(s.path, self.optimal_path)
                   for s in [self.best_by_distance]) \
               or gen >= self.generations


    def _select_parents(self):
        """3) Вибір батьків: турнір/рулетка/елітний відбір."""
        # еліта
        elite = sorted(self.population, key=lambda s: s.points, reverse=True)[:self.elite_size]
        # інша селекція (наприклад, турнір)
        selected = random.choices(elite, k=self.pop_size // 2)
        return elite, selected


    def _crossover_and_mutate(self, parents):
        """4) Створення нащадків: кросовер + мутація."""
        offspring = []
        for _ in range(self.pop_size - self.elite_size):
            p1, p2 = random.sample(parents, 2)
            child = p1.clone(mutate=True, parent2=p2)
            offspring.append(child)
        return offspring


    def _form_next_population(self, elite, offspring):
        """6) Формуємо наступну популяцію: еліта + нові нащадки."""
        self.population = elite + offspring
```

</details>

<details>
<summary><strong>Seller</strong></summary>

```python
class Seller:
    def __init__(…):
        self.genome = self._initialize_genome()   # 1) Ініціалізація однієї особини

    def _initialize_genome(self):
        """Генерує випадковий валідний маршрут."""

    def evaluate_fitness(self):
        """2 & 5) Оцінка придатності поточної особини."""
        # рахує distance, points, штрафи, повертає points

    def move(self):
        """Частина етапу 4: просуває особину по маршруту для анімації."""
```

</details>

--- 

# ПРАКТИЧНА РОБОТА №6
## Завдання: Клітинні автомати. Модель лісової пожежі.
### Умова: Розробити модель епідемії або лісової пожежі за допомогою клітинних автоматів. Навчитися програмувати та візуалізувати динамічні процеси у складних системах.
### Модель лісової пожежі:
   - Клітини: 
      - Кожна клітина може бути в одному з трьох станів: 

         - незаймана (T)
         - горить (B)
         - згоріла (E).
   - Правила переходу:
      - Незаймана клітина може загорітися, якщо поруч з нею є клітини, що горять.
      - Горюча клітина з часом стає згорілою.
      - Згоріла клітина більше не може змінювати свій стан.

   - Параметри:
      - Ймовірність загоряння для незайманої клітини (P_burn).
      - Час горіння клітини (T_burn).

## [Коди завдання](pract6)

## Розбір:

main.py - головний файл із виконанням завдання. 
