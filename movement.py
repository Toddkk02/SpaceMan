import pygame as pg
from settings import *
from images import *
from terrain import *
def movement(world):
    global character_x, character_y, is_jumping, jump_speed, gravity, character_img, direction
    keys = pg.key.get_pressed()

    # Movimento orizzontale
    if keys[pg.K_d]:
        character_x += 5
        if direction != 'right':  # Cambia direzione solo se non è già destra
            character_img = pg.transform.flip(character_img, True, False)  # Flippa l'immagine
            direction = 'right'
    elif keys[pg.K_a]:
        character_x -= 5
        if direction != 'left':  # Cambia direzione solo se non è già sinistra
            character_img = pg.transform.flip(character_img, True, False)  # Flippa l'immagine
            direction = 'left'

    # Salto
    if keys[pg.K_SPACE] and not is_jumping:
        is_jumping = True

    if is_jumping:
        character_y -= jump_speed
        jump_speed -= gravity
        if jump_speed < -10:  # Limita la velocità di salto per evitare accelerazioni eccessive
            is_jumping = False
            jump_speed = 10

    # Applicazione della gravità
    if not is_jumping:
        fall_speed = 5
        character_y += fall_speed

    # Verifica collisioni dopo l'aggiornamento della posizione
    collision(world)
    
    
def collision(world):
    global character_y, is_jumping, jump_speed, tile_type

    player_rect = pg.Rect(character_x, character_y, character_width, character_height)
    on_ground = False

    for chunk_key in world:
        chunk = world[chunk_key]
        for tile in chunk:
            tile_x, tile_y, tile_type = tile
            if tile_type != 0:  # Solo per blocchi solidi
                tile_rect = pg.Rect(tile_x * block_size, tile_y * block_size, block_size, block_size)

                if player_rect.colliderect(tile_rect):
                    # Se il personaggio è sopra il blocco
                    if player_rect.bottom > tile_rect.top and player_rect.top < tile_rect.bottom:
                        if character_y + character_height > tile_y * block_size:
                            character_y = tile_y * block_size - character_height
                            is_jumping = False
                            jump_speed = 10
                            on_ground = True
                    # Se il personaggio è ai lati del blocco
                    elif player_rect.right > tile_rect.left and player_rect.left < tile_rect.right:
                        if character_x + character_width > tile_x * block_size and character_x < (tile_x + 1) * block_size:
                            if character_y < tile_y * block_size:
                                character_y = tile_y * block_size - character_height
                                is_jumping = False
                                jump_speed = 10
                                on_ground = True
                    elif tile_type == 4:  # Se il personaggio è sopra l'albero
                         continue
                    

    # Applica la gravità solo se il personaggio non è a terra
    if not on_ground:
        character_y += gravity
