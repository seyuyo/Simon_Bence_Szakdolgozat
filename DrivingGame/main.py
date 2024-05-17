import pygame
import pygame_widgets
import math
import sys
import os
import random
import numpy as np
from pygame_widgets.slider import Slider
import csv
import obstacles
import json
import matplotlib.pyplot as plt
import model_control
import model

pygame.init()

def scaling(img, scale):
    new_size = round(img.get_width() * scale), round(img.get_height() * scale)
    return pygame.transform.scale(img, new_size)


def rotate_image_to_center(window, img, position, rotation_angle):
    rotated_img = pygame.transform.rotate(img, rotation_angle)
    new_img_rect = rotated_img.get_rect(center=img.get_rect(topleft=position).center)
    window.blit(rotated_img, new_img_rect.topleft)
    pygame.draw.rect(window, (255, 0, 0), new_img_rect, 2)


# ablak szélesség és magasság
WIDTH, HEIGHT = 1200, 900

# fű és pálya képek betöltése, méretezése
GRASS = scaling(pygame.image.load("field/grass.jpg"), 3.5)
FIELD_ONLY = scaling(pygame.image.load("field/field_only.png"), 0.55)
TRACKSIDE = scaling(pygame.image.load("field/trackside.png"), 0.55)
FINISH = scaling(pygame.image.load("field/finish_line.png"), 0.15)
PEDESTRIAN = scaling(pygame.image.load("obstacles/pedestrian3.png"), 0.05)
MUD = scaling(pygame.image.load("obstacles/mud1.png"), 0.06)

# autó kép betöltése, méretezése
CAR = scaling(pygame.image.load("field/car.png"), 0.4)
CAR_WIDTH, CAR_HEIGHT = CAR.get_width(), CAR.get_height()

# maszkok létrehozása
GRASS_MASK = pygame.mask.from_surface(GRASS) # maszk létrehozása a fű képből
FIELD_ONLY_MASK = pygame.mask.from_surface(FIELD_ONLY) # maszk létrehozása a pálya képből
TRACKSIDE_MASK = pygame.mask.from_surface(TRACKSIDE) # maszk létrehozása a pálya képből
CAR_MASK = pygame.mask.from_surface(CAR) # maszk létrehozása az autó képből
PEDESTRIAN_MASK = pygame.mask.from_surface(PEDESTRIAN) # maszk létrehozása a gyalogos képből
MUD_MASK = pygame.mask.from_surface(MUD) # maszk létrehozása a sár képből

# ablak beállítása szélesség-magasság szerint
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Önvezető autó")


obstacles_list = []

# Gyalogos kép pozíciója a vezérlőpanelen
PEDESTRIAN_PANEL_X = WIDTH - 250 + 40  # -15 a vezérlőpanelen belüli eltolás miatt
PEDESTRIAN_PANEL_Y = 420
PEDESTRIAN_PANEL_WIDTH = PEDESTRIAN.get_width()
PEDESTRIAN_PANEL_HEIGHT = PEDESTRIAN.get_height()

# Sár kép pozíciója a vezérlőpanelen
MUD_PANEL_X = WIDTH - 250 + 155
MUD_PANEL_Y = 420
MUD_PANEL_WIDTH = MUD.get_width()
MUD_PANEL_HEIGHT = MUD.get_height()

# Gomb pozíció és méret a vezérlőpanelen
CLEAR_BUTTON_X = WIDTH - 250 + 20
CLEAR_BUTTON_Y = 500
CLEAR_BUTTON_WIDTH = 200
CLEAR_BUTTON_HEIGHT = 50

# maximum képkocka/másodperc
FPS = 60

# A szenzorok számát és elhelyezkedését beállíthatod az alábbi konstansokkal
NUM_SENSORS = 6  # Szenzorok száma
SENSOR_ANGLE_RANGE = 90  # A szenzorok által lefedett szög
SENSOR_LENGTH = 40 # szenzor hossza


