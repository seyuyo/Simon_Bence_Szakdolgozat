import pygame
import pygame_widgets
import math
import sys
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox


pygame.init()

def scaling(img, scale):
    new_size = round(img.get_width() * scale), round(img.get_height() * scale)
    return pygame.transform.scale(img, new_size)


def rotate_to_center(win, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)
    win.blit(rotated_image, new_rect.topleft)


# ablak szélesség és magasság
WIDTH, HEIGHT = 1200, 900

# fű és pálya képek betöltése, méretezése
GRASS = scaling(pygame.image.load("grass.jpg"), 3.5)
FIELD = scaling(pygame.image.load("field.png"), 0.55)
FINISH = scaling(pygame.image.load("finish_line.png"), 0.15)

# autó kép betöltése, méretezése
CAR = scaling(pygame.image.load("car.png"), 0.4)
CAR_WIDTH, CAR_HEIGHT = CAR.get_width(), CAR.get_height()

GRASS_MASK = pygame.mask.from_surface(GRASS) # maszk létrehozása a fű képből
FIELD_MASK = pygame.mask.from_surface(FIELD) # maszk létrehozása a pálya képből
CAR_MASK = pygame.mask.from_surface(CAR) # maszk létrehozása az autó képből

# ablak beállítása szélesség-magasság szerint
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Önvezető autó")

# maximum képkocka/másodperc
FPS = 60

class Car:
    CAR_ = CAR
    START_POSITION = (78, 190)

    """
    Car osztály konstruktor.

    Paraméterek:
    - max_vel (float): Az autó maximális sebessége.
    - rotation_vel (float): Az autó forgási sebessége.
    """
    def __init__(self, max_vel, rotation_vel):
        self.car = self.CAR_
        self.max_vel = max_vel
        self.vel = 0  # Jelenlegi sebesség inicializálása
        self.rotation_vel = rotation_vel  # Forgási sebesség inicializálása
        self.angle = 0
        self.x, self.y = self.START_POSITION  # Kezdő pozíció inicializálása
        self.acceleration = 0.1  # Gyorsulás inicializálása

    def get_max_velocity(self):
        return self.max_vel

    def get_velocity(self):
        return self.vel

    def get_rotation_velocity(self):
        return self.rotation_vel

    def get_position(self):
        return self.x, self.y

    def get_acceleration(self):
        return self.acceleration

    def set_max_velocity(self, max_vel):
        self.max_vel = max_vel

    def set_velocity(self, vel):
        self.vel = vel

    def set_rotation_velocity(self, rotation_vel):
        self.rotation_vel = rotation_vel

    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

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

    """
    Az autó kirajzolását végző metódus.

    Paraméterek:
    - win (pygame.Surface): A Pygame ablak, amelybe az autót kirajzoljuk.

    """
    def draw(self, win):
        rotate_to_center(win, self.car, (self.x, self.y), self.angle)


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
        radians = math.radians(self.angle)  # Szöget radiánba konvertálja
        vertical = math.cos(radians) * self.vel  # Vertikális mozgás számolása
        horizontal = math.sin(radians) * self.vel  # Horizontális mozgás számolása

        self.y -= vertical  # Y pozíció frissítése
        self.x -= horizontal  # X pozíció frissítése


    """ Az autó lassítását végző metódus amennyiben felengedjük a gázt vagy hátrafelé megyünk."""
    def slowing(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)  # Sebesség csökkentése
        self.move()  # Mozgás elvégzése

    """ Az autó fűre/terepre lépését beállító metódus. """
    def collide_grass(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.car)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(car_mask, offset)

#
def draw(win, images, player_car):
    for car, pos in images:
        win.blit(car, pos)
    player_car.draw(win)

# Képek létrehozása és pozíciók beállítása
images = [(GRASS, (0, 0)), (FIELD, (0, 0)), (FINISH, (69, 152))]

# Autó létrehozása
player_car = Car(4, 4)


# Felület az adatok megjelenítéséhez és vezérléshez
control_surface = pygame.Surface((300, HEIGHT))
control_surface.fill((255, 255, 255))

control_panel = pygame.Surface((300, HEIGHT))
control_panel.fill((200, 200, 200))

# csűszkák létrehozása
max_velocity_slider = Slider(WIN, WIDTH - 210, 170, 160, 15, min=0, max=10, step=0.1,
                             initial=player_car.get_max_velocity())
# output = TextBox(WIN, WIDTH - 200, 200, 50, 50, fontSize=20)

rotation_velocity_slider = Slider(WIN, WIDTH - 210, 90, 160, 15, min=0, max=10, step=0.1,
                                      initial=player_car.get_rotation_velocity())
# output2 = TextBox(WIN, WIDTH - 400, 300, 50, 50, fontSize=20)

acceleration_slider = Slider(WIN, WIDTH - 210, 250, 160, 15, min=0, max=1, step=0.1,
                                        initial=player_car.get_acceleration())


""" A program fő ciklusa, amely a játékot vezérli. """
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    draw(WIN, images, player_car)
    WIN.blit(control_panel, (WIDTH - 250, 0))

    keys = pygame.key.get_pressed()
    moved = False

    # Autó mozgatása W, A, S, D vagy a nyíl billentyűkkel
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_car.rotate(left=True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_car.rotate(right=True)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        player_car.move_backward()

    if not moved:
        player_car.slowing()

    # Ha a játékos terepen marad akkor csúszkával állítható a maximális sebesség és a forgási sebesség
    if player_car.collide_grass(FIELD_MASK):
        print("Field")

        max_velocity_slider.listen(events)
        max_velocity_slider.draw()

        player_car.set_max_velocity(max_velocity_slider.getValue())
        # output.setText(round(max_velocity_slider.getValue(), 2))


        rotation_velocity_slider.listen(events)
        rotation_velocity_slider.draw()

        player_car.set_rotation_velocity(rotation_velocity_slider.getValue())
        # output2.setText(round(rotation_velocity_slider.getValue(), 2))

        acceleration_slider.listen(events)
        acceleration_slider.draw()

        player_car.set_acceleration(acceleration_slider.getValue())

    else: # Ha a játékos fűre lép akkor a maximális sebesség és a forgási sebesség lelassul egy fix értékre
        print("Grass")
        player_car.set_max_velocity(2)
        player_car.set_rotation_velocity(2)
        player_car.set_acceleration(0.05)


    # Adatokat megjelenítő felület
    control_panel.blit(control_surface, (0, 0))
    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Sebesség:{round(player_car.get_velocity(), 2)} p/s",
                                                    True, (0, 0, 0)),(25, 5))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Forgási sebesség:{round(player_car.get_rotation_velocity(), 2)}",
                                                    True, (0, 0, 0)), (20, 50))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Maximális sebesség:{round(player_car.get_max_velocity(), 2)}",
                                                    True, (0, 0, 0)), (20, 130))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Gyorsulás:{round(player_car.get_acceleration(), 2)}",
                                                    True, (0, 0, 0)), (52, 210))

    control_panel.blit(
        pygame.font.SysFont("comicsans", 20).render(f"Fék:{round(player_car.get_acceleration(), 2)}",
                                                    True, (0, 0, 0)), (85, 270))
    pygame_widgets.update(events)
    pygame.display.update()
    pygame.time.Clock().tick(FPS)
