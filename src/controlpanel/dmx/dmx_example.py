from controlpanel.dmx import DMXUniverse, device_list
import pygame as pg


if __name__ == "__main__":
    dmx_universe = DMXUniverse(None, devices=device_list, target_frequency=10)

    pg.init()
    screen = pg.display.set_mode((480, 360))

    clock = pg.time.Clock()
    tick = 0
    
    while True:
        tick += 1

        dmx_universe.devices.get("Laser").color += 1
        dmx_universe.devices.get("Spot1").color = (255, 0, 0, 0) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot2").color = (0, 255, 0, 0) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot3").color = (0, 0, 255, 0) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot4").color = (0, 0, 0, 255) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot5").color = (255, 255, 0, 0) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot6").color = (0, 255, 255, 0) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("Spot7").color = (0, 0, 255, 255) if tick % 2 == 0 else (255, 255, 255, 255)
        dmx_universe.devices.get("StarBar1").leds[2] = (255, 255, 255) if tick % 2 == 0 else (0, 0, 0)
        dmx_universe.devices.get("StarBar2").leds[2] = (255, 255, 255) if tick % 2 == 0 else (0, 0, 0)

        for event in pg.event.get():
            ...

        keys_pressed = pg.key.get_pressed()
        
        if keys_pressed[pg.K_a]:
            ...
        if keys_pressed[pg.K_d]:
            ...
        if keys_pressed[pg.K_w]:
            ...
        if keys_pressed[pg.K_s]:
            ...
        
        screen.fill((16, 16, 16))

        pg.event.pump()
        pg.display.flip()

        print(dmx_universe.data)

        clock.tick(2)