class Car:
    CAR_ = CAR
    START_POSITION = (78, 190)

    """
    Car osztály konstruktor.

    Paraméterek:
    - max_vel (float): Az autó maximális sebessége.
    - rotation_vel (float): Az autó forgási sebessége.
    """

    def __init__(self, max_vel, rotation_vel):
        self.car = self.CAR_
        self.max_vel = max_vel
        self.vel = 1  # Jelenlegi sebesség inicializálása
        self.rotation_vel = rotation_vel  # Forgási sebesség inicializálása
        self.angle = 0
        self.x, self.y = self.START_POSITION  # Kezdő pozíció inicializálása
        self.center = (self.x + CAR_WIDTH / 2, self.y + CAR_HEIGHT / 2)  # Az autó középpontja
        self.acceleration = 0.1  # Gyorsulás inicializálása
        self.sensor_length = SENSOR_LENGTH # Szenzor inicializálása
        self.sensors = [] # Szenzorok inicializálása
        self.rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        self.mask = pygame.mask.from_surface(self.CAR_)

        # Szenzorok hozzáadása az autóhoz
        self.add_sensors(NUM_SENSORS, SENSOR_ANGLE_RANGE)

    def detect_collision(self, obstacles):
        """ Ellenőrzi, hogy az autó ütközik-e bármely akadállyal. """
        for obstacle in obstacles:
            if self.mask.overlap(obstacle.mask, (self.rect.x - obstacle.rect.x, self.rect.y - obstacle.rect.y)):
                return True  # Ütközés történt
        return False

    def add_sensors(self, num_sensors, angle_range):
        # A szenzorok közötti szög kiszámítása
        angle_increment = angle_range / (num_sensors - 1)

        # Az első szenzor szögének meghatározása, úgy hogy a szenzorok
        # szimmetrikusan helyezkedjenek el az origó körül
        start_angle = -angle_range / 2

        for i in range(num_sensors):
            # Az aktuális szenzor szögének kiszámítása
            angle = start_angle + i * angle_increment
            self.add_sensor(angle)

    def add_sensor(self, angle):
        self.sensors.append(math.radians(angle))  # A szöget radiánba konvertáljuk

    def get_max_velocity(self):
        return self.max_vel

    def get_velocity(self):
        return self.vel

    def get_angle(self):
        return self.angle

    def get_rotation_velocity(self):
        return self.rotation_vel

    def get_position(self):
        return self.x, self.y

    def get_acceleration(self):
        return self.acceleration

    def set_max_velocity(self, max_vel):
        self.max_vel = max_vel

    def set_velocity(self, vel):
        if vel < 1:
            self.vel = 1
        else:
            self.vel = vel

    def set_angle(self, angle):
        if angle > 360:
            angle -= 360
        elif angle < 0:
            angle += 360
        self.angle = angle


    def set_rotation_velocity(self, rotation_vel):
        self.rotation_vel = rotation_vel

    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    """
    Az autó forgatását végző metódus.

    Paraméterek:
    - left (bool): Balra forgatás engedélyezése.
    - right (bool): Jobbra forgatás engedélyezése.
    """
    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_vel  # Forgatás balra
        elif right:
            self.angle -= self.rotation_vel  # Forgatás jobbra

    """
    Az autó kirajzolását végző metódus.

    Paraméterek:
    - win (pygame.Surface): A Pygame ablak, amelybe az autót kirajzoljuk.

    """
    def draw_car(self, win, obstacles):
        rotate_image_to_center(win, self.car, (self.x, self.y), self.angle)
        self.draw_sensors(win, obstacles)

    """ Az érzékelők rajzolása """

    def draw_sensors(self, win, obstacles):
        """ Az érzékelők rajzolása, beleértve az akadályokkal való ütközést is. """
        for sensor_angle in self.sensors:
            absolute_sensor_angle = self.angle + math.degrees(sensor_angle + math.pi / 2)

            # Az érzékelő kezdőpontja az autó orrában
            start_x = self.center[0] + (CAR_WIDTH / 2) * math.cos(math.radians(self.angle))
            start_y = self.center[1] + (CAR_WIDTH / 2) * math.sin(math.radians(self.angle))
            self.center = (self.x + CAR_WIDTH / 2, self.y + CAR_HEIGHT / 2)

            # Érzékelő végpontjának koordinátái
            end_x = start_x + self.sensor_length * math.cos(math.radians(absolute_sensor_angle))
            end_y = start_y - self.sensor_length * math.sin(math.radians(absolute_sensor_angle))

            # Alapértelmezett szín
            sensor_color = (200, 200, 200)  # Semleges szürke

            # Ellenőrzés az akadályok alapján
            for obstacle in obstacles:
                if obstacle.rect.collidepoint((end_x, end_y)):
                    if obstacle.image == PEDESTRIAN:
                        sensor_color = (0, 0, 0)  # Fekete a gyalogos
                    elif obstacle.image == MUD:
                        sensor_color = (255, 87, 34)  # narancs a sár
                    break  # Kilépünk a ciklusból, ha már találtunk akadályt

            # Ellenőrzés a maszkok alapján, ha az akadályok között nincs találat
            if sensor_color == (200, 200, 200):  # Csak ha nincs akadály
                if self.check_sensor_collision(FIELD_ONLY_MASK, (end_x, end_y)):
                    sensor_color = (0, 255, 0)  # Zöld a pályán
                elif self.check_sensor_collision(TRACKSIDE_MASK, (end_x, end_y)):
                    sensor_color = (255, 180, 0)  # Sárga a pálya szélén
                elif self.check_sensor_collision(GRASS_MASK, (end_x, end_y)):
                    sensor_color = (255, 0, 0)  # Piros a füvön

            # Érzékelő rajzolása
            pygame.draw.line(win, sensor_color, self.center, (end_x, end_y), 2)
            pygame.draw.circle(win, sensor_color, (int(end_x), int(end_y)), 5)

    def check_sensor_collision(self, mask, sensor_end):
        """
        Ellenőrzi az érzékelő végpontjának ütközését a megadott maszkkal.

        :param mask: A maszk, amellyel az ütközést ellenőrizzük (pálya vagy fű maszk).
        :param sensor_end: Az érzékelő végpontjának koordinátái.
        :return: True, ha az érzékelő végpontja az adott maszkon belül van, egyébként False.
        """

        mask_width, mask_height = mask.get_size()  # Maszk méretének lekérése

        # Az érzékelő végpontjának koordinátáinak lekerekítése
        sensor_end_x = round(sensor_end[0])
        sensor_end_y = round(sensor_end[1])

        # Ha az érzékelő végpontja a maszkon belül van, akkor ütközés van
        if 0 <= sensor_end_x < mask_width and 0 <= sensor_end_y < mask_height:
            # Ha a pixel átlátszó, akkor nincs ütközés
            if mask.get_at((sensor_end_x, sensor_end_y)) == 0:
                return False
            else:
                return True
        else:
            return False



    """ Az autó előre mozgását végző metódus. """
    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)  # Sebesség növelése
        self.move()  # Mozgás elvégzése


    """ Az autó hátrafelé mozgását végző metódus. """
    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

    """ Az autó általános mozgását végző metódus. """
    def move(self):
        radians = math.radians(self.angle)  # Szöget radiánba konvertálja
        vertical = math.cos(radians) * self.vel  # Vertikális mozgás számolása
        horizontal = math.sin(radians) * self.vel  # Horizontális mozgás számolása

        self.y -= vertical  # Y pozíció frissítése
        self.x -= horizontal  # X pozíció frissítése


    """ Az autó lassítását végző metódus amennyiben felengedjük a gázt vagy hátrafelé megyünk."""
    def slowing(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)  # Sebesség csökkentése
        self.move()  # Mozgás elvégzése

    """ Az autó fűre/terepre lépését beállító metódus. """
    def collide(self, mask, x=0, y=0):
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(CAR_MASK, offset)

