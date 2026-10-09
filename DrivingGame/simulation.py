"""
A szimuláció megjelenítés nélkül: autó, akadályok, terep hatása, ütközések.
A main.py ezt rajzolja ki, a tanító/kiértékelő szkriptek pedig ablak nélkül futtatják.
"""
import random

import numpy as np

import obstacles as obstacles_module
from assets import (WIDTH, HEIGHT, PANEL_WIDTH, CAR_HEIGHT, PEDESTRIAN, MUD,
                    FIELD_ONLY_MASK, TRACKSIDE_MASK, GRASS_MASK)
from car import Car
from sensors import read_sensors

# Terep hatása: fűn és sárban az autó lassabb és nehezebben fordul
GRASS_LIMITS = {"max_vel": 2, "rotation_vel": 2, "acceleration": 0.05}
MUD_LIMITS = {"max_vel": 1.5, "rotation_vel": 3, "acceleration": 0.05}


class Simulation:
    def __init__(self, max_vel=4, rotation_vel=6, acceleration=0.1):
        # A pályán érvényes beállítások (a csúszkák ezeket módosítják)
        self.track_settings = {"max_vel": max_vel, "rotation_vel": rotation_vel, "acceleration": acceleration}
        self.obstacles = []
        self.reset()

    def reset(self):
        s = self.track_settings
        self.car = Car(s["max_vel"], s["rotation_vel"], s["acceleration"])
        self.frame = 0
        self.pedestrian_hits = 0  # hány gyalogost ütött el az autó
        self.offtrack_frames = 0  # hány képkockán át volt az autó a pályán kívül
        self._touching = set()

    # --- akadályok ---------------------------------------------------------

    def add_obstacle(self, image, position=None):
        if position is None:
            position = random_position_within_mask(FIELD_ONLY_MASK, image.get_width(), image.get_height())
        obstacle = obstacles_module.Obstacle(image, position)
        self.obstacles.append(obstacle)
        return obstacle

    def add_pedestrian(self, position=None):
        return self.add_obstacle(PEDESTRIAN, position)

    def add_mud(self, position=None):
        return self.add_obstacle(MUD, position)

    def clear_obstacles(self):
        self.obstacles.clear()
        self._touching.clear()

    def touched_obstacles(self):
        """ Azok az akadályok, amelyekkel az (elforgatott) autó éppen érintkezik. """
        car_mask, rect = self.car.rotated_mask()
        return [o for o in self.obstacles
                if car_mask.overlap(o.mask, (o.rect.x - rect.x, o.rect.y - rect.y))]

    # --- terep ------------------------------------------------------------

    def on_track(self):
        return bool(self.car.collide(FIELD_ONLY_MASK) or self.car.collide(TRACKSIDE_MASK))

    def apply_terrain(self, touched):
        car = self.car
        if any(o.image is MUD for o in touched):
            limits = MUD_LIMITS
        elif self.on_track():
            limits = self.track_settings
        elif car.collide(GRASS_MASK):
            limits = GRASS_LIMITS
        else:
            limits = self.track_settings
        car.set_max_velocity(limits["max_vel"])
        car.set_rotation_velocity(limits["rotation_vel"])
        car.set_acceleration(limits["acceleration"])
        car.vel = min(car.vel, car.max_vel)

    def keep_inside_window(self):
        car = self.car
        car.x = min(max(car.x, 0), WIDTH - PANEL_WIDTH - 40)
        car.y = min(max(car.y, 0), HEIGHT - CAR_HEIGHT)
        car.update_center()

    # --- egy lépés --------------------------------------------------------

    def sensor_data(self):
        return read_sensors(self.car, self.obstacles)

    def step(self, controller):
        """
        Egy képkocka: szenzorok leolvasása, vezérlés, terep és ütközések kezelése.
        controller(car, sensor_data) mozgatja az autót.
        """
        sensor_data = self.sensor_data()
        controller(self.car, sensor_data)

        touched = self.touched_obstacles()
        for obstacle in touched:
            # egy gyalogossal való érintkezés csak egyszer számít, amíg az autó rajta van
            if obstacle.image is PEDESTRIAN and id(obstacle) not in self._touching:
                self.pedestrian_hits += 1
        self._touching = {id(o) for o in touched}

        self.apply_terrain(touched)
        self.keep_inside_window()
        if not self.on_track():
            self.offtrack_frames += 1
        self.frame += 1
        return sensor_data


def random_position_within_mask(mask, image_width, image_height, rng=random):
    """ Véletlenszerű pozíció, ahol a kép mind a négy sarka és a közepe a maszkon belül van. """
    mask_width, mask_height = mask.get_size()
    while True:
        x = rng.randint(0, mask_width - image_width)
        y = rng.randint(0, mask_height - image_height)
        points = [(x, y), (x + image_width - 1, y), (x, y + image_height - 1),
                  (x + image_width - 1, y + image_height - 1), (x + image_width // 2, y + image_height // 2)]
        if all(mask.get_at(p) != 0 for p in points):
            return x, y


def lap_frame(positions, start, leave_distance=300, return_distance=40):
    """ Melyik képkockán tért vissza az autó a rajthoz, miután eltávolodott tőle (None, ha nem). """
    p = np.asarray(positions, dtype=float)
    distance = np.linalg.norm(p - np.asarray(start, dtype=float), axis=1)
    far = np.nonzero(distance > leave_distance)[0]
    if len(far) == 0:
        return None
    back = np.nonzero(distance[far[0]:] < return_distance)[0]
    return int(far[0] + back[0]) if len(back) else None
