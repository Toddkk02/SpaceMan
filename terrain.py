import pygame as pg
import noise
import random
from settings import *
def generate_chunk(chunk_x, chunk_y):
    chunk = []
    for y_pos in range(CHUNK_SIZE):
        for x_pos in range(CHUNK_SIZE):
            target_x = chunk_x * CHUNK_SIZE + x_pos
            target_y = chunk_y * CHUNK_SIZE + y_pos
            tile_type = 0  # 0 = aria, 1 = erba, 2 = terra, 3 = roccia
            height = int(noise.pnoise1(target_x * 0.1, repeat=9999999) * 5) + 10
            if target_y > height:
                tile_type = 2  # Terra
            elif target_y == height:
                tile_type = 1  # Erba
            elif target_y == height - 1:
                if random.randint(1, 16) == 1:
                    tile_type = 3  # Roccia
                    # Aggiungi l'informazione dell'albero
                    chunk.append([target_x, target_y, 4])  # 4 = albero
                    continue
            if tile_type != 0:
                chunk.append([target_x, target_y, tile_type])
    return chunk

def spawn_tree(x, y, block_size):
    # Restituisce la posizione dell'albero
    return (x * block_size, (y - 14) * block_size)

def is_player_moving(current_x, current_y, previous_x, previous_y):
    return current_x != previous_x or current_y != previous_y


def break_tree(mouse_pos, chunks, camera_offset, all_drops):
    for chunk_key in chunks:
        chunk = chunks[chunk_key]
        for tile in chunk:
            tile_x, tile_y, tile_type = tile
            if tile_type == 4:
                tree_pos = spawn_tree(tile_x, tile_y, block_size)
                tree_rect = pg.Rect(tree_pos[0] - camera_offset[0], tree_pos[1] - camera_offset[1], 200, 400)
                
                if tree_rect.collidepoint(mouse_pos):
                    chunk.remove(tile)
                    num_wood_drops = random.randint(3, 7)
                    for _ in range(num_wood_drops):
                        wood_drop_x = tree_pos[0] + random.randint(5, 10)
                        wood_drop_y = tree_pos[1] - 100
                        all_drops.append([float(wood_drop_x), float(wood_drop_y), 0.0, "wood"])
                    return
