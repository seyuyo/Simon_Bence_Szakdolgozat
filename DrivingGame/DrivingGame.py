import pygame
import pygame_widgets
import math
import sys
import tensorflow as tf
from StandardScaler import scaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import load_model
import numpy as np
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
import pandas as pd
import csv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler



pygame.init()

def scaling(img, scale):
    new_size = round(img.get_width() * scale), round(img.get_height() * scale)
    return pygame.transform.scale(img, new_size)


def rotate_to_center(win, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)
    win.blit(rotated_image, new_rect.topleft)
    pygame.draw.rect(win, (255, 0, 0), new_rect, 2)


# ablak szélesség és magasság
WIDTH, HEIGHT = 1200, 900

# fű és pálya képek betöltése, méretezése
GRASS = scaling(pygame.image.load("grass.jpg"), 3.5)
FIELD_ONLY = scaling(pygame.image.load("field_only.png"), 0.55)
TRACKSIDE = scaling(pygame.image.load("trackside.png"), 0.55)
FINISH = scaling(pygame.image.load("finish_line.png"), 0.15)

# autó kép betöltése, méretezése
CAR = scaling(pygame.image.load("car.png"), 0.4)
CAR_WIDTH, CAR_HEIGHT = CAR.get_width(), CAR.get_height()
GRASS_MASK = pygame.mask.from_surface(GRASS) # maszk létrehozása a fű képből
FIELD_ONLY_MASK = pygame.mask.from_surface(FIELD_ONLY) # maszk létrehozása a pálya képből
TRACKSIDE_MASK = pygame.mask.from_surface(TRACKSIDE) # maszk létrehozása a pálya képből
CAR_MASK = pygame.mask.from_surface(CAR) # maszk létrehozása az autó képből

# ablak beállítása szélesség-magasság szerint
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Önvezető autó")

# maximum képkocka/másodperc
FPS = 60

# A szenzorok számát és elhelyezkedését beállíthatod az alábbi konstansokkal
NUM_SENSORS = 5  # Szenzorok száma
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
        self.vel = 0  # Jelenlegi sebesség inicializálása
        self.rotation_vel = rotation_vel  # Forgási sebesség inicializálása
        self.angle = 0
        self.x, self.y = self.START_POSITION  # Kezdő pozíció inicializálása
        self.center = (self.x + CAR_WIDTH / 2, self.y + CAR_HEIGHT / 2)  # Az autó középpontja
        self.acceleration = 0.1  # Gyorsulás inicializálása
        self.sensor_length = SENSOR_LENGTH # Szenzor inicializálása
        self.sensors = [] # Szenzorok inicializálása

        # Szenzorok hozzáadása az autóhoz
        self.add_sensors(NUM_SENSORS, SENSOR_ANGLE_RANGE)


    def add_sensors(self, num_sensors, angle_range):
        angle_increment = angle_range / (num_sensors - 1)  # A szenzorok közötti szög
        start_angle = -angle_range / 2  # Az első szenzor szöge

        for i in range(num_sensors):
            angle = start_angle + i * angle_increment
            self.add_sensor(angle)

    def add_sensor(self, angle):
        self.sensors.append(math.radians(angle))  # A szöget radiánba konvertáljuk

    def get_max_velocity(self):
        return self.max_vel

    def get_velocity(self):
        return self.vel

    def get_rotation_velocity(self):
        return self.rotation_vel

    def get_position(self):
        return self.x, self.y

    def get_acceleration(self):
        return self.acceleration

    def set_max_velocity(self, max_vel):
        self.max_vel = max_vel

    def set_velocity(self, vel):
        self.vel = vel

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
    def draw(self, win):
        rotate_to_center(win, self.car, (self.x, self.y), self.angle)
        self.draw_sensors(win)

    """ Az érzékelők rajzolása """

    def draw_sensors(self, win):
        for sensor_angle in self.sensors:
            # Az érzékelő szöge az autó szögéhez képest
            absolute_sensor_angle = self.angle + math.degrees(sensor_angle + math.pi / 2)

            # Az érzékelő kezdőpontjának koordinátái az autó orrában
            start_x = self.center[0] + (CAR_WIDTH / 2) * math.cos(math.radians(self.angle))
            start_y = self.center[1] + (CAR_WIDTH / 2) * math.sin(math.radians(self.angle))

            self.center = (self.x + CAR_WIDTH / 2, self.y + CAR_HEIGHT / 2)  # Az autó középpontja

            # Érzékelők végeinek koordinátái
            end_x = start_x + self.sensor_length * math.cos(math.radians(absolute_sensor_angle))
            end_y = start_y - self.sensor_length * math.sin(math.radians(absolute_sensor_angle))

            # Érzékelők rajzolása
            if self.check_sensor_collision(FIELD_ONLY_MASK, (end_x, end_y)):
                pygame.draw.line(win, (0, 255, 0), self.center, (end_x, end_y), 2)
                pygame.draw.circle(win, (0, 255, 0), (int(end_x), int(end_y)), 5)
            elif self.check_sensor_collision(TRACKSIDE_MASK, (end_x, end_y)):
                pygame.draw.line(win, (255,180,0), self.center, (end_x, end_y), 2)
                pygame.draw.circle(win, (255,180,0), (int(end_x), int(end_y)), 5)
            elif self.check_sensor_collision(GRASS_MASK, (end_x, end_y)):
                pygame.draw.line(win, (255, 0, 0), self.center, (end_x, end_y), 2)
                pygame.draw.circle(win, (255, 0, 0), (int(end_x), int(end_y)), 5)
            elif self.check_sensor_collision(FINISH, (end_x, end_y)):
                pygame.draw.line(win, (0, 0, 255), self.center, (end_x, end_y), 2)
                pygame.draw.circle(win, (0, 0, 255), (int(end_x), int(end_y)), 5)

            # # Ha az érzékelő végpontja a pályán van, akkor a pályán van az autó
            # if self.check_sensor_collision(FIELD_ONLY_MASK, (end_x, end_y)):
            #     print("Car is on the field")
            # # Ha az érzékelő végpontja a fűben van, akkor a fűben van az autó
            # elif self.check_sensor_collision(GRASS_MASK, (end_x, end_y)):
            #     print("Car is on the grass")
            # # Ha az érzékelő végpontja sem a pályán, sem a fűben nincs, akkor máshol van az autó
            # else:
            #     print("Car is somewhere else")

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
            if mask.get_at((sensor_end_x, sensor_end_y)) == 0:  # Ha a pixel átlátszó, akkor nincs ütközés
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
    def collide_grass(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)

    """ Az autó pályára lépését beállító metódus. """
    def collide_trackside(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)
    def collide_finish(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)

    def collide_field(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)

    def collide_border(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)


