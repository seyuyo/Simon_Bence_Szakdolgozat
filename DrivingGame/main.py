"""
Önvezető autó: a szimuláció megjelenítése és kezelése.

Indítás:  python main.py [model | rule | manual | qlearning]
"""
import sys

import pygame
import pygame_widgets
from pygame_widgets.slider import Slider

from assets import (WIDTH, HEIGHT, PANEL_WIDTH, FPS, GRASS, FIELD_ONLY, TRACKSIDE, FINISH, FINISH_POSITION,
                    PEDESTRIAN, MUD)
from controllers import CONTROL_MODES, create_controller
from sensors import (SENSOR_COLORS, SENSOR_RANGE, DISTANCE_ANGLES, sensor_direction, sensor_segments, surface_at,
                     read_distances)
from simulation import Simulation

PANEL_X = WIDTH - PANEL_WIDTH

# Gyalogos és sár kép pozíciója a vezérlőpanelen (panelen belüli koordináták)
PEDESTRIAN_PANEL_POS = (40, 420)
MUD_PANEL_POS = (155, 420)

# Törlés gomb pozíció és méret a vezérlőpanelen
CLEAR_BUTTON = pygame.Rect(10, 500, 230, 50)


def draw_sensors(win, car, obstacles):
    """ Az érzékelők rajzolása, a végpontjukon talált felület színével. """
    for start, end in sensor_segments(car):
        color = SENSOR_COLORS[surface_at(end, obstacles)]
        pygame.draw.line(win, color, start, end, 2)
        pygame.draw.circle(win, color, (int(end[0]), int(end[1])), 5)


def draw_distance_sensors(win, car, obstacles):
    """ Távolságmérő sugarak: a sugár a mért távolságig tart, a vége a talált felület színe. """
    distances, surfaces = read_distances(car, obstacles)
    start = car.nose()
    for angle, distance, surface in zip(DISTANCE_ANGLES, distances, surfaces):
        dx, dy = sensor_direction(car, angle)
        length = abs(distance) * SENSOR_RANGE
        end = (start[0] + dx * length, start[1] + dy * length)
        pygame.draw.line(win, (220, 220, 220), start, end, 1)
        if surface != 'G':
            pygame.draw.circle(win, SENSOR_COLORS[surface], (int(end[0]), int(end[1])), 4)


def draw_world(win, sim, distance_sensors=False):
    win.blit(GRASS, (0, 0))
    win.blit(FIELD_ONLY, (0, 0))
    win.blit(TRACKSIDE, (0, 0))
    win.blit(FINISH, FINISH_POSITION)
    for obstacle in sim.obstacles:
        obstacle.draw(win)
    sim.car.draw(win)
    if distance_sensors:
        draw_distance_sensors(win, sim.car, sim.obstacles)
    else:
        draw_sensors(win, sim.car, sim.obstacles)


def draw_panel(panel, font, sim, mode):
    car = sim.car
    panel.fill((255, 255, 255))
    lines = [
        (f"Sebesség:{round(car.get_velocity(), 2)} p/s", (25, 5)),
        (f"Forgási sebesség:{round(car.get_rotation_velocity(), 2)}", (20, 50)),
        (f"Maximális sebesség:{round(car.get_max_velocity(), 2)}", (20, 130)),
        (f"Gyorsulás:{round(car.get_acceleration(), 2)}", (52, 210)),
        (f"Fék:{round(car.get_acceleration(), 2)}", (85, 270)),
        ("Akadályok kiválasztása:", (20, 330)),
        ("Gyalogos", (20, 370)),
        ("Sár", (160, 370)),
        (f"Vezérlés: {mode}", (20, 600)),
        (f"Elütött gyalogos: {sim.pedestrian_hits}", (20, 640)),
    ]
    for text, pos in lines:
        panel.blit(font.render(text, True, (0, 0, 0)), pos)

    # gyalogos és sár hozzáadása
    panel.blit(PEDESTRIAN, PEDESTRIAN_PANEL_POS)
    panel.blit(MUD, MUD_PANEL_POS)

    # Törlés gomb rajzolása
    pygame.draw.rect(panel, (0, 0, 0), CLEAR_BUTTON)
    panel.blit(font.render("Összes akadály törlése", True, (255, 255, 255)),
               (CLEAR_BUTTON.x + 10, CLEAR_BUTTON.y + 15))


def panel_rect(image, pos):
    return image.get_rect(topleft=(PANEL_X + pos[0], pos[1]))


def handle_mouse(event, sim):
    for obstacle in sim.obstacles:
        obstacle.handle_event(event)

    # Az új akadály hozzáadása csak `MOUSEBUTTONDOWN` eseménynél történik
    if event.type != pygame.MOUSEBUTTONDOWN:
        return
    if CLEAR_BUTTON.move(PANEL_X, 0).collidepoint(event.pos):
        sim.clear_obstacles()
    elif panel_rect(PEDESTRIAN, PEDESTRIAN_PANEL_POS).collidepoint(event.pos):
        sim.add_pedestrian()
    elif panel_rect(MUD, MUD_PANEL_POS).collidepoint(event.pos):
        sim.add_mud()


def main(mode):
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Önvezető autó")
    font = pygame.font.SysFont("comicsans", 20)  # betűtípus egyszer betöltve, nem minden képkockában
    clock = pygame.time.Clock()  # egyetlen óra, különben a tick() nem korlátozza az FPS-t

    sim = Simulation()
    controller = create_controller(mode, sim)
    panel = pygame.Surface((PANEL_WIDTH, HEIGHT))

    # csúszkák létrehozása: a pályán érvényes beállítások
    settings = sim.track_settings
    sliders = {
        "rotation_vel": Slider(win, WIDTH - 210, 90, 160, 15, min=0, max=10, step=0.1,
                               initial=settings["rotation_vel"]),
        "max_vel": Slider(win, WIDTH - 210, 170, 160, 15, min=0, max=10, step=0.1,
                          initial=settings["max_vel"]),
        "acceleration": Slider(win, WIDTH - 210, 250, 160, 15, min=0, max=1, step=0.1,
                               initial=settings["acceleration"]),
    }

    """ A program fő ciklusa, amely a játékot vezérli. """
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                handle_mouse(event, sim)

        for name, slider in sliders.items():
            settings[name] = slider.getValue()

        sim.step(controller)

        draw_world(win, sim, distance_sensors=mode in ("model", "expert"))
        draw_panel(panel, font, sim, mode)
        win.blit(panel, (PANEL_X, 0))

        pygame_widgets.update(events)
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    selected_mode = sys.argv[1] if len(sys.argv) > 1 else "model"
    if selected_mode not in CONTROL_MODES:
        sys.exit(f"Ismeretlen vezérlési mód: {selected_mode} ({' | '.join(CONTROL_MODES)})")
    main(selected_mode)
