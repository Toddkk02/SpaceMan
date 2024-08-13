import json
import pygame as pg

def save_game(health, character_x, character_y, items_in_slot, chunks, active_hash_snails):
    serializable_snails = []
    for snail in active_hash_snails:
        serializable_snail = {
            "rect": [snail["rect"].x, snail["rect"].y, snail["rect"].width, snail["rect"].height],
            "health": snail["health"],
            "direction": snail["direction"],
            "movement_timer": snail["movement_timer"]
        }
        serializable_snails.append(serializable_snail)

    data = {
        'health': health,
        'character_x': character_x,
        'character_y': character_y,
        'items_in_slot': items_in_slot,
        'chunks': {f"{key}": value for key, value in chunks.items()},
        'active_hash_snails': serializable_snails
    }
    with open('save_game.json', 'w') as f:
        json.dump(data, f, indent=4)


def load_game():
    try:
        with open('save_game.json', 'r') as f:
            data = json.load(f)
        
        chunks_serializable = data.get('chunks', {})
        chunks = {eval(key): value for key, value in chunks_serializable.items()}
        
        items_in_slot = data.get('items_in_slot', [None] * 10)
        for i in range(len(items_in_slot)):
            if items_in_slot[i] is not None:
                item = items_in_slot[i]
                if not isinstance(item, dict) or 'item' not in item or 'quantity' not in item:
                    items_in_slot[i] = None
                elif not isinstance(item['item'], str) or not isinstance(item['quantity'], int) or item['quantity'] < 0:
                    items_in_slot[i] = None

        active_hash_snails = []
        for snail_data in data.get('active_hash_snails', []):
            snail = {
                "rect": pg.Rect(*snail_data["rect"]),
                "image": pg.image.load("images/hash_snail.png"),
                "health": snail_data["health"],
                "direction": snail_data["direction"],
                "movement_timer": snail_data["movement_timer"]
            }
            snail["image"] = pg.transform.scale(snail["image"], (100, 100))
            active_hash_snails.append(snail)

        return (
            data.get('health', 100),
            data.get('character_x', 0),
            data.get('character_y', 0),
            items_in_slot,
            chunks,
            active_hash_snails
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading game: {e}")
        return (
            100,
            0,
            0,
            [None] * 10,
            {},
            []
        )

def initialize_game():
    global health, character_x, character_y, items_in_slot, chunks
    health = 100
    character_x = 0
    character_y = 100
    items_in_slot = [None] * 10
    chunks = {}
    
