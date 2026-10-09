"""
Az autó szenzorai.

Minden szenzor egy, az autó orrából induló sugár. Két dolgot mér:
- read_sensors: milyen felület van a sugár végén (SENSOR_LENGTH távolságban),
  ezt használja a szabályalapú vezérlő és az első neurális háló;
- read_distances: milyen messze van a sugár mentén az első nem-aszfalt pont
  (pálya széle, fű, akadály), legfeljebb SENSOR_RANGE távolságig. Ehhez sűrűbb, szélesebb
  legyezőt használunk (DISTANCE_ANGLES), hogy a kis gyalogos se essen két sugár közé.

A szenzorok sorrendje mindkét esetben jobbról balra halad (0. = jobbra előre).
"""
import math

from assets import PEDESTRIAN, MUD, FIELD_ONLY_MASK, TRACKSIDE_MASK

# A szenzorok számát és elhelyezkedését beállíthatod az alábbi konstansokkal
NUM_SENSORS = 6  # Szenzorok száma
SENSOR_ANGLE_RANGE = 90  # A szenzorok által lefedett szög
SENSOR_LENGTH = 40  # szenzor hossza (felület érzékelés)
SENSOR_RANGE = 160  # távolságmérés legnagyobb hatótávja
NUM_DISTANCE_SENSORS = 13  # távolságmérő sugarak száma
DISTANCE_ANGLE_RANGE = 180  # a távolságmérő sugarak által lefedett szög (oldalra is lát)
DISTANCE_STEP = 4  # távolságmérés lépésköze pixelben

# szenzorok szöge az autó haladási irányához képest (fokban, pozitív = balra)
SENSOR_ANGLES = [-SENSOR_ANGLE_RANGE / 2 + i * SENSOR_ANGLE_RANGE / (NUM_SENSORS - 1)
                 for i in range(NUM_SENSORS)]
DISTANCE_ANGLES = [-DISTANCE_ANGLE_RANGE / 2 + i * DISTANCE_ANGLE_RANGE / (NUM_DISTANCE_SENSORS - 1)
                   for i in range(NUM_DISTANCE_SENSORS)]

# Felületek jelölése és megjelenítési színe
SENSOR_COLORS = {
    'G': (0, 255, 0),  # Zöld: pálya
    'Y': (255, 180, 0),  # Sárga: pálya széle
    'R': (255, 0, 0),  # Piros: fű
    'B': (0, 0, 0),  # Fekete: gyalogos
    'O': (255, 87, 34),  # Narancs: sár
}


def _mask_hit(mask, x, y):
    x, y = round(x), round(y)
    width, height = mask.get_size()
    return 0 <= x < width and 0 <= y < height and mask.get_at((x, y)) != 0


def surface_at(point, obstacles):
    """ Milyen felület van az adott ponton: 'G', 'Y', 'R', 'B' vagy 'O'. """
    for obstacle in obstacles:
        if obstacle.rect.collidepoint(point):
            return 'B' if obstacle.image is PEDESTRIAN else 'O' if obstacle.image is MUD else 'R'
    x, y = point
    if _mask_hit(FIELD_ONLY_MASK, x, y):
        return 'G'
    if _mask_hit(TRACKSIDE_MASK, x, y):
        return 'Y'
    # a fű és minden, ami a pályán kívül esik
    return 'R'


def sensor_direction(car, sensor_angle):
    radians = math.radians(car.angle + sensor_angle)
    return -math.sin(radians), -math.cos(radians)


def sensor_segments(car, length=SENSOR_LENGTH, angles=SENSOR_ANGLES):
    """ A szenzorsugarak kezdő- és végpontjai (rajzoláshoz és méréshez). """
    start_x, start_y = car.nose()
    segments = []
    for sensor_angle in angles:
        dx, dy = sensor_direction(car, sensor_angle)
        segments.append(((start_x, start_y), (start_x + dx * length, start_y + dy * length)))
    return segments


def read_sensors(car, obstacles):
    """ Felület a szenzorok végén, pl. ['G', 'G', 'Y', 'G', 'G', 'R']. """
    return [surface_at(end, obstacles) for _, end in sensor_segments(car)]


def read_distances(car, obstacles):
    """
    Távolság az első nem-aszfalt pontig minden szenzor mentén, [0, 1] tartományba skálázva
    (1 = SENSOR_RANGE távolságon belül csak pálya van), és hogy mi van ott.

    Ha a sugár eleve nem aszfalton indul (az autó orra a pályán kívül vagy sárban van), akkor
    negatív érték: -(távolság a legközelebbi aszfaltig), illetve -1, ha a hatótávon belül nincs aszfalt.
    Így a pályáról letért autó is tudja, merre van vissza az út.
    """
    start_x, start_y = car.nose()
    distances, surfaces = [], []
    for sensor_angle in DISTANCE_ANGLES:
        dx, dy = sensor_direction(car, sensor_angle)
        start_surface = surface_at((start_x, start_y), obstacles)
        if start_surface != 'G':
            distance = -SENSOR_RANGE
            for step in range(DISTANCE_STEP, SENSOR_RANGE + 1, DISTANCE_STEP):
                if surface_at((start_x + dx * step, start_y + dy * step), obstacles) == 'G':
                    distance = -step
                    break
            distances.append(distance / SENSOR_RANGE)
            surfaces.append(start_surface)
            continue

        distance, surface = SENSOR_RANGE, 'G'
        for step in range(DISTANCE_STEP, SENSOR_RANGE + 1, DISTANCE_STEP):
            found = surface_at((start_x + dx * step, start_y + dy * step), obstacles)
            if found != 'G':
                distance, surface = step, found
                break
        distances.append(distance / SENSOR_RANGE)
        surfaces.append(surface)
    return distances, surfaces
