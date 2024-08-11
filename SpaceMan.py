import random
import sys
import time
import pygame as pg
import pygame_gui as pgui
import noise

CHUNK_SIZE = 24
LEFT = -1
RIGHT = 1
# Impostazioni di base
direction = 'right' 
health = 100
coin = 0
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

def UI(health, mouse_pos):
    hearth_width, hearth_height = 50, 50
    hearth = pg.transform.scale(hearth_img, (hearth_width, hearth_height))
    broken_hearth = pg.transform.scale(broken_hearth_img, (hearth_width, hearth_height))
    
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
def movement(world):
    global character_x, character_y, is_jumping, jump_speed, gravity, character_img, direction
    print(character_x, character_y)
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

def break_tree(mouse_pos, chunks, camera_offset, wood_drops):
    for chunk_key in chunks:
        chunk = chunks[chunk_key]
        for tile in chunk:
            tile_x, tile_y, tile_type = tile
            if tile_type == 4:  # Se è un albero
                tree_pos = spawn_tree(tile_x, tile_y, block_size)
                # Regola la posizione dell'albero in base allo spostamento della telecamera
                tree_rect = pg.Rect(tree_pos[0] - camera_offset[0], tree_pos[1] - camera_offset[1], 200, 400)
                
                if tree_rect.collidepoint(mouse_pos):
                    print("Tree hit detected at:", tree_pos)
                    chunk.remove(tile)
                    num_wood_drops = random.randint(3, 7)  # Numero di pezzi di legno
                    for _ in range(num_wood_drops):
                        # Posizione iniziale del pezzo di legno
                        wood_drop_x = tree_pos[0] + random.randint(5, 10)  # Posizione X del drop
                        wood_drop_y = tree_pos[1] - 100  # Posizione Y del drop, 100 pixel sopra il suolo
                        print(wood_drop_x, wood_drop_y)
                        wood_drops.append([wood_drop_x, wood_drop_y, 0, "wood"])  # 0 è la velocità iniziale di caduta
                        
                    return

def update_and_draw_drops(wood_drops, world, ground_level, block_size, screen, wood_drop_img, camera_offset):
    wood_drops = drop_gravity(wood_drops, world, ground_level, block_size)

    drop_width = 75
    drop_height = 75
    
    for drop in wood_drops:
        # Crea un rettangolo per il drop
        drop_rect = pg.Rect(drop[0], drop[1], drop_width, drop_height)
        
        # Disegna il drop
        screen.blit(wood_drop_img, (drop[0] - camera_offset[0], drop[1] - camera_offset[1]))

    return wood_drops


def use_trigger(mouse_pos, chunks, camera_offset, wood_drops):
    global mouse_press_start_time
    click = pg.mouse.get_pressed()
    current_time = time.time()

    if click[0]:  # Se il tasto sinistro del mouse è premuto
        if mouse_press_start_time is None:
            mouse_press_start_time = current_time  # Inizia il cronometro
        elif current_time - mouse_press_start_time >= mouse_held_duration:
            break_tree(mouse_pos, chunks, camera_offset, wood_drops)  # Chiama la funzione per rompere l'albero
            mouse_press_start_time = None  # Resetta il cronometro dopo l'azione
    else:
        mouse_press_start_time = None  # Resetta il cronometro se il mouse viene rilasciato

def update_drops(wood_drops, world, ground_level):
    # Aggiorna la posizione dei drop chiamando drop_gravity
    wood_drops = drop_gravity(wood_drops, world, ground_level)
    # Potresti aggiungere qui la logica per disegnare i drop sullo schermo o per altre azioni
    return wood_drops

    
    
def day_and_night(opacity):
    filter_background = pg.image.load("images/night.jpg")
    filter_background = pg.transform.scale(filter_background, (1280, 720))
    filter_background.set_alpha(opacity)  # Imposta l'opacità del filtro
    screen.blit(filter_background, (0, 0))  # Applica il filtro notte allo schermo

