"""
Távolságmérő szenzorokat használó neurális háló (a "model" vezérlési mód).

A háló a szakértő vezérlőt (expert.py) utánozza: bemenete a távolságmérő sugarak értéke, hogy
gyalogost vagy sarat látnak-e, és az autó sebessége; kimenete a kormányzás és a célsebesség.

Tanítás:   python distance_model.py
  1. adatgyűjtés a szakértővel, véletlen akadályokkal és időnként véletlen kormánymozdulatokkal
     (így a háló azt is látja, hogyan kell visszatérni, ha kicsit letért a jó útról);
  2. tanítás;
  3. DAgger: a betanított háló vezet, a szakértő minden helyzetben megmondja, mit tett volna,
     ezeket az adatokat hozzáadjuk és újratanítunk.
"""
import os
import random

import numpy as np

import expert
from assets import BASE_DIR
from sensors import read_distances, NUM_DISTANCE_SENSORS
from simulation import Simulation, place_random_obstacles

MODEL_FILE = os.path.join(BASE_DIR, "distance_model.keras")
DATA_FILE = os.path.join(BASE_DIR, "distance_driving_data.npz")  # újragenerálható, nincs a repóban
NUM_FEATURES = 3 * NUM_DISTANCE_SENSORS + 1


def features(distances, surfaces, velocity, max_velocity):
    """ A háló bemenete: távolságok, gyalogos/sár jelzők sugaranként, relatív sebesség. """
    pedestrian = [1.0 if s == 'B' else 0.0 for s in surfaces]
    mud = [1.0 if s == 'O' else 0.0 for s in surfaces]
    return np.array(list(distances) + pedestrian + mud + [velocity / max(max_velocity, 1e-6)],
                    dtype=np.float32)


def collect(episodes, frames=1500, policy=None, noise=0.03, seed=0):
    """
    Adatgyűjtés. A címke mindig a szakértő döntése; az autót a policy vezeti
    (None = maga a szakértő), noise valószínűséggel pedig pár képkockányi véletlen kormányzás.
    """
    rng = random.Random(seed)
    sim = Simulation()
    X, y_steering, y_velocity = [], [], []
    for _ in range(episodes):
        sim.clear_obstacles()
        sim.reset()
        place_random_obstacles(sim, rng, pedestrians=rng.randint(0, 4), muds=rng.randint(0, 3))
        random_steps, random_steering = 0, expert.STRAIGHT

        for _ in range(frames):
            car = sim.car
            distances, surfaces = read_distances(car, sim.obstacles)
            steering, target_velocity = expert.decide(distances, surfaces, car.vel, car.max_vel)
            x = features(distances, surfaces, car.vel, car.max_vel)
            X.append(x)
            y_steering.append(steering)
            y_velocity.append(target_velocity / car.max_vel)

            # mit hajtunk végre: a szakértő, a háló, vagy egy rövid véletlen kitérés
            if random_steps == 0 and rng.random() < noise:
                random_steps, random_steering = rng.randint(3, 12), rng.choice([expert.LEFT, expert.RIGHT])
            if random_steps > 0:
                random_steps -= 1
                action = (random_steering, target_velocity)
            elif policy is not None:
                action = policy(x, car.max_vel)
            else:
                action = (steering, target_velocity)
            sim.step(lambda c, _: expert.drive(c, *action))
    return np.array(X), np.array(y_steering), np.array(y_velocity, dtype=np.float32)


def create_model():
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Dense

    inputs = Input(shape=(NUM_FEATURES,))
    x = Dense(128, activation='relu')(inputs)
    x = Dense(64, activation='relu')(x)
    x = Dense(32, activation='relu')(x)
    steering_output = Dense(len(expert.STEERING_NAMES), activation='softmax', name='steering_output')(x)
    velocity_output = Dense(1, activation='sigmoid', name='velocity_output')(x)  # célsebesség / max sebesség

    model = Model(inputs=inputs, outputs=[steering_output, velocity_output])
    model.compile(optimizer='adam',
                  loss={'steering_output': 'sparse_categorical_crossentropy',
                        'velocity_output': 'mean_squared_error'},
                  loss_weights={'steering_output': 1.0, 'velocity_output': 5.0},
                  metrics={'steering_output': ['accuracy'], 'velocity_output': ['mae']})
    return model


def fit(model, X, y_steering, y_velocity, epochs=40):
    from tensorflow.keras.callbacks import EarlyStopping

    return model.fit(X, {'steering_output': y_steering, 'velocity_output': y_velocity},
                     epochs=epochs, batch_size=256, validation_split=0.15, verbose=2,
                     callbacks=[EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True)])


class DistanceModelController:
    """ controller(car, sensor_data) alakú vezérlő: a háló dönt, az expert.drive hajtja végre. """

    def __init__(self, model, sim_obstacles):
        self.model = model
        self.obstacles = sim_obstacles  # a szimuláció akadálylistája (ugyanaz az objektum)

    def decide(self, x, max_velocity):
        steering, velocity = self.model(x[np.newaxis, :], training=False)
        return int(np.argmax(steering[0])), float(velocity[0, 0]) * max_velocity

    def __call__(self, car, sensor_data):
        distances, surfaces = read_distances(car, self.obstacles)
        x = features(distances, surfaces, car.vel, car.max_vel)
        expert.drive(car, *self.decide(x, car.max_vel))


def load_trained_model(path=MODEL_FILE):
    from tensorflow.keras.models import load_model
    return load_model(path, compile=False)


def train(expert_episodes=60, dagger_rounds=2, dagger_episodes=30):
    print(f"Adatgyűjtés a szakértővel ({expert_episodes} epizód)...")
    X, y_steering, y_velocity = collect(expert_episodes, seed=0)
    model = create_model()
    fit(model, X, y_steering, y_velocity)

    for round_ in range(1, dagger_rounds + 1):
        print(f"DAgger {round_}. kör: a háló vezet, a szakértő címkéz ({dagger_episodes} epizód)...")
        controller = DistanceModelController(model, [])
        X2, s2, v2 = collect(dagger_episodes, policy=controller.decide, noise=0.0, seed=1000 * round_)
        X, y_steering, y_velocity = (np.concatenate([X, X2]), np.concatenate([y_steering, s2]),
                                     np.concatenate([y_velocity, v2]))
        fit(model, X, y_steering, y_velocity)

    np.savez_compressed(DATA_FILE, X=X, steering=y_steering, velocity=y_velocity)
    model.save(MODEL_FILE)
    print(f"{len(X)} minta, modell elmentve: {MODEL_FILE}")
    return model


if __name__ == "__main__":
    train()