# Adathalmaz létrehozása (példa)
# Például, itt az inputok színeket (mint számokat) reprezentálnak, és az outputok az autó vezérlését határozzák meg
# Az adatokat lehetne szimulálni a szenzorok valós méréseivel, vagy egy szimulált környezetből származhatnak
# input_data = np.random.rand(num_samples, input_dim)  # Példa véletlenszerű input adatokra
# output_data = np.random.rand(num_samples, output_dim)  # Példa véletlenszerű output adatokra

# Példa adathalmaz betöltése
# Feltehetjük, hogy az adathalmazat előre elkészítették és betöltötték
# input_data, output_data = load_data()


def draw(win, images, player_car):
    for car, pos in images:
        win.blit(car, pos)
    player_car.draw(win)
    player_car.draw_sensors(win)  # Érzékelők rajzolása

def save_sensor_data(sensor_data, filename):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(sensor_data)


# Képek létrehozása és pozíciók beállítása
images = [(GRASS, (0, 0)), (FIELD_ONLY, (0, 0)), (TRACKSIDE, (0, 0)), (FINISH, (69, 152))]

# Autó létrehozása
player_car = Car(4, 4)

# Adatok betöltése
def load_data():
    df = pd.read_csv('sensor_data.csv')
    df = df.replace({'G': 1, 'Y': 2, 'R': 3})
    X = df.iloc[:, :-1].values  # Bemenetek (szenzor adatok)
    y = df.iloc[:, -1].values   # Kimenet (autó vezérlés)
    return X, y

# Adatok előkészítése
def prepare_data(X, y):
    scaler = MinMaxScaler()  # Normalizáló objektum létrehozása
    X_scaled = scaler.fit_transform(X)  # Normalizálás
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)  # Felosztás tanító és teszt adatokra
    return X_train, X_test, y_train, y_test