def gameplay():
    global character_x, character_y, character_height, opacity, active_hash_snails, screen, health, drops
    
    # Inizializzazioni
    chunks = {}
    clock = pg.time.Clock()
    wood_drops = []

    tree_img = pg.image.load("images/tree.png")
    tree_img = pg.transform.scale(tree_img, (200, 400))

    wood_drop_img = pg.image.load("images/wood_drop.png")
    wood_drop_img = pg.transform.scale(wood_drop_img, (75, 75))

    background_img = pg.image.load("images/background.jpg")
    background_img = pg.transform.scale(background_img, (1280, 720))

    # Variabili per il ciclo giorno/notte
    day_night_cycle = 60000  # 60 secondi per un ciclo completo
    opacity = 0
    increasing = True  # Flag per determinare se aumentare o diminuire l'opacità
    last_time = pg.time.get_ticks()

    while True:
        time_delta = clock.tick(60) / 1000.0

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()

        screen.blit(background_img, (0, 0))

        # Calcola l'offset della camera
        camera_offset = [character_x - screen.get_width() // 2, character_y - screen.get_height() // 2]

        # Determina il chunk corrente del personaggio
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
                        pg.draw.rect(screen, (34, 139, 34), tile_rect)  # Erba
                    elif tile_type == 2:
                        pg.draw.rect(screen, (139, 69, 19), tile_rect)  # Terra
                    elif tile_type == 3:
                        pg.draw.rect(screen, (169, 169, 169), tile_rect)  # Pietra
                    elif tile_type == 4:
                        tree_pos = spawn_tree(tile_x, tile_y, block_size)
                        screen.blit(tree_img, (tree_pos[0] - camera_offset[0], tree_pos[1] - camera_offset[1]))

        # Interfaccia utente
        mouse_pos = pg.mouse.get_pos()
        UI(health, mouse_pos)
        use_trigger(mouse_pos, chunks, camera_offset, wood_drops)

        # Movimenti del personaggio e gestione oggetti
        movement(chunks)
        wood_drops = update_and_draw_drops(wood_drops, chunks, character_y + character_height, block_size, screen, wood_drop_img, camera_offset)
        collect_items(wood_drops)

        day_time_monster(screen, character_y, character_height, opacity, active_hash_snails)
        update_snail_positions(active_hash_snails)
        handle_snail_death(active_hash_snails, drops)
        remove_extra_mob(active_hash_snails)

        # Gestisci le collisioni
        handle_collisions(active_hash_snails, character_x, character_y)

        # Disegna le lumache
        draw_snails(screen, active_hash_snails, camera_offset)


        # Ciclo giorno/notte
        current_time = pg.time.get_ticks()
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

        # Controllo se il mouse è sopra un albero
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

        # Cambia il cursore in base alla posizione del mouse
        if is_over_tree:
            screen.blit(trigger_cursor_img, mouse_pos)
        else:
            screen.blit(default_cursor_img, mouse_pos)

        # Disegna il personaggio
        screen.blit(character_img, (character_x - camera_offset[0], character_y - camera_offset[1]))

        pg.display.update()


# Costanti per la direzione delle lumache
def day_time_monster(screen, character_y, character_height, opacity, active_hash_snails):
    if opacity < 200:  # Controlla se è giorno
        spawn_probability = random.randint(1, 100)
        
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
    global health  # Usa la variabile globale health
    character_rect = pg.Rect(character_x, character_y, 50, 50)
    
    for snail in active_hash_snails[:]:
        # Controlla collisioni con il giocatore
        if snail["rect"].colliderect(character_rect):
            # Verifica che la lumaca sia a terra (y == 150)
            if snail["rect"].y == 150:  
                health -= 10  # Riduci la salute del giocatore
                get_knockback(character_rect, snail)  # Applica il knockback

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

def handle_snail_death(active_hash_snails, drops):
    if pg.mouse.get_pressed()[0]:  # Tasto sinistro del mouse premuto
        mouse_x, mouse_y = pg.mouse.get_pos()
        mouse_rect = pg.Rect(mouse_x, mouse_y, 1, 1)  # Rettangolo per il rilevamento del mouse

        for snail in active_hash_snails[:]:  # Itera sulle lumache attive
            if mouse_rect.colliderect(snail["rect"]):  # Verifica la collisione con il mouse
                snail["health"] -= 1  # Riduci la salute della lumaca
                if snail["health"] <= 0:  # Controlla se la salute è esaurita
                    # Crea un drop alla posizione della lumaca
                    drop = {"type": "hot shell", "position": (snail["rect"].x, snail["rect"].y)}
                    drops.append(drop)  # Aggiungi il drop alla lista dei drops
                    active_hash_snails.remove(snail)  # Rimuovi la lumaca dalla lista delle lumache attive
        print(f"Mouse Pos: ({mouse_x}, {mouse_y})")
        for snail in active_hash_snails:
            print(f"Snail Pos: ({snail['rect'].x}, {snail['rect'].y}) Health: {snail['health']}")

def remove_extra_mob(active_hash_snails):
    while len(active_hash_snails) > 10:  # Rimuovi lumache extra se ce ne sono più di 10
        active_hash_snails.pop(0)

def draw_slots():
    global slot_positions, selected_slot
    screen_width = screen.get_width()  # Get the width of the screen
    toolbar_y = 670  # Position the toolbar at the bottom of the screen
    
    total_slots_width = (slot_size + 10) * 10 - 10  # Total width of all slots including spacing
    start_x = screen_width - total_slots_width  # Start position for the slots

    slot_positions = [(start_x + i * (slot_size + 10), toolbar_y) for i in range(10)]  # Updated positions of slots

    for i, pos in enumerate(slot_positions):
        color = (255, 0, 0) if i == selected_slot else (0, 255, 0)
        slot_rect = pg.Rect(pos[0], pos[1], slot_size, slot_size)
        pg.draw.rect(screen, color, slot_rect, 2)

        # Draw item in the slot if there's an item
        if items_in_slot[i] is not None:
            item_image = wood_drop_img  # Placeholder for item image
            screen.blit(item_image, (pos[0], pos[1]))
        number_of_items = items_in_slot[i]['quantity'] if items_in_slot[i] is not None else 0
        font = pg.font.Font(None, 24)  # Load a font
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

    # Trova lo slot con la maggiore quantità di oggetti dello stesso tipo
    max_quantity = 0
    slot_index_to_add = None

    for i, slot in enumerate(items_in_slot):
        if slot is not None:
            if slot['item'] == item:
                if slot['quantity'] > max_quantity:
                    max_quantity = slot['quantity']
                    slot_index_to_add = i

    # Se non è stato trovato uno slot con lo stesso tipo di oggetto, cerca uno slot vuoto
    if slot_index_to_add is None:
        for i, slot in enumerate(items_in_slot):
            if slot is None:
                slot_index_to_add = i
                break

    # Se è stato trovato uno slot valido, aggiungi l'oggetto
    if slot_index_to_add is not None:
        if items_in_slot[slot_index_to_add] is None:
            items_in_slot[slot_index_to_add] = {'item': item, 'quantity': 1}
        else:
            if items_in_slot[slot_index_to_add]['item'] == item and items_in_slot[slot_index_to_add]['quantity'] < 999:
                items_in_slot[slot_index_to_add]['quantity'] += 1


def collect_items(drops):
    global character_x, character_y, character_width, character_height, items_in_slot

    character_rect = pg.Rect(character_x, character_y, character_width, character_height)

    for drop in drops[:]:  # Iterate over a copy of the list to allow modification
        if isinstance(drop, (tuple, list)) and len(drop) >= 4:
            try:
                drop_x, drop_y, drop_fall_speed, drop_type = drop
                drop_rect = pg.Rect(drop_x, drop_y, 75, 75)  # Size of the drop item

                if character_rect.colliderect(drop_rect):
                    add_to_slot(drop_type)  # Add the item to the selected slot
                    drops.remove(drop)  # Remove the collected item
            except ValueError:
                print(f"Invalid drop format: {drop}")  # Debugging output


    
def menu():
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

menu()
