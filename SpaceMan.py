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


def save_game(health, character_x, character_y, items_in_slot, chunks):
    data = {
        'health': health,
        'character_x': character_x,
        'character_y': character_y,
        'items_in_slot': items_in_slot,
        'chunks': {f"{key}": value for key, value in chunks.items()}  # Convert tuples to strings
    }
    with open('save_game.json', 'w') as f:
        json.dump(data, f, indent=4)



def load_game():
    try:
        with open('save_game.json', 'r') as f:
            data = json.load(f)
        
        # Convert chunk keys from strings back to tuples
        chunks_serializable = data.get('chunks', {})
        chunks = {eval(key): value for key, value in chunks_serializable.items()}
        
        # Retrieve and validate each item
        items_in_slot = data.get('items_in_slot', [None] * 10)
        if not isinstance(items_in_slot, list) or len(items_in_slot) != 10:
            items_in_slot = [None] * 10
        
        for i in range(len(items_in_slot)):
            if items_in_slot[i] is not None:
                item = items_in_slot[i]
                if not isinstance(item, dict):
                    items_in_slot[i] = None
                elif 'item' not in item or 'quantity' not in item:
                    items_in_slot[i] = None
                else:
                    # Validate item fields
                    if not isinstance(item['item'], str):
                        items_in_slot[i] = None
                    elif not isinstance(item['quantity'], int) or item['quantity'] < 0:
                        items_in_slot[i] = None
        
        return (
            data.get('health', 100),
            data.get('character_x', 0),
            data.get('character_y', 0),
            items_in_slot,
            chunks
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading game: {e}")
        # Return default values in case of an error
        return (
            100,  # default health
            0,    # default character_x
            0,    # default character_y
            [None] * 10,  # default items_in_slot
            {}    # default chunks
        )


def initialize_game():
    global health, character_x, character_y, items_in_slot, chunks
    health = 100
    character_x = 0
    character_y = 100
    items_in_slot = [None] * 10
    chunks = {}
    
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
    # Variabili del menu
    
    bar_width, bar_height = 800, 100
    bar_x, bar_y = (screen.get_width() - bar_width) // 2, (screen.get_height() - bar_height) // 2
    bar_color = ()  # Colore di sfondo della barra
    item_size = 50
    items_per_bar = bar_width // item_size
    scroll_speed = 10
    
    
    
    # Stato della scroll
    scroll_pos = 0
    max_scroll = max(0, len(item_images) - items_per_bar)
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 4:  # Rotella del mouse su
                    scroll_pos = max(0, scroll_pos - 1)
                elif event.button == 5:  # Rotella del mouse giù
                    scroll_pos = min(max_scroll, scroll_pos + 1)

        # Pulisce lo schermo

        # Disegna la barra di crafting
        pg.draw.rect(screen, bar_color, (bar_x, bar_y, bar_width, bar_height))

        # Disegna gli oggetti craftabili
        for i in range(items_per_bar):
            index = scroll_pos + i
            if index < len(item_images):
                item_x = bar_x + i * item_size
                item_y = bar_y + (bar_height - item_size) // 2
                screen.blit(item_images[index], (item_x, item_y))

        # Aggiorna lo schermo
        pg.display.update()
        
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
    global character_x, character_y, character_height, opacity, active_hash_snails, screen, health, drops, items_in_slot
    # Carica i dati di gioco salvati
    health, character_x, character_y, items_in_slot, chunks = load_game()

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

            # Salva il gioco solo se è trascorso un intervallo di tempo
            current_time = pg.time.get_ticks()
            if current_time - last_save_time >= 1000:  # 1 secondo
                save_game(health, character_x, character_y, items_in_slot, chunks)
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

            day_time_monster(screen, character_y, character_height, opacity, active_hash_snails)
            handle_input_and_damage(active_hash_snails, character_x, character_y, all_drops)
            
            update_snail_positions(active_hash_snails)
            draw_snails(screen, active_hash_snails, camera_offset)
            day_and_night(opacity)
            handle_collisions(active_hash_snails, character_x, character_y)
            remove_extra_mob(active_hash_snails)

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
def day_time_monster(screen, character_y, character_height, opacity, active_hash_snails):
    if opacity < 200:  # Controlla se è giorno
        spawn_probability = random.randint(1, 300)
        
        if spawn_probability == 100:  # Controlla la probabilità di spawn
            # Genera una posizione di spawn casuale sulla larghezza dello schermo
            spawn_x = random.randint(0, screen.get_width() - 100)  # Posizione X casuale, 100 è la larghezza dell'immagine
            spawn_y = fixed_y_positions[0]  # Posizione Y al livello del terreno
            
            hash_snail_img = pg.image.load("images/hash_snail.png")
            hash_snail_img = pg.transform.scale(hash_snail_img, (100, 100))
            hash_snail_img_rect = pg.Rect(spawn_x, spawn_y, 100, 100)
            hash_snail_health = 2  # 2 colpi necessari per distruggere una lumaca
            
            direction = random.choice([-1, 1])  # LEFT = -1, RIGHT = 1
            active_hash_snails.append({
                "rect": hash_snail_img_rect, 
                "image": hash_snail_img, 
                "health": hash_snail_health,
                "direction": direction,
                "movement_timer": pg.time.get_ticks()
            })

def update_snail_positions(active_hash_snails):
    for snail in active_hash_snails:
        # Muovi la lumaca solo orizzontalmente
        snail["rect"].x += snail["direction"] * 1  # Muove la lumaca di un blocco

def draw_snails(screen, active_hash_snails, camera_offset):
    for snail in active_hash_snails:
        # Disegna la lumaca utilizzando le coordinate assolute
        screen.blit(snail["image"], (snail["rect"].x - camera_offset[0], snail["rect"].y - camera_offset[1]))

def handle_collisions(active_hash_snails, character_x, character_y):
    global health, last_collision_time
    current_time = pg.time.get_ticks()
    character_rect = pg.Rect(character_x, character_y, 75, 75)
    collision_cooldown = 3000  # Tempo di cooldown per la collisione
    for snail in active_hash_snails[:]:
        if snail["rect"].colliderect(character_rect):
            # Verifica che la lumaca sia a terra (y <= 150 o y >= 300)
            if snail["rect"].y <= 150 or snail["rect"].y >= 300:
                # Controlla se è passato abbastanza tempo per applicare una nuova collisione
                if current_time - last_collision_time >= collision_cooldown:
                    health -= 10  # Riduci la salute del giocatore
                    get_knockback(character_rect, snail)  # Applica il knockback
                    last_collision_time = current_time  # Aggiorna l'ultimo tempo di collisione

                    

def get_knockback(character_rect, snail):
    knockback_distance = 50  # Distanza di knockback
    if character_rect.centerx > snail["rect"].centerx:  # Se il personaggio è a destra della lumaca
        character_rect.x += knockback_distance  # Muovi il personaggio verso destra
    else:  # Se il personaggio è a sinistra della lumaca
        character_rect.x -= knockback_distance  # Muovi il personaggio verso sinistra

    if character_rect.centery > snail["rect"].centery:  # Se il personaggio è sotto la lumaca
        character_rect.y += knockback_distance  # Muovi il personaggio verso il basso
    else:  # Se il personaggio è sopra la lumaca
        character_rect.y -= knockback_distance  # Muovi il personaggio verso l'alto

def damage_snails_within_radius(active_hash_snails, character_x, character_y, damage_radius, damage_amount, all_drops):
    for snail in active_hash_snails[:]:
        snail_center_x = snail["rect"].centerx
        snail_center_y = snail["rect"].centery
        distance = ((snail_center_x - character_x) ** 2 + (snail_center_y - character_y) ** 2) ** 0.5
        
        if distance <= damage_radius:
            snail["health"] -= damage_amount
            if snail["health"] <= 0:
                all_drops.append([float(snail["rect"].x), float(snail["rect"].y), 0.0, "hot shell"])
                active_hash_snails.remove(snail)
                
def handle_input_and_damage(active_hash_snails, character_x, character_y, all_drops):
    click = pg.mouse.get_pressed()[0]
    if click: 
        damage_radius = 200
        damage_amount = 1
        damage_snails_within_radius(active_hash_snails, character_x, character_y, damage_radius, damage_amount, all_drops)

def remove_extra_mob(active_hash_snails):
    while len(active_hash_snails) > 10:  # Rimuovi lumache extra se ce ne sono più di 10
        active_hash_snails.pop(0)

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
            else:
                item_image = wood_drop_img  # Default image
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
