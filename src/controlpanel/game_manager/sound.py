import pygame as pg
pg.mixer.init()

def play_sound(path, volume=1.0, loops=0) -> pg.mixer.Sound:
    sound = pg.mixer.Sound(path)
    sound.set_volume(volume)
    sound.play(loops=loops)
    return sound