# Neurális hálózat létrehozása
def create_model(input_dim):
    model = Sequential([
        Dense(64, activation='relu', input_shape=(input_dim,)),
        Dropout(0.2),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(4, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

# Adatok betöltése és előkészítése
X, y = load_data()
X_train, X_test, y_train, y_test = prepare_data(X, y)
#
# # Neurális hálózat létrehozása
# model = create_model(X_train.shape[1])
#
# # Háló tanítása
# model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2)
#
# # Háló értékelése
# test_loss, test_accuracy = model.evaluate(X_test, y_test)
# print("Test Accuracy:", test_accuracy)
#
# # Háló mentése
# model.save('car_control_model.h5')

# Modell betöltése
model = load_model('car_control_model.h5')

# Felület az adatok megjelenítéséhez és vezérléshez
control_surface = pygame.Surface((300, HEIGHT))
control_surface.fill((255, 255, 255))

control_panel = pygame.Surface((300, HEIGHT))
control_panel.fill((200, 200, 200))

# csűszkák létrehozása
max_velocity_slider = Slider(WIN, WIDTH - 210, 170, 160, 15, min=0, max=10, step=0.1,
                             initial=player_car.get_max_velocity())
# output = TextBox(WIN, WIDTH - 200, 200, 50, 50, fontSize=20)

rotation_velocity_slider = Slider(WIN, WIDTH - 210, 90, 160, 15, min=0, max=10, step=0.1,
                                      initial=player_car.get_rotation_velocity())
# output2 = TextBox(WIN, WIDTH - 400, 300, 50, 50, fontSize=20)

acceleration_slider = Slider(WIN, WIDTH - 210, 250, 160, 15, min=0, max=1, step=0.1,
                                        initial=player_car.get_acceleration())

# Adatgyűjtés szenzorok alapján
def collect_sensor_data(car):
    sensor_data = []
    for sensor_angle in car.sensors:
        # Az érzékelő szöge az autó szögéhez képest
        absolute_sensor_angle = car.angle + math.degrees(sensor_angle + math.pi / 2)

        # Az érzékelő kezdőpontjának koordinátái az autó orrában
        start_x = car.center[0] + (CAR_WIDTH / 2) * math.cos(math.radians(car.angle))
        start_y = car.center[1] + (CAR_WIDTH / 2) * math.sin(math.radians(car.angle))

        # Érzékelők végeinek koordinátái
        end_x = start_x + car.sensor_length * math.cos(math.radians(absolute_sensor_angle))
        end_y = start_y - car.sensor_length * math.sin(math.radians(absolute_sensor_angle))

        # Ha az érzékelő végpontja a pályán van, akkor tároljuk a szenzor által mért távolságot
        if car.check_sensor_collision(FIELD_ONLY_MASK, (end_x, end_y)):
            sensor_data.append("G")  # Pályán
        elif car.check_sensor_collision(TRACKSIDE_MASK, (end_x, end_y)):
            sensor_data.append("Y")
        else:
            sensor_data.append("R")  # Füvön

    return sensor_data



""" A program fő ciklusa, amely a játékot vezérli. """
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Adatgyűjtés szenzorok alapján
    sensor_data = collect_sensor_data(player_car)

    # Az adatokat folyamatosan hozzáfűzzük a CSV fájlhoz
    # save_sensor_data(sensor_data, 'sensor_data.csv')


    # # Formázzuk az adatokat egy NumPy tömbbé
    # sensor_data_array = np.array(sensor_data)
    # print("Sensor Data:")
    # print(sensor_data_array)

    # StandardScaler objektum létrehozása és illesztése az adathalmazra
    scaler = StandardScaler()
    scaler.fit(X_train)  # X_train az illesztendő adathalmaz

    # Adatok átalakítása numerikus formátumba
    numeric_sensor_data = [1 if data == 'G' else 2 if data == 'Y' else 3 for data in sensor_data]

    # Használjuk a betanított modellt az előrejelzéshez
    predicted_control = model.predict(np.array([numeric_sensor_data]))

    # Kiválasztjuk a legvalószínűbb osztályt
    predicted_class = np.argmax(predicted_control)

    # Az előrejelzett vezérlést alkalmazzuk az autóra
    if predicted_class == 1:
        player_car.move_forward()
    elif predicted_class == 2:
        player_car.move_forward()
        player_car.rotate(left=True)
    elif predicted_class == 3:
        player_car.move_forward()
        player_car.rotate(right=True)


    draw(WIN, images, player_car)
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
    if player_car.collide_grass(FIELD_ONLY_MASK) or player_car.collide_trackside(TRACKSIDE_MASK):
        # print("Field")

        max_velocity_slider.listen(events)
        max_velocity_slider.draw()

        player_car.set_max_velocity(max_velocity_slider.getValue())
        # output.setText(round(max_velocity_slider.getValue(), 2))


        rotation_velocity_slider.listen(events)
        rotation_velocity_slider.draw()

        player_car.set_rotation_velocity(rotation_velocity_slider.getValue())
        # output2.setText(round(rotation_velocity_slider.getValue(), 2))

        acceleration_slider.listen(events)
        acceleration_slider.draw()

        player_car.set_acceleration(acceleration_slider.getValue())

    else: # Ha a játékos fűre lép akkor a maximális sebesség és a forgási sebesség lelassul egy fix értékre
        # print("Grass")
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
    pygame_widgets.update(events)
    pygame.display.update()
    pygame.time.Clock().tick(FPS)
