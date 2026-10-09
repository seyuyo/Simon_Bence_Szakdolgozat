"""
Q-tanulás: táblázatos megerősítéses tanulás a szenzoradatokon.

Tanítás ablak nélkül:   python qlearning.py [epizódok száma]
Futtatás a játékban:    python main.py qlearning
"""
import json
import os
import sys

import numpy as np

from assets import BASE_DIR
from model_control import apply_direction, DIRECTION_NAMES
from sensors import NUM_SENSORS

Q_TABLE_FILE = os.path.join(BASE_DIR, "q_table_v2.npy")
REWARDS_FILE = os.path.join(BASE_DIR, "rewards_v2.json")
REFERENCE_PATH_FILE = os.path.join(BASE_DIR, "reference_path.json")

# Szenzorértékek leképezése különböző felületekre
sensor_values = {
    'G': 0,  # Pálya
    'Y': 1,  # Pálya széle
    'R': 2,  # Fű
    'B': 3,  # Gyalogos
    'O': 4   # Sár
}

STATE_SIZE = len(sensor_values) ** NUM_SENSORS
ACTION_SIZE = len(DIRECTION_NAMES)


# Állapot kinyerése a szenzor adatokból: 5-ös számrendszerbeli szám, így a szenzorok
# sorrendje is számít (az egyszerű összeg pl. a bal és jobb oldali fűt nem különböztetné meg)
def get_state_from_sensors(sensor_data):
    state = 0
    for data in sensor_data:
        state = state * len(sensor_values) + sensor_values[data]
    return state


class QLearningAgent:
    def __init__(self, action_size=ACTION_SIZE, state_size=STATE_SIZE, learning_rate=0.1, discount_factor=0.95,
                 initial_exploration_rate=0.5, exploration_decay=0.99, min_exploration_rate=0.01):
        self.action_size = action_size  # Az elérhető akciók száma
        self.state_size = state_size  # A lehetséges állapotok száma
        self.learning_rate = learning_rate  # Tanulási ráta (alfa)
        self.discount_factor = discount_factor  # Diszkont faktor (gamma)
        self.exploration_rate = initial_exploration_rate  # Kezdeti felfedezési ráta (epszilon)
        self.exploration_decay = exploration_decay  # A felfedezési ráta csökkenési üteme (epizódonként)
        self.min_exploration_rate = min_exploration_rate  # Minimális felfedezési ráta
        self.q_table = np.zeros((state_size, action_size))  # Q-táblázat inicializálása nullákkal
        self.rng = np.random.default_rng()

    def decide_action(self, state, explore=True):
        # Akció kiválasztása epsilon-greedy stratégia alapján
        if explore and self.rng.random() < self.exploration_rate:
            # Véletlenszerű akció választása (exploration)
            return int(self.rng.integers(self.action_size))
        # Legjobb akció választása (exploitation)
        return int(np.argmax(self.q_table[state]))

    def update_policy(self, state, action, reward, next_state, done=False):
        # Q-táblázat frissítése a Q-learning egyenlettel
        old_value = self.q_table[state, action]
        future_q = 0.0 if done else np.max(self.q_table[next_state])
        # Új Q-érték számítása
        new_value = (1 - self.learning_rate) * old_value + self.learning_rate * (reward + self.discount_factor * future_q)
        self.q_table[state, action] = new_value

    def end_episode(self):
        # Felfedezési ráta csökkentése
        self.exploration_rate = max(self.exploration_rate * self.exploration_decay, self.min_exploration_rate)

    def save(self, filename=Q_TABLE_FILE):
        np.save(filename, self.q_table)

    def load(self, filename=Q_TABLE_FILE):
        self.q_table = np.load(filename)


class ReferencePath:
    """
    A pálya mentén haladás mérése: a szabályalapú vezérlő egy körének útvonala.
    A jutalom az ezen mért előrehaladás, így az autó nem kap jutalmat azért, ha egy helyben köröz.
    """

    def __init__(self, points):
        self.points = np.asarray(points, dtype=float)

    @classmethod
    def load_or_record(cls):
        if os.path.exists(REFERENCE_PATH_FILE):
            with open(REFERENCE_PATH_FILE) as f:
                return cls(json.load(f))
        path = cls(record_reference_lap())
        with open(REFERENCE_PATH_FILE, "w") as f:
            json.dump([[round(x, 1), round(y, 1)] for x, y in path.points], f)
        return path

    def index_of(self, position, hint=None, window=40):
        """ A legközelebbi útvonalpont indexe (hint körül keres, hogy a kereszteződésnél ne ugorjon). """
        n = len(self.points)
        if hint is None:
            candidates = np.arange(n)
        else:
            candidates = np.arange(hint - window, hint + window + 1) % n
        distances = np.linalg.norm(self.points[candidates] - np.asarray(position), axis=1)
        return int(candidates[np.argmin(distances)])

    def progress(self, old_index, new_index):
        """ Előrehaladás pontokban (negatív, ha visszafelé ment), a kör végén átfordulva. """
        n = len(self.points)
        delta = (new_index - old_index) % n
        return delta - n if delta > n // 2 else delta