class QLearningAgent:
    def __init__(self, action_size, state_size, learning_rate=0.1, discount_factor=0.95,
                 initial_exploration_rate=0.5, exploration_decay=0.99, min_exploration_rate=0.001):
        self.action_size = action_size  # Az elérhető akciók száma
        self.state_size = state_size  # A lehetséges állapotok száma
        self.learning_rate = learning_rate  # Tanulási ráta (alfa)
        self.discount_factor = discount_factor  # Diszkont faktor (gamma)
        self.exploration_rate = initial_exploration_rate  # Kezdeti felfedezési ráta (epszilon)
        self.exploration_decay = exploration_decay  # A felfedezési ráta csökkenési üteme
        self.min_exploration_rate = min_exploration_rate  # Minimális felfedezési ráta
        self.q_table = np.zeros((state_size, action_size))  # Q-táblázat inicializálása nullákkal

    def decide_action(self, state):
        # Akció kiválasztása epsilon-greedy stratégia alapján
        if np.random.rand() < self.exploration_rate:
            # Véletlenszerű akció választása (exploration)
            return np.random.randint(self.action_size)
        else:
            # Legjobb akció választása (exploitation)
            return np.argmax(self.q_table[state])

    def update_policy(self, state, action, reward, next_state):
        # Q-táblázat frissítése a Q-learning egyenlettel
        old_value = self.q_table[state, action]
        future_q = np.max(self.q_table[next_state])
        # Új Q-érték számítása
        new_value = (1 - self.learning_rate) * old_value + self.learning_rate * (reward + self.discount_factor * future_q)
        self.q_table[state, action] = new_value
        # Felfedezési ráta csökkentése
        self.exploration_rate = max(self.exploration_rate * self.exploration_decay, self.min_exploration_rate)

    def get_q_table(self):
        return self.q_table

