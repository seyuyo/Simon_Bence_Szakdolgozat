import pygame

class Obstacle:
    def __init__(self, image, position):
        self.image = image
        self.rect = self.image.get_rect(topleft=position)
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win):
        win.blit(self.image, self.rect.topleft)

    def collides_with_point(self, point):
        """ Ellenőrzi, hogy az adott pont (x, y) benne van-e a maszkban. """

        x, y = point
        offset_x = x - self.rect.left
        offset_y = y - self.rect.top
        return self.mask.get_at((offset_x, offset_y)) == 1  # 1 = nem átlátszó pixel

    def handle_event(self, event):
        """Egér esemény kezelése az akadály húzása érdekében."""

        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            mouse_x, mouse_y = event.pos
            self.offset_x = self.rect.x - mouse_x
            self.offset_y = self.rect.y - mouse_y
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x, mouse_y = event.pos
            self.rect.x = mouse_x + self.offset_x
            self.rect.y = mouse_y + self.offset_y