def record_reference_lap(max_frames=2000):
    """ Egy kör a szabályalapú vezérlővel; az autó középpontjainak listája. """
    import controllers
    from simulation import Simulation, lap_frame

    sim = Simulation()
    start = sim.car.center
    positions = []
    for _ in range(max_frames):
        sim.step(controllers.rule_controller)
        positions.append(sim.car.center)
        lap = lap_frame(positions, start)
        if lap is not None:
            return positions[:lap]
    raise RuntimeError("A szabályalapú vezérlő nem tett meg egy kört, nincs referencia útvonal.")


# Jutalmak beállítása
def compute_reward(sim, progress, pedestrian_hit):
    """ Jutalom egy lépésért, és hogy véget ért-e az epizód. """
    if not sim.on_track():
        return -100.0, True  # büntetés pályaelhagyás esetén, az epizód véget ér
    reward = float(progress)  # jutalom a pálya mentén megtett útért
    if pedestrian_hit:
        reward -= 100.0  # büntetés gyalogos elütéséért
    if sim.car.get_velocity() < 1:
        reward -= 1.0  # büntetés, ha az autó nem mozog
    return reward, False


class QLearningController:
    """ Betanított Q-táblával vezet (felfedezés nélkül). """

    def __init__(self, agent):
        self.agent = agent

    @classmethod
    def load(cls, filename=Q_TABLE_FILE):
        agent = QLearningAgent()
        if os.path.exists(filename):
            agent.load(filename)
        else:
            print(f"Nincs betanított Q-tábla ({filename}), előbb futtasd: python qlearning.py")
        return cls(agent)

    def __call__(self, car, sensor_data):
        action = self.agent.decide_action(get_state_from_sensors(sensor_data), explore=False)
        apply_direction(car, action)


def run_episode(sim, agent, path, max_steps, explore=True, learn=True):
    """ Egy epizód a rajttól; visszaadja az összjutalmat és a megtett utat (útvonalpontokban). """
    sim.reset()
    index = path.index_of(sim.car.center)
    total_reward, total_progress = 0.0, 0
    sensor_data = sim.sensor_data()
    state = get_state_from_sensors(sensor_data)

    for _ in range(max_steps):
        action = agent.decide_action(state, explore)
        hits_before = sim.pedestrian_hits
        sensor_data = sim.step(lambda car, _: apply_direction(car, action))
        new_index = path.index_of(sim.car.center, hint=index)
        progress = path.progress(index, new_index)
        index = new_index

        reward, done = compute_reward(sim, progress, sim.pedestrian_hits > hits_before)
        new_state = get_state_from_sensors(sim.sensor_data())
        if learn:
            agent.update_policy(state, action, reward, new_state, done)
        state = new_state
        total_reward += reward
        total_progress += progress
        if done:
            break
    return total_reward, total_progress


def train(episodes=3000, max_steps=1500, max_pedestrians=2, max_muds=1, seed=0):
    """ Tanítás; minden epizódban 0..max_pedestrians gyalogos és 0..max_muds sárfolt véletlen helyen. """
    import random
    from simulation import Simulation, place_random_obstacles

    rng = random.Random(seed)
    path = ReferencePath.load_or_record()
    sim = Simulation()
    agent = QLearningAgent()
    agent.rng = np.random.default_rng(seed)
    rewards_per_episode = []

    for episode in range(episodes):
        sim.clear_obstacles()
        sim.reset()
        place_random_obstacles(sim, rng, rng.randint(0, max_pedestrians), rng.randint(0, max_muds))
        total_reward, total_progress = run_episode(sim, agent, path, max_steps)
        agent.end_episode()
        rewards_per_episode.append((episode, round(total_reward, 1), int(total_progress)))
        if episode % 100 == 0 or episode == episodes - 1:
            recent = rewards_per_episode[-100:]
            print(f"epizód {episode}: átlagos jutalom {np.mean([r[1] for r in recent]):.0f}, "
                  f"átlagos út {np.mean([r[2] for r in recent]):.0f}/{len(path.points)} pont, "
                  f"epszilon {agent.exploration_rate:.3f}")

    agent.save(Q_TABLE_FILE)
    with open(REWARDS_FILE, "w") as f:
        json.dump(rewards_per_episode, f)
    print(f"Q-tábla elmentve: {Q_TABLE_FILE}")
    return agent, rewards_per_episode


if __name__ == "__main__":
    train(episodes=int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