# Szenzorértékek leképezése különböző felületekre
sensor_values = {
    'G': 0,  # Pálya
    'Y': 1,  # Pálya széle
    'R': 2,  # Fű
    'B': 3,  # Gyalogos
    'O': 4   # Sár
}

# Állapot kinyerése a szenzor adatokból
def get_state_from_sensors(sensor_data):
    state = 0
    for data in sensor_data:
        state += sensor_values[data]
    return state

# Q-tábla mentése és betöltése fájlból
def save_q_table(agent, filename="q_table.json"):
    with open(filename, "w") as f:
        json.dump(agent.q_table.tolist(), f)  # Numpy array konvertálása listává a mentéshez

def load_q_table(agent, filename="q_table.json"):
    with open(filename, "r") as f:
        agent.q_table = np.array(json.load(f))  # Lista konvertálása Numpy array-vé a betöltéshez


# Jutalmak beállítása
def compute_reward(car):
    """ Számolja ki a jutalmat az autó állapota alapján. """
    if not car.collide(FIELD_ONLY_MASK) and not car.collide(TRACKSIDE_MASK):
        # büntetés, pélyaelhagyás esetén
        return -100
    elif car.collide(TRACKSIDE_MASK):
        # büntetés, ha a pálya szélén van
        return -10
    elif car.get_velocity() < 1:
        # büntetés, ha az autó nem mozog
        return -50
    # Pozitív jutalom helyes haladásért
    return 100

# Játék ciklus frissítése
agent = QLearningAgent(action_size=5, state_size=300)

# Jutalmak betöltése fájlból
with open("rewards.json", "r") as f:
    rewards_per_episode = json.load(f)

# Csak az összegzett jutalmakra van szükségünk
rewards = [reward[2] for reward in rewards_per_episode]

# Eredmények plotolása
# plt.plot(rewards)
# plt.xlabel('Episodes')
# plt.ylabel('Total Reward')
# plt.title('Q-learning Agent Performance')
# plt.show()

# Kiértékelés
# average_reward = np.mean(rewards)
# print(f"Average Reward: {average_reward}")

# Például kiszámíthatjuk a mozgó átlagot a simább görbe érdekében
# moving_average = np.convolve(rewards, np.ones(100)/100, mode='valid')
# plt.plot(moving_average)
# plt.xlabel('Episodes')
# plt.ylabel('Moving Average Reward')
# plt.title('Q-learning Agent Performance (Moving Average)')
# plt.show()

# Q-tábla betöltése
load_q_table(agent)

# akció végrehajtása az autón
def apply_action_to_car(car, action):
    # Itt a cselekvések lehetnek például:
    # 0 - előre, 1 - jobbra, 2 - balra, 3 - Fordul jobbra, 4 - Fordul balra
    if action == 0:
        car.move_forward()
    elif action == 1:
        car.rotate(right=True)
    elif action == 2:
        car.rotate(left=True)
    elif action == 4:
        car.move_forward()
        car.rotate(right=True)
    elif action == 5:
        car.move_forward()
        car.rotate(left=True)

