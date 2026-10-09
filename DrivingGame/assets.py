""" Képek, maszkok és közös konstansok betöltése. Megjelenítés (ablak) nélkül is használható. """
import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ablak szélesség és magasság
WIDTH, HEIGHT = 1200, 900
PANEL_WIDTH = 250  # a jobb oldali vezérlőpanel szélessége

# maximum képkocka/másodperc
FPS = 60


def scaling(img, scale):
    new_size = round(img.get_width() * scale), round(img.get_height() * scale)
    return pygame.transform.scale(img, new_size)


def _load(path, scale):
    return scaling(pygame.image.load(os.path.join(BASE_DIR, path)), scale)


# fű és pálya képek betöltése, méretezése
GRASS = _load("field/grass.jpg", 3.5)
FIELD_ONLY = _load("field/field_only.png", 0.55)
TRACKSIDE = _load("field/trackside.png", 0.55)
FINISH = _load("field/finish_line.png", 0.15)
FINISH_POSITION = (69, 152)
PEDESTRIAN = _load("obstacles/pedestrian3.png", 0.05)
MUD = _load("obstacles/mud1.png", 0.06)

# autó kép betöltése, méretezése
CAR = _load("field/car.png", 0.4)
CAR_WIDTH, CAR_HEIGHT = CAR.get_width(), CAR.get_height()

# maszkok létrehozása
GRASS_MASK = pygame.mask.from_surface(GRASS)  # maszk létrehozása a fű képből
FIELD_ONLY_MASK = pygame.mask.from_surface(FIELD_ONLY)  # maszk létrehozása a pálya képből
TRACKSIDE_MASK = pygame.mask.from_surface(TRACKSIDE)  # maszk létrehozása a pálya széle képből
CAR_MASK = pygame.mask.from_surface(CAR)  # maszk létrehozása az autó képből
