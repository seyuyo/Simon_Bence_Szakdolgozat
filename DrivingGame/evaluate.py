"""
Vezérlők kiértékelése ablak nélkül, rögzített forgatókönyveken.

    python evaluate.py [model | rule | qlearning ...]

Forgatókönyvek: üres pálya, valamint egy gyalogos vagy egy sárfolt a pálya hat pontján.
Mérés: kör ideje (képkocka), elütött gyalogosok, pályán kívül töltött képkockák.
"""
import sys

import controllers
from simulation import Simulation, lap_frame

# Akadálypontok a pálya mentén (az akadály középpontja)
OBSTACLE_POINTS = [(185, 112), (567, 227), (794, 175), (603, 590), (364, 653), (457, 378)]


def run_scenario(controller, obstacle=None, point=None, frames=1000, sim=None):
    sim = sim if sim is not None else Simulation()
    sim.clear_obstacles()
    sim.reset()
    if obstacle is not None:
        image = {"ped": "PEDESTRIAN", "mud": "MUD"}[obstacle]
        import assets
        img = getattr(assets, image)
        sim.add_obstacle(img, (point[0] - img.get_width() // 2, point[1] - img.get_height() // 2))
    start = sim.car.center
    positions = []
    for _ in range(frames):
        sim.step(controller)
        positions.append(sim.car.center)
    return {"lap": lap_frame(positions, start), "hits": sim.pedestrian_hits,
            "offtrack": sim.offtrack_frames, "positions": positions}


def evaluate(controller, frames=1000, sim=None):
    results = {"empty": run_scenario(controller, frames=frames, sim=sim)}
    for kind in ("ped", "mud"):
        for point in OBSTACLE_POINTS:
            results[(kind, point)] = run_scenario(controller, kind, point, frames, sim)
    return results


def random_scenarios(controller, episodes=30, frames=1500, pedestrians=3, muds=2, seed=1, sim=None):
    """ Véletlenszerűen elhelyezett akadályok (rögzített seed, így minden vezérlő ugyanazt kapja). """
    import random
    from simulation import place_random_obstacles

    rng = random.Random(seed)
    sim = sim if sim is not None else Simulation()
    results = []
    for _ in range(episodes):
        sim.clear_obstacles()
        sim.reset()
        start = sim.car.center
        place_random_obstacles(sim, rng, pedestrians, muds)
        positions = []
        for _ in range(frames):
            sim.step(controller)
            positions.append(sim.car.center)
        results.append({"lap": lap_frame(positions, start), "hits": sim.pedestrian_hits,
                        "offtrack": sim.offtrack_frames})
    return {
        "véletlen: elütött gyalogos / futás": round(sum(r["hits"] for r in results) / episodes, 2),
        "véletlen: futás elütés nélkül": f"{sum(r['hits'] == 0 for r in results)}/{episodes}",
        "véletlen: kör teljesítve": f"{sum(r['lap'] is not None for r in results)}/{episodes}",
        "véletlen: pályán kívül (össz.)": sum(r["offtrack"] for r in results),
    }


def summary(results):
    empty = results["empty"]
    ped = [r for k, r in results.items() if k != "empty" and k[0] == "ped"]
    mud = [r for k, r in results.items() if k != "empty" and k[0] == "mud"]
    obstacle_runs = ped + mud
    return {
        "kör (üres pálya)": empty["lap"],
        "pályán kívül (üres pálya)": empty["offtrack"],
        "gyalogos elütve": f"{sum(r['hits'] > 0 for r in ped)}/{len(ped)}",
        "kör teljesítve akadállyal": f"{sum(r['lap'] is not None for r in obstacle_runs)}/{len(obstacle_runs)}",
        "pályán kívül (akadállyal, össz.)": sum(r["offtrack"] for r in obstacle_runs),
    }


if __name__ == "__main__":
    import builtins
    print_ = builtins.print
    builtins.print = lambda *args, **kwargs: None  # a vezérlők kiírásai nélkül
    for mode in sys.argv[1:] or ["rule", "model"]:
        sim = Simulation()
        controller = controllers.create_controller(mode, sim)
        result = summary(evaluate(controller, sim=sim))
        result.update(random_scenarios(controller, sim=sim))
        print_(mode, result)
