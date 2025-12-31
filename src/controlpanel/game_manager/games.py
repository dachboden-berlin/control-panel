import pygame as pg
from anaconsole import console_command
import random


class BaseGame:
    """Base class to be used for all games as inheritance."""
    def __init__(self,
                 name: str,
                 resolution: tuple[int, int],
                 *,
                 tickrate: float = 30.0,
                 timescale: float = 1.0,
                 ):
        self.name: str = name
        self.screen: pg.Surface = pg.Surface(resolution)
        self._base_tickrate: float = tickrate
        self._tickrate: float = tickrate * timescale
        self._timescale: float = timescale
        self._working_directory_override: str | None = None
        self._joysticks: dict[int, pg.joystick.JoystickType] = {}
        self._dt: float = 1 / tickrate * timescale
        # self.fallback_shaders = Shaders([resolution], [(-1, "To_BGRA", {"_MainTex": 0})])
        # self.shaders = shaders if shaders is not None else self.fallback_shaders

    @property
    def working_directory_override(self) -> str:
        return self._working_directory_override

    @property
    def tickrate(self) -> float:
        return self._tickrate

    @tickrate.setter
    def tickrate(self, tickrate: float):
        self._base_tickrate = tickrate
        self._tickrate = tickrate * self._timescale

    @console_command("tickrate", is_cheat_protected=True, hint=lambda self: self.tickrate)
    def set_tickrate(self, tickrate: float):
        """Sets the tickrate (updates per second) of the game. Ideally has no impact on simulation speed."""
        self.tickrate = tickrate

    @property
    def timescale(self) -> float:
        return self._timescale

    @timescale.setter
    def timescale(self, new_timescale: float):
        self._timescale = new_timescale
        self._tickrate = self._base_tickrate * new_timescale

    @console_command("host_timescale", "timescale", is_cheat_protected=True, hint=lambda self: self.timescale)
    def set_timescale(self, timescale: float):
        """Sets the tick speed (game simulation speed). Default is 1.0"""
        self.timescale = timescale

    @property
    def dt(self) -> float:
        return self._dt

    def handle_events(self, events: list[pg.event.Event]) -> None:
        pass

    def update(self) -> None:
        pass

    def render(self) -> None:
        pass

    def standalone_run(self):
        """This method makes it possible for a game to be run without the controlpanel overhead.
        It is a self-contained game loop in its most vanilla and bare-bone form."""
        import argparse
        parser = argparse.ArgumentParser(description=self.name)
        parser.add_argument('-w', '--windowed', action='store_true', help='Run in windowed mode (fullscreen is default)')
        args = parser.parse_args()

        pg.init()
        self.screen = pg.display.set_mode(self.screen.get_size(), pg.FULLSCREEN if not args.windowed else 0)
        clock = pg.time.Clock()
        while True:
            self.handle_events(pg.event.get())
            self.update()
            self.render()

            pg.display.flip()
            self._dt = clock.tick(self._tickrate) / 1000 * self._timescale


class FallbackGame(BaseGame):
    """Bouncing DVD Logo inspired text animation. No inputs, just used as a fallback."""
    COLORS = [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255),]

    def __init__(self):
        super().__init__("Fallback Game", resolution=(960, 540))
        self.text_color_idx: int = 0
        self.text_velocity: pg.Vector2 = pg.Vector2(50, 50)
        self.text = "No GUI Script loaded. Use --no-gui to run headless."
        self.text_surf = self._get_error_surf()
        self.text_pos: pg.Vector2 = (pg.Vector2(self.screen.get_rect().center) -
                                     pg.Vector2(self.text_surf.get_rect().center))

    def _get_error_surf(self) -> pg.Surface:
        return pg.font.Font(None, 36).render(
            self.text,
            True, self.COLORS[self.text_color_idx], None)

    def update(self) -> None:
        self.text_pos += self.text_velocity * self.dt
        bounce_count = 0
        if self.text_pos.x + self.text_surf.get_width() > self.screen.get_width() or self.text_pos.x < 0:
            self.text_pos.x = max(0, min(self.screen.get_width() - self.text_surf.get_width(), int(self.text_pos.x)))
            self.text_velocity.x *= -1
            bounce_count += 1
        if self.text_pos.y + self.text_surf.get_height() > self.screen.get_height() or self.text_pos.y < 0:
            self.text_pos.y = max(0, min(self.screen.get_height() - self.text_surf.get_height(), int(self.text_pos.y)))
            bounce_count += 1
            self.text_velocity.y *= -1
        if bounce_count == 1:
            self.text_color_idx += 1
            if self.text_color_idx >= len(self.COLORS):
                self.text_color_idx = 0
                random.shuffle(self.COLORS)
            self.text_surf = self._get_error_surf()
        elif bounce_count == 2:
            print("pog")

    def render(self) -> None:
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.text_surf, self.text_pos)