# Játék ciklus frissítése
def draw_elements(win, images, player_car, obstacles):
    for car, pos in images:
        win.blit(car, pos)

    for obstacle in obstacles:
        obstacle.draw(win)

    player_car.draw_car(win, obstacles)
    player_car.draw_sensors(win, obstacles)

def save_sensor_data(sensor_data, filename):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(sensor_data)


# adatok elmentése fájlba
def save_drive_data(sensor_data, velocity, filename='automated_driving_data_full.csv'):
    # Ellenőrizzük, hogy a fájl létezik-e
    file_exists = os.path.exists(filename)

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Ha a fájl nem létezik, írjuk ki a fejlécet
        if not file_exists:
            # Fejléc, amely meghatározza az oszlopok nevét
            header = ['sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5', 'sensor_6', 'velocity']
            writer.writerow(header)

        # Összeállítjuk a rögzítendő adatokat
        data = sensor_data + [velocity]
        writer.writerow(data)



# Képek létrehozása és pozíciók beállítása
images = [(GRASS, (0, 0)), (FIELD_ONLY, (0, 0)), (TRACKSIDE, (0, 0)), (FINISH, (69, 152))]

# Autó létrehozása
player_car = Car(4, 6)


# Felület az adatok megjelenítéséhez és vezérléshez
control_surface = pygame.Surface((300, HEIGHT))
control_surface.fill((255, 255, 255))

control_panel = pygame.Surface((300, HEIGHT))
control_panel.fill((200, 200, 200))

# csűszkák létrehozása
max_velocity_slider = Slider(WIN, WIDTH - 210, 170, 160, 15, min=0, max=10, step=0.1,
                             initial=player_car.get_max_velocity())

rotation_velocity_slider = Slider(WIN, WIDTH - 210, 90, 160, 15, min=0, max=10, step=0.1,
                                      initial=player_car.get_rotation_velocity())

acceleration_slider = Slider(WIN, WIDTH - 210, 250, 160, 15, min=0, max=1, step=0.1,
                                        initial=player_car.get_acceleration())

def random_position_within_mask(mask, image_width, image_height):
    """ Generál egy véletlenszerű pozíciót a megadott maszkon belül. """
    mask_width, mask_height = mask.get_size()

    while True:
        x = random.randint(0, mask_width - image_width)
        y = random.randint(0, mask_height - image_height)

        # Ellenőrizni, hogy a maszk érvényes területén belül van-e a kép
        if mask.get_at((x, y)) != 0:
            return x, y

# Adatgyűjtés szenzorok alapján
def collect_sensor_data(car):
    sensor_data = [''] * NUM_SENSORS # mindig a szenzorok számával inicializáljuk
    try:
        for index, sensor_angle in enumerate(car.sensors):

            # Az érzékelő szöge az autó szögéhez képest
            absolute_sensor_angle = car.angle + math.degrees(sensor_angle + math.pi / 2)

            # Az érzékelő kezdőpontjának koordinátái az autó orrában
            start_x = car.center[0] + (CAR_WIDTH / 2) * math.cos(math.radians(car.angle))
            start_y = car.center[1] + (CAR_WIDTH / 2) * math.sin(math.radians(car.angle))

            # Érzékelők végeinek koordinátái
            end_x = start_x + car.sensor_length * math.cos(math.radians(absolute_sensor_angle))
            end_y = start_y - car.sensor_length * math.sin(math.radians(absolute_sensor_angle))

            # Ellenőrizzük, melyik akadály található a szenzorban
            found_obstacle = False
            for obstacle in obstacles_list:
                if obstacle.rect.collidepoint((end_x, end_y)):
                    if obstacle.image == PEDESTRIAN:
                        sensor_data[index] = "B"  # Gyalogos
                    elif obstacle.image == MUD:
                        sensor_data[index] = "O"  # Sár
                    found_obstacle = True
                    break

            # Ha az érzékelő végpontja a pályán van, akkor tároljuk a szenzor által mért távolságot
            if not found_obstacle:
                if car.check_sensor_collision(FIELD_ONLY_MASK, (end_x, end_y)):
                    sensor_data[index] = "G"  # Pálya
                elif car.check_sensor_collision(TRACKSIDE_MASK, (end_x, end_y)):
                    sensor_data[index] = "Y"  # Pálya széle
                elif car.check_sensor_collision(GRASS_MASK, (end_x, end_y)):
                    sensor_data[index] = "R"  # Fű
                elif sensor_data[index] == '':
                    sensor_data[index] = "R"

        if len(sensor_data) != NUM_SENSORS:
            raise ValueError("Nem elegendő szenzor adat")

    except Exception as e:
        print(f"Adatgyűjtési hiba: {e}")
        sensor_data = ['R'] * NUM_SENSORS

    return sensor_data

