"""
Vezérlők: függvények, amelyek a szenzoradatok alapján mozgatják az autót.
Mindegyik controller(car, sensor_data) alakú, így a Simulation.step() bármelyiket futtathatja.
"""
import pygame

import automated_car
import model_control

CONTROL_MODES = ("model", "model_v2", "expert", "rule", "manual", "qlearning")


def keyboard_control(car, keys):
    """ Autó mozgatása W, A, S, D vagy a nyíl billentyűkkel. Igaz, ha volt gáz vagy fék. """
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        car.rotate(left=True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        car.rotate(right=True)
    moved = False
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        moved = True
        car.move_forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        car.move_backward()
    return moved


def manual_controller(car, sensor_data):
    if not keyboard_control(car, pygame.key.get_pressed()):
        car.slowing()  # gurulás/lassulás, ha nincs gáz


def rule_controller(car, sensor_data):
    """ Szabályalapú vezérlés (automated_car.py); utána az autó gurul, ahogy gáz nélkül tenné. """
    automated_car.apply_control(car, sensor_data)
    car.slowing()


class ModelController:
    """ A neurális háló vezérli az autót; a háló maga állítja a sebességet is. """

    def __init__(self, model):
        self.model = model

    def __call__(self, car, sensor_data):
        model_control.apply_advanced_model_control(car, self.model, sensor_data)


def create_controller(mode, sim):
    """ Vezérlő a megadott módhoz; a távolságot mérő vezérlők a szimuláció akadályait is látják. """
    if mode == "manual":
        return manual_controller
    if mode == "rule":
        return rule_controller
    if mode == "expert":
        import expert
        return expert.ExpertController(sim.obstacles)
    if mode == "model":
        import distance_model  # a TensorFlow betöltése lassú, csak akkor kell, ha a háló vezet
        return distance_model.DistanceModelController(distance_model.load_trained_model(), sim.obstacles)
    if mode == "model_v2":
        import model
        return ModelController(model.load_trained_model())
    if mode == "qlearning":
        import qlearning
        return qlearning.QLearningController.load()
    raise ValueError(f"Ismeretlen vezérlési mód: {mode} ({' | '.join(CONTROL_MODES)})")
