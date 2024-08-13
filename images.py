import pygame as pg
from settings import *
tree_img = pg.image.load("images/tree.png")
tree_img = pg.transform.scale(tree_img, (200, 400))

wood_drop_img = pg.image.load("images/wood_drop.png")
wood_drop_img = pg.transform.scale(wood_drop_img, (75, 75))

hot_shell_drop_img = pg.image.load("images/hot_shell.png")
hot_shell_drop_img = pg.transform.scale(hot_shell_drop_img, (75, 75))

background_img = pg.image.load("images/background.jpg")
background_img = pg.transform.scale(background_img, (1280, 720))
filter_background = pg.image.load("images/night.jpg")
filter_background = pg.transform.scale(filter_background, (1280, 720))
hearth_img = pg.image.load("images/hearth.png")
broken_hearth_img = pg.image.load("images/broken_hearth.png")
character_img = pg.image.load("images/character.png")
character_img = pg.transform.scale(character_img, (character_width, character_height))

# Carica le immagini del cursore
default_cursor_img = pg.image.load("images/cursor.png")
default_cursor_img = pg.transform.scale(default_cursor_img, (30, 30))  # Ridimensiona se necessario

trigger_cursor_img = pg.image.load("images/cursor_trigger.png")
trigger_cursor_img = pg.transform.scale(trigger_cursor_img, (30, 30))  # Assicurati che il cursore sia delle stesse dimensioni

wood_drop_img = pg.image.load("images/wood_drop.png")
wood_drop_img = pg.transform.scale(wood_drop_img, (75, 75))

hot_shell_drop_img = pg.image.load("images/hot_shell.png")
hot_shell_drop_img = pg.transform.scale(hot_shell_drop_img, (75, 75))