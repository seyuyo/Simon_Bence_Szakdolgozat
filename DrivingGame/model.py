"""
A felügyelt tanulású (SL) modell tanítása és betöltése.

Tanítás:   python model.py            (kimenet: MODEL_FILE)
Betöltés:  model.load_trained_model() (a main.py hívja, csak ha modell vezérli az autót)
"""
import os
import builtins

import numpy as np

import automated_car
from model_control import (encode_sensors, FORWARD, LEFT, RIGHT, FORWARD_LEFT, FORWARD_RIGHT,
                           DIRECTION_NAMES)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'automated_driving_data_full.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'automated_trained_model_v2.keras')
SENSOR_COLUMNS = ['sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5', 'sensor_6']


class _RecordingCar:
    """ Ál-autó, amely csak feljegyzi, mit csinálna vele a szabályalapú vezérlő. """

    def __init__(self, velocity):
        self.velocity = velocity
        self.rotation = 0
        self.forward = False

    def get_velocity(self):
        return self.velocity

    def move_forward(self):
        self.forward = True

    def move_backward(self):
        pass

    def slowing(self):
        pass

    def rotate(self, left=False, right=False):
        self.rotation += 1 if left else -1 if right else 0


def direction_label(sensor_data, velocity):
    """
    Irány címke előállítása a szabályalapú vezérlő (automated_car) döntéséből.
    A CSV csak sebességet tartalmaz, ezért enélkül a direction_output kimenetnek nincs mit tanulnia.
    """
    car = _RecordingCar(velocity)
    original_print = builtins.print
    builtins.print = lambda *args, **kwargs: None  # az automated_car sokat ír a konzolra
    try:
        automated_car.apply_control(car, list(sensor_data))
    finally:
        builtins.print = original_print

    if car.rotation > 0:
        return FORWARD_LEFT if car.forward else LEFT
    if car.rotation < 0:
        return FORWARD_RIGHT if car.forward else RIGHT
    return FORWARD


def load_data():
    import pandas as pd

    df = pd.read_csv(DATA_FILE)
    sensors = df[SENSOR_COLUMNS].values
    X = np.stack([encode_sensors(row) for row in sensors])
    y_velocity = df['velocity'].values.astype(np.float32)
    y_direction = np.array([direction_label(row, v) for row, v in zip(sensors, y_velocity)])
    return X, y_velocity, y_direction


def create_model(input_dim, optimizer):
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Dense, Dropout

    input_layer = Input(shape=(input_dim,))
    x = Dense(128, activation='relu')(input_layer)
    x = Dropout(0.2)(x)
    x = Dense(64, activation='relu')(x)
    x = Dense(32, activation='relu')(x)

    velocity_output = Dense(1, name='velocity_output')(x)
    direction_output = Dense(len(DIRECTION_NAMES), activation='softmax', name='direction_output')(x)

    model = Model(inputs=input_layer, outputs=[velocity_output, direction_output])
    model.compile(optimizer=optimizer,
                  loss={'velocity_output': 'mean_squared_error',
                        'direction_output': 'sparse_categorical_crossentropy'},
                  loss_weights={'velocity_output': 0.1, 'direction_output': 1.0},
                  metrics={'velocity_output': ['mae'],
                           'direction_output': ['accuracy']})
    return model


def train(optimizer_name='rmsprop', epochs=100):
    from sklearn.model_selection import train_test_split
    from tensorflow.keras.optimizers import Adam, SGD, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

    optimizers = {
        'adam': lambda: Adam(learning_rate=0.001),
        'sgd': lambda: SGD(learning_rate=0.001, momentum=0.9, nesterov=True),
        'rmsprop': lambda: RMSprop(learning_rate=0.001),
    }

    X, y_velocity, y_direction = load_data()
    print("Irány címkék eloszlása:",
          {DIRECTION_NAMES[i]: int(n) for i, n in enumerate(np.bincount(y_direction, minlength=5))})

    (X_train, X_test, yv_train, yv_test, yd_train, yd_test) = train_test_split(
        X, y_velocity, y_direction, test_size=0.2, random_state=42, stratify=y_direction)

    model = create_model(X_train.shape[1], optimizers[optimizer_name]())
    callbacks = [EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
                 ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)]
    history = model.fit(X_train, {'velocity_output': yv_train, 'direction_output': yd_train},
                        epochs=epochs, batch_size=64, validation_split=0.2, callbacks=callbacks)

    results = model.evaluate(X_test, {'velocity_output': yv_test, 'direction_output': yd_test},
                             return_dict=True, verbose=0)
    print("Teszt eredmények:", results)
    model.save(MODEL_FILE)
    print(f"Modell elmentve: {MODEL_FILE}")
    return history


def load_trained_model(path=MODEL_FILE):
    from tensorflow.keras.models import load_model
    return load_model(path, compile=False)


if __name__ == '__main__':
    train()
