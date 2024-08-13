
import pygame as pg

def play_music(track):
    pg.mixer.music.load(track)
    pg.mixer.music.play(-1)  # Riproduce in loop infinito
    print(f"Playing {track}")
    pg.mixer.music.set_volume(0.7)  # Imposta volume musicale

def stop_music():
    pg.mixer.music.fadeout(1000)
    print("Music stopped")