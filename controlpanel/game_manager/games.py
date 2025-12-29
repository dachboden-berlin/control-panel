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
        self.error_color_index: int = 0
        self.error_velocity: pg.Vector2 = pg.Vector2(50, 50)
        self.error_text = "Dear CCC, feel free to uncover the mysteries this panel has to offer."
        self.error_surf = self._get_error_surf()
        self.error_position: pg.Vector2 = (pg.Vector2(self.screen.get_rect().center) -
                                           pg.Vector2(self.error_surf.get_rect().center))

    def _get_error_surf(self) -> pg.Surface:
        return pg.font.Font(None, 36).render(
            self.error_text,
            True, self.COLORS[self.error_color_index], None)

    def update(self) -> None:
        self.error_position += self.error_velocity * self.dt
        bounce_count = 0
        if self.error_position.x + self.error_surf.get_width() > self.screen.get_width() or self.error_position.x < 0:
            self.error_position.x = max(0, min(self.screen.get_width() - self.error_surf.get_width(), int(self.error_position.x)))
            self.error_velocity.x *= -1
            bounce_count += 1
        if self.error_position.y + self.error_surf.get_height() > self.screen.get_height() or self.error_position.y < 0:
            self.error_position.y = max(0, min(self.screen.get_height() - self.error_surf.get_height(), int(self.error_position.y)))
            bounce_count += 1
            self.error_velocity.y *= -1
        if bounce_count == 1:
            self.error_color_index += 1
            if self.error_color_index >= len(self.COLORS):
                self.error_color_index = 0
                random.shuffle(self.COLORS)
            self.error_surf = self._get_error_surf()
        elif bounce_count == 2:
            print("pog")

    def render(self) -> None:
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.error_surf, self.error_position)
