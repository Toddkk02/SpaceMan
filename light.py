import pygame as pg
from settings import *
from images import *
from terrain import *
from UI import *
from movement import *
from drop import *
def circle_surf_light(radius, color):
    surface = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
    pg.draw.circle(surface, color, (radius, radius), radius)
    surface.set_colorkey((0, 0, 0))  # Trasparente la superficie
    return surface

def draw_light(screen, light_pos, light_radius, light_color):
    light_surf = circle_surf_light(light_radius, light_color)
    light_rect = light_surf.get_rect(center=light_pos)
    screen.blit(light_surf, light_rect.topleft)


    
def day_and_night(opacity):
    
    filter_background.set_alpha(opacity)  # Imposta l'opacità del filtro
    screen.blit(filter_background, (0, 0))  # Applica il filtro notte allo schermo

