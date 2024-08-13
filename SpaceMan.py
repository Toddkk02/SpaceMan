import random
import time
import pygame as pg
import pygame_gui as pgui
import noise
import json
from settings import *
from images import *
from UI import *
from movement import *
from drop import *
from save_and_load import *
from music import *

def use_trigger(mouse_pos, chunks, camera_offset, all_drops):
    global mouse_press_start_time
    click = pg.mouse.get_pressed()
    current_time = time.time()

    if click[0]:
        if mouse_press_start_time is None:
            mouse_press_start_time = current_time
        elif current_time - mouse_press_start_time >= mouse_held_duration:
            break_tree(mouse_pos, chunks, camera_offset, all_drops)
            mouse_press_start_time = None
    else:
        mouse_press_start_time = None
        
def gameplay():
    global character_x, character_y, character_height, opacity, active_hash_snails, screen, health, drops, items_in_slot
    
    # Carica i dati di gioco salvati
    health, character_x, character_y, items_in_slot, chunks, active_hash_snails = load_game()

    # Inizializzazioni
    clock = pg.time.Clock()
    all_drops = []  # Combined list

    # Carica immagini
    

    day_music_file = 'music/day_music.mp3'
    night_music_file = 'music/night_music.mp3'

    day_night_cycle = 15000  # 15 seconds for a full cycle
    opacity = 0
    increasing = True
    last_time = pg.time.get_ticks()
    music_playing_day = True

    # Start playing day music
    play_music(day_music_file)

    is_paused = False
    last_save_time = pg.time.get_ticks()  # Tempo dell'ultimo salvataggio

    while True:
        if not is_paused:
            time_delta = clock.tick(60) / 1000.0

            # Salva il gioco solo se è trascorso un intervallo di tempo
            current_time = pg.time.get_ticks()
            if current_time - last_save_time >= 1000:  # 1 secondo
                save_game(health, character_x, character_y, items_in_slot, chunks, active_hash_snails)
                last_save_time = current_time

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_p:  # Pause with the 'P' key
                    is_paused = not is_paused
                if event.key == pg.K_e:
                    crafting_menu()

        if not is_paused:
            # Update and render the game here
            screen.blit(background_img, (0, 0))

            # Calculate camera offset
            camera_offset = [character_x - screen.get_width() // 2, character_y - screen.get_height() // 2]

            # Determine current chunk
            chunk_x = character_x // (CHUNK_SIZE * block_size)
            chunk_y = character_y // (CHUNK_SIZE * block_size)

            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    target_chunk_x = chunk_x + dx
                    target_chunk_y = chunk_y + dy
                    chunk_key = (target_chunk_x, target_chunk_y)
                    if chunk_key not in chunks:
                        chunks[chunk_key] = generate_chunk(target_chunk_x, target_chunk_y)

                    chunk = chunks[chunk_key]
                    for tile in chunk:
                        tile_x, tile_y, tile_type = tile
                        tile_rect = pg.Rect(tile_x * block_size - camera_offset[0], tile_y * block_size - camera_offset[1], block_size, block_size)

                        if tile_type == 1:
                            pg.draw.rect(screen, (34, 139, 34), tile_rect)  # Grass
                        elif tile_type == 2:
                            pg.draw.rect(screen, (139, 69, 19), tile_rect)  # Dirt
                        elif tile_type == 3:
                            pg.draw.rect(screen, (169, 169, 169), tile_rect)  # Stone
                        elif tile_type == 4:
                            tree_pos = spawn_tree(tile_x, tile_y, block_size)
                            screen.blit(tree_img, (tree_pos[0] - camera_offset[0], tree_pos[1] - camera_offset[1]))

            # Update UI
            mouse_pos = pg.mouse.get_pos()
            health = UI(health, mouse_pos, time_delta)
            use_trigger(mouse_pos, chunks, camera_offset, all_drops)

            # Handle movements and objects
            movement(chunks)
            all_drops = update_and_draw_drops(all_drops, chunks, character_y + character_height, block_size, screen, wood_drop_img, hot_shell_drop_img, camera_offset)
            collect_items(all_drops)
    

            # Day-Night Cycle
            if current_time - last_time > day_night_cycle:
                last_time = current_time
                if increasing:
                    opacity += 25
                    if opacity >= 200:
                        opacity = 200
                        increasing = False
                else:
                    opacity -= 25
                    if opacity <= 0:
                        opacity = 0
                        increasing = True

            # Change music based on opacity
            if 76 <= opacity <= 178:
                if music_playing_day:
                    stop_music()
                    play_music(night_music_file)
                    music_playing_day = False
            elif opacity < 76:
                if not music_playing_day:
                    stop_music()
                    play_music(day_music_file)
                    music_playing_day = True

            # Apply opacity effect (example with a surface)
            opacity_surface = pg.Surface((1280, 720), pg.SRCALPHA)
            opacity_surface.fill((0, 0, 0, opacity))
            screen.blit(opacity_surface, (0, 0))

            # Mouse cursor handling
            is_over_tree = False
            for chunk_key in chunks:
                chunk = chunks[chunk_key]
                for tile in chunk:
                    tile_x, tile_y, tile_type = tile
                    if tile_type == 4:
                        tree_pos = spawn_tree(tile_x, tile_y, block_size)
                        tree_rect = pg.Rect(tree_pos[0] - camera_offset[0], tree_pos[1] - camera_offset[1], 200, 400)
                        if tree_rect.collidepoint(mouse_pos):
                            is_over_tree = True
                            break
                if is_over_tree:
                    break

            if is_over_tree:
                screen.blit(trigger_cursor_img, mouse_pos)
            else:
                screen.blit(default_cursor_img, mouse_pos)

            # Draw character
            screen.blit(character_img, (character_x - camera_offset[0], character_y - camera_offset[1]))

            pg.display.update()





    
def menu():
    pg.init()
    screen = pg.display.set_mode((1280, 720))
    background = pg.image.load("images/menu.jpeg")
    background = pg.transform.scale(background, (1280, 720))
    
    manager = pgui.UIManager((1280, 720))

    button_width = 200
    button_height = 50

    play_button = pgui.elements.UIButton(
        relative_rect=pg.Rect(((1280 - button_width) // 2, 300), (button_width, button_height)),
        text='Play',
        manager=manager
    )

    quit_button = pgui.elements.UIButton(
        relative_rect=pg.Rect(((1280 - button_width) // 2, 400), (button_width, button_height)),
        text='Quit',
        manager=manager
    )

    clock = pg.time.Clock()

    while True:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()

            manager.process_events(event)

            if event.type == pgui.UI_BUTTON_PRESSED:
                if event.ui_element == play_button:
                    gameplay()
                elif event.ui_element == quit_button:
                    pg.quit()
                    quit()

        manager.update(time_delta)
        
        screen.blit(background, (0, 0))
        manager.draw_ui(screen)
        pg.display.update()

# Avvia il menu
menu()