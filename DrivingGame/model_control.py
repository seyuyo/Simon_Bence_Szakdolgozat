import numpy as np


# Szenzorértékek kódolása. Ugyanezt használja a tanítás (model.py) és a vezérlés is,
# különben a háló mást kap futás közben, mint amin tanult.
SENSOR_ENCODING = {'G': 0, 'Y': 1, 'R': 2, 'B': 3, 'O': 4}

# Irány osztályok (a háló direction_output kimenetének indexei)
FORWARD, LEFT, RIGHT, FORWARD_LEFT, FORWARD_RIGHT = range(5)
DIRECTION_NAMES = ["előre", "balra", "jobbra", "előre + balra", "előre + jobbra"]


def encode_sensors(sensor_data):
    """ Szenzoradatok (pl. ['G', 'Y', ...]) átalakítása a háló bemenetévé, [0, 1] tartományba. """
    return np.array([SENSOR_ENCODING[s] for s in sensor_data], dtype=np.float32) / (len(SENSOR_ENCODING) - 1)


def apply_direction(car, direction):
    if direction == FORWARD:
        car.move_forward()
    elif direction == LEFT:
        car.rotate(left=True)
        car.move()
    elif direction == RIGHT:
        car.rotate(right=True)
        car.move()
    elif direction == FORWARD_LEFT:
        car.move_forward()
        car.rotate(left=True)
    elif direction == FORWARD_RIGHT:
        car.move_forward()
        car.rotate(right=True)


def apply_advanced_model_control(car, model, sensor_data):
    if any(s not in SENSOR_ENCODING for s in sensor_data):
        print("Hiba: Ismeretlen szenzoradat.")
        return

    # model(...) közvetlen hívása képkockánként sokkal gyorsabb, mint a model.predict(...)
    velocity, direction = model(encode_sensors(sensor_data)[np.newaxis, :], training=False)
    predicted_velocity = float(velocity[0, 0])
    predicted_direction = int(np.argmax(direction[0]))

    car.set_velocity(min(predicted_velocity, car.get_max_velocity()))
    apply_direction(car, predicted_direction)
