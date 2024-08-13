import pygame as pg
from settings import *
from images import *
from terrain import *

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
        