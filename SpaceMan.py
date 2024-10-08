import math
import random
import sys
import time
import pygame as pg
import pygame_gui as pgui
import noise
import json
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
fixed_y_positions = [150]
last_collision_time = 0
collision_cooldown = 1000  # Millisecondi di cooldown
global chunks
chunks = {}


pg.init()



pg.display.set_caption("SpaceMan")
screen = pg.display.set_mode((1280, 720))

# Carica le immagini
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


def save_game(health, character_x, character_y, items_in_slot, chunks, snails):
    data = {
        'health': health,
        'character_x': character_x,
        'character_y': character_y,
        'items_in_slot': items_in_slot,
        'chunks': {f"{key}": value for key, value in chunks.items()},
        'snails': [(snail.x, snail.y) for snail in snails]
    }
    with open('save_game.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_game():
    try:
        with open('save_game.json', 'r') as f:
            data = json.load(f)
        
        chunks = {eval(key): value for key, value in data.get('chunks', {}).items()}
        items_in_slot = data.get('items_in_slot', [None] * 10)
        snails = [Snail(x, y) for x, y in data.get('snails', [])]
        
        return (
            data.get('health', 100),
            data.get('character_x', 0),
            data.get('character_y', 0),
            items_in_slot,
            chunks,
            snails
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading game: {e}")
        return initialize_game()



def initialize_game():
    global health, character_x, character_y, items_in_slot, chunks
    health = 100
    character_x = 0
    character_y = 100
    items_in_slot = [None] * 10
    chunks = {}
    return (100, 0, 0, [None] * 10, {}, [])
# Generazione del mondo
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

# Inizializzazione delle variabili globali all'inizio del gioco
time_to_auto_health = 0
last_movement_time = pg.time.get_ticks()

def UI(health, mouse_pos, time_delta):
    global time_to_auto_health, last_movement_time
    global character_x, character_y
    print(character_x, character_y)
    hearth_width, hearth_height = 50, 50
    hearth = pg.transform.scale(hearth_img, (hearth_width, hearth_height))
    broken_hearth = pg.transform.scale(broken_hearth_img, (hearth_width, hearth_height))
    
    time_to_auto_health += time_delta * 1000  # Accumula il tempo trascorso in millisecondi

    if time_to_auto_health >= 1000:  # 1000 ms = 1 secondo
        time_to_auto_health -= 1000  # Resetta il timer di un secondo (non a 0 per accumulare eventuali frammenti di tempo)
        health = min(health + 1, 100)  # Aumenta la salute del giocatore (fino a un massimo di 100)
    

    # Disegna i cuori (pieno e rotto) sullo schermo
    max_hearts = 10
    full_hearts = health // 10
    broken_hearts = max_hearts - full_hearts

    for i in range(full_hearts):
        screen.blit(hearth, (i * hearth_width, 0))

    for i in range(broken_hearts):
        screen.blit(broken_hearth, ((full_hearts + i) * hearth_width, 0))

    pg.mouse.set_visible(False)  # Nasconde il cursore del sistema

    # Disegna l'immagine del cursore alla posizione del mouse
    screen.blit(default_cursor_img, mouse_pos)

    tool_bar_logic()
    return health


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
def draw_circle_around_player(screen, character_x, character_y, radius):
    pg.draw.circle(screen, (255, 0, 0), (character_x + character_width // 2, character_y + character_height // 2), radius, 2)



def update_and_draw_drops(drops, world, ground_level, block_size, screen, wood_drop_img, hot_shell_drop_img, camera_offset):
    drops = drop_gravity(drops, world, ground_level, block_size)

    for drop in drops:
        drop_x, drop_y, _, drop_type = drop
        if drop_type == "wood":
            screen.blit(wood_drop_img, (drop_x - camera_offset[0], drop_y - camera_offset[1]))
        elif drop_type == "hot shell":
            screen.blit(hot_shell_drop_img, (drop_x - camera_offset[0], drop_y - camera_offset[1]))

    return drops

item_images = [pg.Surface((50, 50)) for _ in range(5)]  # Esempio di 5 immagini di oggetti
for item in item_images:
    torch = pg.image.load("images/torch.png")
    torch = pg.transform.scale(torch, (50, 50))




def crafting_menu():
    crafting_open = True
    crafting_background = pg.Surface((400, 300))
    crafting_background.fill((200, 200, 200))
    crafting_rect = crafting_background.get_rect(center=(640, 360))

    font = pg.font.Font(None, 36)
    craft_torch_text = font.render("Craft Torch", True, (0, 0, 0))
    craft_torch_rect = craft_torch_text.get_rect(center=(640, 360))

    while crafting_open:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_e:
                    crafting_open = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if craft_torch_rect.collidepoint(event.pos):
                    craft_torch()

        screen.blit(crafting_background, crafting_rect)
        screen.blit(craft_torch_text, craft_torch_rect)
        screen.blit(default_cursor_img, pg.mouse.get_pos())
        pg.display.flip()
def craft_torch():
    global items_in_slot
    # Check if player has necessary items (e.g., 1 wood and 1 hot shell)
    has_wood = any(slot and slot['item'] == 'wood' and slot['quantity'] >= 1 for slot in items_in_slot)
    has_hot_shell = any(slot and slot['item'] == 'hot shell' and slot['quantity'] >= 1 for slot in items_in_slot)

    if has_wood and has_hot_shell:
        # Remove crafting materials
        remove_item('wood', 1)
        remove_item('hot shell', 1)
        # Add torch to inventory
        add_to_slot('torch')
        print("Torch crafted!")
    else:
        print("Not enough materials to craft a torch!")

def remove_item(item_name, quantity):
    global items_in_slot
    for slot in items_in_slot:
        if slot and slot['item'] == item_name:
            if slot['quantity'] > quantity:
                slot['quantity'] -= quantity
                return
            elif slot['quantity'] == quantity:
                slot.clear()
                return
            else:
                quantity -= slot['quantity']
                slot.clear()

def place_torch(mouse_pos, chunks, camera_offset):
    global items_in_slot, selected_slot
    
    if items_in_slot[selected_slot] is None or items_in_slot[selected_slot]['item'] != 'torch':
        return

    chunk_x = int((mouse_pos[0] + camera_offset[0]) // (CHUNK_SIZE * block_size))
    chunk_y = int((mouse_pos[1] + camera_offset[1]) // (CHUNK_SIZE * block_size))
    chunk_key = (chunk_x, chunk_y)
    
    if chunk_key not in chunks:
        chunks[chunk_key] = []

    tile_x = int((mouse_pos[0] + camera_offset[0]) // block_size)
    tile_y = int((mouse_pos[1] + camera_offset[1]) // block_size)
    
    chunks[chunk_key].append([tile_x, tile_y, 5])  # 5 could be the ID for torch
    items_in_slot[selected_slot]['quantity'] -= 1
    
    if items_in_slot[selected_slot]['quantity'] == 0:
        items_in_slot[selected_slot] = None

def draw_torch_light(screen, torch_pos, camera_offset, chunks, day_opacity):
    light_radius = 10  # Raggio della luce in blocchi
    max_brightness = 255
    
    for dy in range(-light_radius, light_radius + 1):
        for dx in range(-light_radius, light_radius + 1):
            block_x = torch_pos[0] // block_size + dx
            block_y = torch_pos[1] // block_size + dy
            
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= light_radius:
                brightness = int(max_brightness * (1 - distance / light_radius))
                brightness = min(brightness, 255 - day_opacity)  # Regola la luminosità in base al ciclo giorno/notte
                
                screen_x = block_x * block_size - camera_offset[0]
                screen_y = block_y * block_size - camera_offset[1]
                
                light_surf = pg.Surface((block_size, block_size), pg.SRCALPHA)
                light_surf.fill((255, 200, 100, brightness))
                screen.blit(light_surf, (screen_x, screen_y), special_flags=pg.BLEND_RGBA_ADD)

                # Illumina i blocchi vicini
                chunk_key = (block_x // CHUNK_SIZE, block_y // CHUNK_SIZE)
                if chunk_key in chunks:
                    for tile in chunks[chunk_key]:
                        if tile[0] == block_x and tile[1] == block_y:
                            tile_rect = pg.Rect(screen_x, screen_y, block_size, block_size)
                            pg.draw.rect(screen, (brightness, brightness, brightness), tile_rect, 1)

def place_wood(mouse_pos, chunks, camera_offset):
    global items_in_slot, selected_slot
    
    if items_in_slot[selected_slot] is None or items_in_slot[selected_slot]['item'] != 'wood':
        return

    chunk_x = int((mouse_pos[0] + camera_offset[0]) // (CHUNK_SIZE * block_size))
    chunk_y = int((mouse_pos[1] + camera_offset[1]) // (CHUNK_SIZE * block_size))
    chunk_key = (chunk_x, chunk_y)
    
    if chunk_key not in chunks:
        chunks[chunk_key] = []

    tile_x = int((mouse_pos[0] + camera_offset[0]) // block_size)
    tile_y = int((mouse_pos[1] + camera_offset[1]) // block_size)
    
    # Aggiungi il blocco di legno al chunk
    chunks[chunk_key].append([tile_x, tile_y, 6])  # 6 potrebbe essere l'ID per il legno
    items_in_slot[selected_slot]['quantity'] -= 1
    
    if items_in_slot[selected_slot]['quantity'] == 0:
        items_in_slot[selected_slot] = None

def remove_wood(mouse_pos, chunks, camera_offset):
    chunk_x = int((mouse_pos[0] + camera_offset[0]) // (CHUNK_SIZE * block_size))
    chunk_y = int((mouse_pos[1] + camera_offset[1]) // (CHUNK_SIZE * block_size))
    chunk_key = (chunk_x, chunk_y)
    
    if chunk_key in chunks:
        tile_x = int((mouse_pos[0] + camera_offset[0]) // block_size)
        tile_y = int((mouse_pos[1] + camera_offset[1]) // block_size)
        for tile in chunks[chunk_key]:
            if tile[0] == tile_x and tile[1] == tile_y and tile[2] == 6:  # 6 è l'ID per il legno
                chunks[chunk_key].remove(tile)
                break  
def use_trigger(mouse_pos, chunks, camera_offset, all_drops):
    global mouse_press_start_time, snails

    click = pg.mouse.get_pressed()
    current_time = time.time()

    player_center = (character_x + character_width // 2, character_y + character_height // 2)
    radius = 200

    if click[0]:  # Left click
        for snail in snails[:]:  # Use a copy of the list to safely remove items
            snail_pos = (snail.x, snail.y)
            distance = pg.math.Vector2(player_center).distance_to(snail_pos)

            if distance <= radius:
                snails.remove(snail)
                # Add hot shell drops
                num_hot_shell_drops = random.randint(1, 3)
                for _ in range(num_hot_shell_drops):
                    drop_x = snail.x + random.randint(-10, 10)
                    drop_y = snail.y - random.randint(10, 20)
                    all_drops.append([float(drop_x), float(drop_y), 0.0, "hot shell"])


def update_drops(wood_drops, world, ground_level):
    # Aggiorna la posizione dei drop chiamando drop_gravity
    wood_drops = drop_gravity(wood_drops, world, ground_level)
    # Potresti aggiungere qui la logica per disegnare i drop sullo schermo o per altre azioni
    return wood_drops

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
    global filter_background
    filter_background = pg.image.load("images/night.jpg")
    filter_background = pg.transform.scale(filter_background, (1280, 720))
    filter_background.set_alpha(opacity)  # Imposta l'opacità del filtro
    screen.blit(filter_background, (0, 0))  # Applica il filtro notte allo schermo


def play_music(track):
    pg.mixer.music.load(track)
    pg.mixer.music.play(-1)  # Riproduce in loop infinito
    print(f"Playing {track}")
    pg.mixer.music.set_volume(0.7)  # Imposta volume musicale

def stop_music():
    pg.mixer.music.fadeout(1000)
    print("Music stopped")

def gameplay():
    global character_x, character_y, character_height, opacity, screen, health, drops, items_in_slot, snails
    
    health, character_x, character_y, items_in_slot, chunks, snails = load_game()

    # Inizializzazioni
    clock = pg.time.Clock()
    all_drops = []  # Combined list for all types of drops

    tree_img = pg.image.load("images/tree.png")
    tree_img = pg.transform.scale(tree_img, (200, 400))

    wood_drop_img = pg.image.load("images/wood_drop.png")
    wood_drop_img = pg.transform.scale(wood_drop_img, (75, 75))

    hot_shell_drop_img = pg.image.load("images/hot_shell.png")
    hot_shell_drop_img = pg.transform.scale(hot_shell_drop_img, (75, 75))

    background_img = pg.image.load("images/background.jpg")
    background_img = pg.transform.scale(background_img, (1280, 720))

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
            current_time = pg.time.get_ticks()

            if current_time - last_save_time >= 1000:
                save_game(health, character_x, character_y, items_in_slot, chunks, snails)
                last_save_time = current_time

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_p:
                        is_paused = not is_paused
                    if event.key == pg.K_e:
                        crafting_menu()
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        use_trigger(event.pos, chunks, camera_offset, all_drops)
                        break_block(event.pos, chunks, camera_offset)
                        break_tree(event.pos, chunks, camera_offset, all_drops)
                    elif event.button == 3:  # Right click
                        place_block(event.pos, chunks, camera_offset)
                        place_torch(event.pos, chunks, camera_offset)

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
            spawn_snails(camera_offset, screen.get_width(), screen.get_height())
            update_snails(time_delta)
            draw_snails(screen, camera_offset)
            check_snail_collision()

            # Draw collection circle
            player_center = (character_x - camera_offset[0] + character_width // 2, 
                             character_y - camera_offset[1] + character_height // 2)
            pg.draw.circle(screen, (255, 0, 0), player_center, 200, 2)
            day_and_night(opacity)

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
            pg.key.get_pressed()

            # Draw light source (e.g., torch) on top of the opacity effect
            light_pos = (character_x - camera_offset[0], character_y - camera_offset[1])  # Example position
            light_radius = 100
            light_color = (255, 255, 100)  # Light yellow color
            # draw_light(screen, light_pos, light_radius, light_color)

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
            for chunk_key in chunks:
                chunk = chunks[chunk_key]
                for tile in chunk:
                    tile_x, tile_y, tile_type = tile
                    if tile_type == 5:  # Torch
                        torch_pos = (tile_x * block_size, tile_y * block_size)
                        draw_torch_light(screen, torch_pos, camera_offset, chunks, opacity)

            if is_over_tree:
                screen.blit(trigger_cursor_img, mouse_pos)
            else:
                screen.blit(default_cursor_img, mouse_pos)

            # Draw character
            screen.blit(character_img, (character_x - camera_offset[0], character_y - camera_offset[1]))

            pg.display.update()
        else:
            # Display paused screen or other UI elements here
            pass


# Costanti per la direzione delle luFche
class Snail:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 50  # Aumentato per inseguire il giocatore
        self.texture = pg.image.load("images/hash_snail.png").convert_alpha()
        self.texture = pg.transform.scale(self.texture, (125, 125))

def spawn_snails(camera_offset, screen_width, screen_height):
    if random.randint(1, 300) == 1:  # 1 su 300 chance di spawn
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x = random.randint(0, screen_width)
            y = camera_offset[1] - 125
        elif side == 'bottom':
            x = random.randint(0, screen_width)
            y = camera_offset[1] + screen_height
        elif side == 'left':
            x = camera_offset[0] - 125
            y = random.randint(0, screen_height)
        else:  # right
            x = camera_offset[0] + screen_width
            y = random.randint(0, screen_height)
        snails.append(Snail(x, y))

def update_snails(dt):
    global character_x, character_y
    for snail in snails:
        dx = character_x - snail.x
        snail.x += (dx / abs(dx)) * snail.speed * dt
        snail.y = character_y  # Mantiene le lumache sulla stessa y del personaggio

def draw_snails(screen, camera_offset):
    for snail in snails:
        screen_x = snail.x - camera_offset[0]
        screen_y = snail.y - camera_offset[1]
        screen.blit(snail.texture, (screen_x, screen_y))
def check_snail_collision():
    global health, last_collision_time
    current_time = pg.time.get_ticks()
    
    for snail in snails:
        if pg.Rect(character_x, character_y, character_width, character_height).colliderect(
            pg.Rect(snail.x, snail.y, 125, 125)):
            if current_time - last_collision_time > 3000:  # 3 secondi di cooldown
                health -= 10
                last_collision_time = current_time
            

def break_block(mouse_pos, chunks, camera_offset):
    for chunk_key in chunks:
        chunk = chunks[chunk_key]
        for tile in chunk[:]:
            tile_x, tile_y, tile_type = tile
            tile_rect = pg.Rect(tile_x * block_size - camera_offset[0], tile_y * block_size - camera_offset[1], block_size, block_size)
            
            if tile_rect.collidepoint(mouse_pos):
                chunk.remove(tile)
                add_to_slot(f"block_{tile_type}")
                return

def place_block(mouse_pos, chunks, camera_offset):
    global items_in_slot, selected_slot
    
    if items_in_slot[selected_slot] is None or not items_in_slot[selected_slot]['item'].startswith('block_'):
        return

    block_type = int(items_in_slot[selected_slot]['item'].split('_')[1])
    
    chunk_x = int((mouse_pos[0] + camera_offset[0]) // (CHUNK_SIZE * block_size))
    chunk_y = int((mouse_pos[1] + camera_offset[1]) // (CHUNK_SIZE * block_size))
    chunk_key = (chunk_x, chunk_y)
    
    if chunk_key not in chunks:
        chunks[chunk_key] = []

    tile_x = int((mouse_pos[0] + camera_offset[0]) // block_size)
    tile_y = int((mouse_pos[1] + camera_offset[1]) // block_size)
    
    chunks[chunk_key].append([tile_x, tile_y, block_type])
    items_in_slot[selected_slot]['quantity'] -= 1
    
    if items_in_slot[selected_slot]['quantity'] == 0:
        items_in_slot[selected_slot] = None

def draw_slots():
    global slot_positions, selected_slot, items_in_slot
    screen_width = screen.get_width()
    toolbar_y = 670
    
    total_slots_width = (slot_size + 10) * 10 - 10
    start_x = screen_width - total_slots_width

    slot_positions = [(start_x + i * (slot_size + 10), toolbar_y) for i in range(10)]

    for i, pos in enumerate(slot_positions):
        color = (255, 0, 0) if i == selected_slot else (0, 255, 0)
        slot_rect = pg.Rect(pos[0], pos[1], slot_size, slot_size)
        pg.draw.rect(screen, color, slot_rect, 2)

        if items_in_slot[i] is not None:
            if items_in_slot[i]['item'] == "wood":
                item_image = wood_drop_img
            elif items_in_slot[i]['item'] == "hot shell":
                item_image = hot_shell_drop_img
            elif items_in_slot[i]['item'] == "block_1":  # Grass
                item_image = pg.image.load("images/grass.jpg")
            elif items_in_slot[i]['item'] == "block_2":  # Dirt
                item_image = pg.image.load("images/dirt.jpg")
                item_image = pg.transform.scale(item_image, (slot_size * 0.075, slot_size * 0.075))
            else:
                item_image = wood_drop_img  # Default image
            item_image = pg.transform.scale(item_image, (slot_size, slot_size))
            screen.blit(item_image, (pos[0], pos[1]))
            
        number_of_items = items_in_slot[i]['quantity'] if items_in_slot[i] is not None else 0
        font = pg.font.Font(None, 24)
        text_surface = font.render(f"{number_of_items}", True, (255, 255, 255))
        screen.blit(text_surface, (pos[0] + slot_size - text_surface.get_width(), pos[1] + slot_size - text_surface.get_height()))


def tool_bar_logic():
    global selected_slot, slot_positions
    mouse_pos = pg.mouse.get_pos()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse click
                for i, pos in enumerate(slot_positions):
                    slot_rect = pg.Rect(pos[0], pos[1], slot_size, slot_size)
                    if slot_rect.collidepoint(mouse_pos):
                        selected_slot = i
                        break
            elif event.button == 4:  # Mouse wheel up
                selected_slot = (selected_slot - 1) % len(slot_positions)
            elif event.button == 5:  # Mouse wheel down
                selected_slot = (selected_slot + 1) % len(slot_positions)

    draw_slots()  # Draw updated slots


def add_to_slot(item):
    global items_in_slot

    max_quantity = 0
    slot_index_to_add = None

    for i, slot in enumerate(items_in_slot):
        if slot is not None:
            if slot['item'] == item:
                if slot['quantity'] > max_quantity:
                    max_quantity = slot['quantity']
                    slot_index_to_add = i

    if slot_index_to_add is None:
        for i, slot in enumerate(items_in_slot):
            if slot is None:
                slot_index_to_add = i
                break

    if slot_index_to_add is not None:
        if items_in_slot[slot_index_to_add] is None:
            items_in_slot[slot_index_to_add] = {'item': item, 'quantity': 1}
        else:
            if items_in_slot[slot_index_to_add]['item'] == item and items_in_slot[slot_index_to_add]['quantity'] < 999:
                items_in_slot[slot_index_to_add]['quantity'] += 1


def collect_items(all_drops):
    global character_x, character_y, character_width, character_height, items_in_slot

    character_rect = pg.Rect(character_x, character_y, character_width, character_height)

    for drop in all_drops[:]:
        if isinstance(drop, (tuple, list)) and len(drop) >= 4:
            try:
                drop_x, drop_y, drop_fall_speed, drop_type = drop
                drop_rect = pg.Rect(drop_x, drop_y, 75, 75)

                if character_rect.colliderect(drop_rect):
                    add_to_slot(drop_type)
                    all_drops.remove(drop)
            except ValueError:
                print(f"Invalid drop format: {drop}")
    
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