# Adatgyűjtésre szolgáló lista inicializálása
data = []

# jutaalmak listája
rewards_per_episode = []

""" A program fő ciklusa, amely a játékot vezérli. """
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            # Kilépés előtt mentjük az állapotot
            # save_q_table(agent)
            # print("Az utolsó Q-tábla elmentve.")
            # # A játék végeztével mentjük a jutalmakat
            # with open("rewards.json", "w") as f:
            #     json.dump(rewards_per_episode, f)
            pygame.quit()
            sys.exit()

        # Kezeljük az egér eseményeket (gomb lenyomás, elengedés, mozgás)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            for obstacle in obstacles_list:
                obstacle.handle_event(event)

            # Az új akadály hozzáadása csak `MOUSEBUTTONDOWN` eseménynél történik
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                # Törlés gomb kattintásának ellenőrzése
                if (CLEAR_BUTTON_X <= mouse_x <= CLEAR_BUTTON_X + CLEAR_BUTTON_WIDTH and
                        CLEAR_BUTTON_Y <= mouse_y <= CLEAR_BUTTON_Y + CLEAR_BUTTON_HEIGHT):
                    obstacles_list.clear()

                # Ha a gyalogos képre kattintottak
                if (PEDESTRIAN_PANEL_X <= mouse_x <= PEDESTRIAN_PANEL_X + PEDESTRIAN_PANEL_WIDTH and
                        PEDESTRIAN_PANEL_Y <= mouse_y <= PEDESTRIAN_PANEL_Y + PEDESTRIAN_PANEL_HEIGHT):
                    x, y = random_position_within_mask(FIELD_ONLY_MASK, PEDESTRIAN.get_width(), PEDESTRIAN.get_height())
                    new_obstacle = obstacles.Obstacle(PEDESTRIAN, (x, y))
                    obstacles_list.append(new_obstacle)

                # Ha a sár képre kattintottak
                elif (MUD_PANEL_X <= mouse_x <= MUD_PANEL_X + MUD_PANEL_WIDTH and
                      MUD_PANEL_Y <= mouse_y <= MUD_PANEL_Y + MUD_PANEL_HEIGHT):
                    x, y = random_position_within_mask(FIELD_ONLY_MASK, MUD.get_width(), MUD.get_height())
                    new_obstacle = obstacles.Obstacle(MUD, (x, y))
                    obstacles_list.append(new_obstacle)

    # Adatgyűjtés a szenzoroktól
    sensor_data = collect_sensor_data(player_car)
    # state = get_state_from_sensors(sensor_data)
    #
    # # Agent cselekvés döntése
    # action = agent.decide_action(state)
    # apply_action_to_car(player_car, action)
    #
    # # Új állapot és jutalom számítása
    # new_sensor_data = collect_sensor_data(player_car)
    # new_state = get_state_from_sensors(new_sensor_data)
    # reward = compute_reward(player_car)
    #
    # # Q-tábla frissítése
    # agent.update_policy(state, action, reward, new_state)
    #
    # # Rögzítjük a jutalmat
    # if len(rewards_per_episode) == 0 or rewards_per_episode[-1][1] > pygame.time.get_ticks():
    #     rewards_per_episode.append((len(rewards_per_episode), pygame.time.get_ticks() + 1000, 0))
    # rewards_per_episode[-1] = (rewards_per_episode[-1][0], rewards_per_episode[-1][1], rewards_per_episode[-1][2] + reward)



    # Debug információk
    # print(f"State: {state}, Action: {action}, Reward: {reward}, Exploration: {agent.exploration_rate}")
    # Például 1000 ciklusonként mentjük a Q-táblát
    # if pygame.time.get_ticks() % 100000 == 0:
    #     save_q_table(agent)
    #     print("Q-tábla mentve.")

    # Az autó vezérlése a szenzorok alapján (automatikus vezérlés)
    # ac.apply_control(player_car, sensor_data)

    # Az adatokat folyamatosan hozzáfűzzük a CSV fájlhoz (SL modell)
    # save_sensor_data(sensor_data, 'automated_driving_data_full.csv')
    # save_drive_data(sensor_data, round(player_car.get_velocity(), 2))

    # Az autó mozgatása az SL modell vezérlése alapján
    model_control.apply_advanced_model_control(player_car, model.load_model, sensor_data)

    draw_elements(WIN, images, player_car, obstacles_list)
    WIN.blit(control_panel, (WIDTH - 250, 0))

    keys = pygame.key.get_pressed()
    moved = False

    # Autó mozgatása W, A, S, D vagy a nyíl billentyűkkel
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_car.rotate(left=True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_car.rotate(right=True)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        player_car.move_backward()
    if not moved:
        player_car.slowing()

    # Ha a játékos terepen marad akkor csúszkával állítható a maximális sebesség és a forgási sebesség
    if player_car.collide(FIELD_ONLY_MASK) or player_car.collide(TRACKSIDE_MASK):
        max_velocity_slider.listen(events)
        max_velocity_slider.draw()

        player_car.set_max_velocity(max_velocity_slider.getValue())

        rotation_velocity_slider.listen(events)
        rotation_velocity_slider.draw()

        player_car.set_rotation_velocity(rotation_velocity_slider.getValue())

        acceleration_slider.listen(events)
        acceleration_slider.draw()

        player_car.set_acceleration(acceleration_slider.getValue())

    # Ha a játékos fűre lép akkor a maximális sebesség és a forgási sebesség lelassul egy fix értékre
    elif player_car.collide(GRASS_MASK):
        player_car.set_max_velocity(2)
        player_car.set_rotation_velocity(2)
        player_car.set_acceleration(0.05)

    # Autó pozíciójának ellenőrzése, hogy ne menjen ki az ablakból
    if player_car.x < 0:
        player_car.x = 0
    elif player_car.x > WIDTH - 290:
        player_car.x = WIDTH - 290

    if player_car.y < 0:
        player_car.y = 0
    elif player_car.y > HEIGHT - CAR_HEIGHT:
        player_car.y = HEIGHT - CAR_HEIGHT

    # Adatokat megjelenítő felület
    control_panel.blit(control_surface, (0, 0))
    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Sebesség:{round(player_car.get_velocity(), 2)} p/s",
                                                    True, (0, 0, 0)),(25, 5))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Forgási sebesség:{round(player_car.get_rotation_velocity(), 2)}",
                                                    True, (0, 0, 0)), (20, 50))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Maximális sebesség:{round(player_car.get_max_velocity(), 2)}",
                                                    True, (0, 0, 0)), (20, 130))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Gyorsulás:{round(player_car.get_acceleration(), 2)}",
                                                    True, (0, 0, 0)), (52, 210))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Fék:{round(player_car.get_acceleration(), 2)}",
                                                    True, (0, 0, 0)), (85, 270))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Akadályok kiválasztása:",
                                                    True, (0, 0, 0)), (20, 330))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Gyalogos",
                                                    True, (0, 0, 0)), (20, 370))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Sár",
                                                    True, (0, 0, 0)), (160, 370))
    #gyalogos hozzáadása
    control_panel.blit(PEDESTRIAN, (40, 420))

    #sár hozzáadása
    control_panel.blit(MUD, (155, 420))

    # Törlés gomb rajzolása
    pygame.draw.rect(control_panel, (0, 0, 0), (CLEAR_BUTTON_X - (WIDTH - 240), CLEAR_BUTTON_Y,
                                                CLEAR_BUTTON_WIDTH + 30, CLEAR_BUTTON_HEIGHT))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render("Összes akadály törlése", True, (255, 255, 255)),
        (CLEAR_BUTTON_X - (WIDTH - 250), CLEAR_BUTTON_Y + 15))

    pygame_widgets.update(events)
    pygame.display.update()
    pygame.time.Clock().tick(FPS)
