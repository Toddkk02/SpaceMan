import pygame as pg
from settings import *
from images import *
from terrain import *
from movement import *
def update_and_draw_drops(drops, world, ground_level, block_size, screen, wood_drop_img, hot_shell_drop_img, camera_offset):
    drops = drop_gravity(drops, world, ground_level, block_size)

    for drop in drops:
        drop_x, drop_y, _, drop_type = drop
        if drop_type == "wood":
            screen.blit(wood_drop_img, (drop_x - camera_offset[0], drop_y - camera_offset[1]))
        elif drop_type == "hot shell":
            screen.blit(hot_shell_drop_img, (drop_x - camera_offset[0], drop_y - camera_offset[1]))

    return drops
def drop_gravity(drops, world, ground_level, block_size):
    drop_width = 75
    drop_height = 75

    for drop in drops:
        try:
            # Ensure all elements are of the correct type
            drop[0] = float(drop[0])  # x position
            drop[1] = float(drop[1])  # y position
            drop[2] = float(drop[2])  # fall speed

            drop[2] += gravity  # Incrementa la velocità di caduta dovuta alla gravità
            new_y_position = drop[1] + drop[2]

            # Crea un rettangolo per il drop
            drop_rect = pg.Rect(drop[0], new_y_position, drop_width, drop_height)

            # Verifica le collisioni con il mondo
            on_ground = False
            for chunk_key in world:
                chunk = world[chunk_key]
                for tile in chunk:
                    tile_x, tile_y, tile_type = tile
                    if tile_type != 0:  # Controlla solo i blocchi solidi
                        tile_rect = pg.Rect(tile_x * block_size, tile_y * block_size, block_size, block_size)

                        if drop_rect.colliderect(tile_rect):
                            new_y_position = tile_y * block_size - drop_height
                            drop[2] = 0  # Ferma la caduta
                            on_ground = True
                            break
                if on_ground:
                    break

            # Se il drop tocca il terreno o un oggetto solido, fermalo
            if new_y_position >= ground_level - drop_height:
                new_y_position = ground_level - drop_height
                drop[2] = 0  # Ferma la caduta

            drop[1] = new_y_position  # Aggiorna la posizione Y del drop

        except (ValueError, IndexError) as e:
            print(f"Error processing drop: {drop}. Error: {e}")
            drops.remove(drop)  # Remove invalid drops

    return drops


def update_drops(wood_drops, world, ground_level):
    # Aggiorna la posizione dei drop chiamando drop_gravity
    wood_drops = drop_gravity(wood_drops, world, ground_level)
    # Potresti aggiungere qui la logica per disegnare i drop sullo schermo o per altre azioni
    return wood_drops