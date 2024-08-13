import pygame as pg
pg.init()




pg.display.set_caption("SpaceMan")
screen = pg.display.set_mode((1280, 720))

CHUNK_SIZE = 24
LEFT = -1
RIGHT = 1
# Impostazioni di base
last_movement_time = 0
time_to_auto_health = 0
direction = 'right' 
health = 100
jump_speed = 10
gravity = 0.5
is_jumping = False
character_y = 100
character_x = 100
character_height = 150
character_width = 100
world_width = 2000
world_height = 100
block_size = 25
mouse_press_start_time = None
mouse_held_duration = 3  # Durata in secondi
slot_size = 50
selected_slot = 0  # Inizializza con un valore valido
slot_positions = []
items_in_slot = [None] * 10
active_hash_snails = []
drops = ["wood", "dirt", "stone", "hot shell"]
fixed_y_positions = [450]
last_collision_time = 0
collision_cooldown = 1000  # Millisecondi di cooldown

time_to_auto_health = 0
last_movement_time = pg.time.get_ticks()
item_images = [pg.Surface((50, 50)) for _ in range(5)]  # Esempio di 5 immagini di oggetti
for item in item_images:
    torch = pg.image.load("images/torch.png")
    torch = pg.transform.scale(torch, (50, 50))
