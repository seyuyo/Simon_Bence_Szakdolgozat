"""
Távolságmérő szenzorokat használó szabályalapú vezérlő ("szakértő").

Ez a tanár a távolság alapú neurális hálónak (distance_model.py): adatgyűjtéskor ennek a döntéseit
rögzítjük, a háló pedig ezt tanulja meg utánozni.

Döntés: kormányzás (egyenesen / balra / jobbra) és célsebesség.
"""
import math

from assets import CAR_WIDTH
from sensors import read_distances, DISTANCE_ANGLES, SENSOR_RANGE

STRAIGHT, LEFT, RIGHT = range(3)
STEERING_NAMES = ["egyenesen", "balra", "jobbra"]

CENTER = len(DISTANCE_ANGLES) // 2  # az egyenesen előre néző sugár indexe
STEER_DEADZONE = 7.5  # fok: ennél kisebb eltérésnél egyenesen megy
PEDESTRIAN_PENALTY = 0.2  # gyalogos felé ennyiszer "rövidebbnek" látjuk a szabad utat
MUD_PENALTY = 0.5
PEDESTRIAN_CLEARANCE = CAR_WIDTH + 8  # px: ilyen oldaltávolságon belül elhaladva kitér
PEDESTRIAN_NEAR = 110  # px: ennél közelebbi gyalogosnál figyeli az oldaltávolságot


def effective_distances(distances, surfaces):
    """
    Szabad út sugaranként. A gyalogos és a sár felé rövidebbnek vesszük, és a szomszédos sugarakat is
    csökkentjük, mert az autó szélesebb egy sugárnál (a gyalogosnál kettővel, hogy bőven kikerülje).
    """
    effective = list(distances)
    for i, (distance, surface) in enumerate(zip(distances, surfaces)):
        if distance <= 0:
            continue
        if surface == 'B':
            penalty, spread = PEDESTRIAN_PENALTY, 2
        elif surface == 'O':
            penalty, spread = MUD_PENALTY, 1
        else:
            continue
        for j in range(i - spread, i + spread + 1):
            if 0 <= j < len(effective):
                weight = penalty + (1 - penalty) * abs(j - i) / (spread + 1)
                effective[j] = min(effective[j], distance * weight)
    return effective


def steering_towards(angle):
    if angle > STEER_DEADZONE:
        return LEFT
    if angle < -STEER_DEADZONE:
        return RIGHT
    return STRAIGHT


def decide(distances, surfaces, velocity, max_velocity):
    """ Kormányzás és célsebesség a távolságok és a talált felületek alapján. """
    if max(distances) <= 0:
        # Az autó letért a pályáról (vagy sárban áll): lassan a legközelebbi aszfalt felé
        nearest = max(range(len(distances)), key=lambda i: distances[i])
        if distances[nearest] == -1:  # előtte nincs aszfalt a hatótávon belül: fordul
            return LEFT, 1.0
        return steering_towards(DISTANCE_ANGLES[nearest]), 1.5

    effective = effective_distances(distances, surfaces)

    # Rés keresése: egy irány annyira szabad, amennyire a két szomszédja közül a szűkebb (az autó széles)
    n = len(effective)
    gap = [min(effective[max(i - 1, 0):i + 2]) for i in range(n)]
    best = max(gap)
    # a közel legjobbak közül az egyeneshez legközelebbit választja, hogy ne kanyarogjon feleslegesen
    candidates = [i for i in range(n) if gap[i] >= best - 0.05]
    target = min(candidates, key=lambda i: abs(i - CENTER))
    steering = steering_towards(DISTANCE_ANGLES[target])

    # Közeli gyalogos: ha az autó túl közel haladna el mellette, a másik oldal felé tér ki
    for distance, surface, angle in zip(distances, surfaces, DISTANCE_ANGLES):
        if surface != 'B' or distance * SENSOR_RANGE > PEDESTRIAN_NEAR:
            continue
        lateral = distance * SENSOR_RANGE * math.sin(math.radians(angle))  # pozitív = balra van
        if abs(lateral) < PEDESTRIAN_CLEARANCE:
            steering = RIGHT if lateral > 0 else LEFT
            break

    # Célsebesség: minél közelebb van elöl a pálya széle vagy akadály, annál lassabban
    front = min(effective[CENTER - 1:CENTER + 2])
    target_velocity = 1 + (max_velocity - 1) * min(1.0, front * 1.3)
    if any(s == 'B' and d < 0.6 for d, s in zip(distances, surfaces)):
        target_velocity = min(target_velocity, 1.5)  # gyalogos közelében lassan
    return steering, target_velocity


def drive(car, steering, target_velocity):
    """ Végrehajtás: a sebesség a gyorsulás mértékével közelít a célhoz (fékezés kétszer olyan erős). """
    if car.vel < target_velocity:
        car.vel = min(car.vel + car.acceleration, target_velocity, car.max_vel)
    else:
        car.vel = max(car.vel - 2 * car.acceleration, target_velocity, 0)
    car.vel = min(car.vel, car.max_vel)
    if steering == LEFT:
        car.rotate(left=True)
    elif steering == RIGHT:
        car.rotate(right=True)
    car.move()


class ExpertController:
    """ controller(car, sensor_data) alakú vezérlő; a távolságokat maga méri a szimulációban. """

    def __init__(self, sim_obstacles):
        self.obstacles = sim_obstacles  # a szimuláció akadálylistája (ugyanaz az objektum)

    def __call__(self, car, sensor_data):
        distances, surfaces = read_distances(car, self.obstacles)
        steering, target_velocity = decide(distances, surfaces, car.vel, car.max_vel)
        drive(car, steering, target_velocity)
