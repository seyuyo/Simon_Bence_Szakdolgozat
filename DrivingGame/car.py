import math

import pygame

from assets import CAR, CAR_WIDTH, CAR_HEIGHT


class Car:
    START_POSITION = (78, 190)

    """
    Car osztály konstruktor.

    Paraméterek:
    - max_vel (float): Az autó maximális sebessége.
    - rotation_vel (float): Az autó forgási sebessége.
    """

    def __init__(self, max_vel, rotation_vel, acceleration=0.1):
        self.car = CAR
        self.max_vel = max_vel
        self.vel = 1  # Jelenlegi sebesség inicializálása
        self.rotation_vel = rotation_vel  # Forgási sebesség inicializálása
        self.angle = 0
        self.x, self.y = self.START_POSITION  # Kezdő pozíció inicializálása
        self.acceleration = acceleration  # Gyorsulás inicializálása
        self.rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        self.update_center()

    def get_max_velocity(self):
        return self.max_vel

    def get_velocity(self):
        return self.vel

    def get_angle(self):
        return self.angle

    def get_rotation_velocity(self):
        return self.rotation_vel

    def get_position(self):
        return self.x, self.y

    def get_acceleration(self):
        return self.acceleration

    def set_max_velocity(self, max_vel):
        self.max_vel = max_vel

    def set_velocity(self, vel):
        if vel < 1:
            self.vel = 1
        else:
            self.vel = vel

    def set_rotation_velocity(self, rotation_vel):
        self.rotation_vel = rotation_vel

    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    def heading(self):
        """ Egységvektor a haladási irányba (0 fok = felfelé, a szög balra forgatva nő). """
        radians = math.radians(self.angle)
        return -math.sin(radians), -math.cos(radians)

    def nose(self):
        """ Az autó orrának pozíciója, innen indulnak a szenzorok. """
        hx, hy = self.heading()
        return self.center[0] + hx * CAR_HEIGHT / 2, self.center[1] + hy * CAR_HEIGHT / 2

    """
    Az autó forgatását végző metódus.

    Paraméterek:
    - left (bool): Balra forgatás engedélyezése.
    - right (bool): Jobbra forgatás engedélyezése.
    """
    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_vel  # Forgatás balra
        elif right:
            self.angle -= self.rotation_vel  # Forgatás jobbra
        self.angle %= 360

    """ Az autó előre mozgását végző metódus. """
    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)  # Sebesség növelése
        self.move()  # Mozgás elvégzése

    """ Az autó hátrafelé mozgását végző metódus. """
    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

    """ Az autó általános mozgását végző metódus. """
    def move(self):
        hx, hy = self.heading()
        self.x += hx * self.vel  # X pozíció frissítése
        self.y += hy * self.vel  # Y pozíció frissítése
        self.update_center()

    """ Az autó lassítását végző metódus amennyiben felengedjük a gázt vagy hátrafelé megyünk."""
    def slowing(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)  # Sebesség csökkentése
        self.move()  # Mozgás elvégzése

    def update_center(self):
        """ Középpont és befoglaló téglalap frissítése az aktuális pozíció alapján. """
        self.center = (self.x + CAR_WIDTH / 2, self.y + CAR_HEIGHT / 2)
        self.rect.topleft = (self.x, self.y)

    def rotated(self):
        """ Az elforgatott autókép és a helye (a kép középpontja körül forgatva). """
        rotated_img = pygame.transform.rotate(self.car, self.angle)
        return rotated_img, rotated_img.get_rect(center=self.center)

    def rotated_mask(self):
        rotated_img, rect = self.rotated()
        return pygame.mask.from_surface(rotated_img), rect

    """ Ütközik-e az (elforgatott) autó a megadott, (x, y) helyre tett maszkkal. """
    def collide(self, mask, x=0, y=0):
        car_mask, rect = self.rotated_mask()
        return mask.overlap(car_mask, (rect.x - x, rect.y - y))

    def draw(self, win):
        rotated_img, rect = self.rotated()
        win.blit(rotated_img, rect.topleft)
