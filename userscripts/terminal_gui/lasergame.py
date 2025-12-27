import pygame as pg
from math import sin, cos, radians, pi
from gui.widgets import Widget, Desktop
from gui.window_manager.window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, BACKGROUND_COLOR, DEFAULT_GAP
from controlpanel import dmx  # TODO: Fix console clutter coming from here


def spherical_to_cartesian(phi, theta) -> pg.Vector3:
    return pg.Vector3(sin(theta) * cos(phi),
                      sin(theta) * sin(phi),
                      cos(theta))


class Camera:
    def __init__(self, zoom: float, shift: pg.Vector2 = pg.Vector2(0, 0)) -> None:
        # Initial orientation facing 'forward' along the negative Z-axis
        self._yaw = pi / 4
        self._pitch = pi / 4
        self.position = spherical_to_cartesian(self._yaw, self._pitch)
        self.zoom = zoom
        self.shift = shift

    def project_point(self, point: pg.Vector3) -> pg.Vector2:
        from gui.widgets.stl_renderer import find_basis_vectors
        camera_angle = -self.position
        basis_x, basis_y = find_basis_vectors(camera_angle)
        basis_x = pg.Vector3(basis_x[0], basis_x[1], basis_x[2])
        basis_y = pg.Vector3(basis_y[0], basis_y[1], basis_y[2])

        # Translate points relative to the camera position
        translated_point = point - self.position
        return pg.Vector2(self.zoom * translated_point.dot(basis_x) + self.shift.x,
                          - self.zoom * translated_point.dot(basis_y) + self.shift.y)

    @property
    def yaw(self):
        return self._yaw

    @yaw.setter
    def yaw(self, angle: float):
        self._yaw = angle
        self.position = spherical_to_cartesian(self._yaw, self._pitch)

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, angle: float):
        angle = max(min(angle, 0.99 * pi), 0.01 * pi)
        self._pitch = angle
        self.position = spherical_to_cartesian(self._yaw, self._pitch)


class Entity:
    def __init__(self, position: pg.Vector3) -> None:
        self.position = position
        self.origins: set[Relay] = set()

    def draw(self, surface: pg.Surface, camera: Camera):
        center = camera.project_point(self.position)
        pg.draw.circle(surface, (255, 255, 0), center, 4)


class Relay(Entity):
    def __init__(self, moving_head: dmx.HydroBeamX12, position: pg.Vector3, orientation: pg.Vector3) -> None:
        super().__init__(position)
        self.orientation = orientation.normalize()
        self.moving_head = moving_head
        self.beam_vector: pg.Vector3
        self.target: Entity | None = None
        self.selected: bool = False
        self.recalculate_beam_vector()

    def recalculate_beam_vector(self):
        self.beam_vector = spherical_to_cartesian(self.moving_head._phi, self.moving_head._theta)

    def recalculate_connections(self, targets: list[Entity]):
        for target in targets:
            if target is self:
                continue
            vector_to_antenna = target.position - self.position
            angle = self.beam_vector.angle_to(vector_to_antenna)
            if angle <= 16 / 2:
                self.target = target
                target.origins.add(self)
                return
        self.target = None
        if target and self in target.origins:
            target.origins.remove(self)

    def draw(self, surface: pg.Surface, camera: Camera):
        super().draw(surface, camera)
        center = camera.project_point(self.position)
        if self.selected:
            pg.draw.circle(surface, (255, 255, 0), center, 8, 2)
        pg.draw.line(surface, (255, 0, 0), center, camera.project_point(self.position + 1.0 * self.beam_vector), 2)


class Antenna(Entity):
    def __init__(self, position: pg.Vector3) -> None:
        super().__init__(position)

    def draw(self, surface: pg.Surface, camera: Camera):
        center = camera.project_point(self.position)
        if self.origins:
            width = 0
            moving_head = list(self.origins)[0].moving_head
            color = moving_head.COLOR_MAP[moving_head.COLOR(moving_head._color_wheel)]  # TODO: implement color mixing
        else:
            width = 2
            color = (255, 255, 255)
        pg.draw.circle(surface, color, center, 12, width)


class Viewport(Widget):
    def __init__(self, name: str, parent: Widget):
        super().__init__(name, parent, parent.position.x + DEFAULT_GAP, parent.position.y + DEFAULT_GAP,
                         parent.surface.get_width() - 2 * DEFAULT_GAP, parent.surface.get_height() - 2 * DEFAULT_GAP)
        self.camera = Camera(zoom=128.0,
                             shift=pg.Vector2(self.surface.get_width() // 2, self.surface.get_height() // 2))
        self.entities = []

    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        rad_per_second = pi / 4
        if self.active:
            radians = rad_per_second * dt
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                self.camera.yaw += radians
            if keys[pg.K_RIGHT]:
                self.camera.yaw -= radians
            if keys[pg.K_UP]:
                self.camera.pitch -= radians
            if keys[pg.K_DOWN]:
                self.camera.pitch += radians
            if any((keys[pg.K_LEFT], keys[pg.K_RIGHT], keys[pg.K_UP], keys[pg.K_DOWN])):
                self.flag_as_needing_rerender()

    def render_origin(self):
        start = self.camera.project_point(pg.Vector3(0, 0, 0))
        end_x = self.camera.project_point(pg.Vector3(1, 0, 0))
        end_y = self.camera.project_point(pg.Vector3(0, 1, 0))
        end_z = self.camera.project_point(pg.Vector3(0, 0, 1))
        pg.draw.line(self.surface, (255, 0, 0), start, end_x)
        pg.draw.line(self.surface, (0, 255, 0), start, end_y)
        pg.draw.line(self.surface, (0, 0, 255), start, end_z)

    def draw_entities(self):
        for entity in self.entities:
            entity.draw(self.surface, self.camera)

    def render_body(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_origin()
        self.draw_entities()


class LaserGame(Widget):
    def __init__(self, name: str, parent: Desktop | None, x: int | None = None, y: int | None = None,
                 w: int | None = None, h: int | None = None):
        if x is None:
            x = parent.position.x
        if y is None:
            y = parent.position.y
        if w is None:
            w = parent.surface.get_width()
        if h is None:
            h = parent.surface.get_height()
        super().__init__(name, parent, x, y, w, h)
        self.max_speed = radians(45)
        self.viewport = Viewport(self.name + "Viewport", self)
        self.elements.append(self.viewport)
        from controlpanel import api
        self.moving_heads = [device for device in api.services.event_manager.devices.values() if
                             isinstance(device, dmx.HydroBeamX12)]
        self.relays = [
            Relay(moving_head=self.moving_heads[0], position=pg.Vector3(0, 0, 0), orientation=pg.Vector3(1, 0, 0))]
        self.antennas = [Antenna(pg.Vector3(0.473, 0.533, 0.700).normalize()), ]
        self.entities = self.relays + self.antennas
        self.viewport.entities = self.entities
        self.selected_relay = self.relays[0]
        self.selected_relay.selected = True

    def recalculate_connections(self):
        for relay in self.relays:
            relay.recalculate_connections(self.relays + self.antennas)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.JOYBUTTONDOWN:
            print(event.button)
        mods = pg.key.get_mods()
        if event.type == pg.JOYBUTTONDOWN and event.button == 0:
            self.selected_relay.moving_head.strobe = True
        elif event.type == pg.JOYBUTTONUP and event.button == 0:
            self.selected_relay.moving_head.strobe = False
        elif event.type == pg.JOYBUTTONDOWN and event.button == 2:
            self.selected_relay.moving_head.gobo1 += 1
        elif event.type == pg.JOYBUTTONDOWN and event.button == 3:
            self.selected_relay.moving_head.gobo2 += 1
        elif event.type == pg.JOYBUTTONDOWN and event.button == 1:
            self.selected_relay.moving_head.gobo1 = 0
            self.selected_relay.moving_head.gobo2 = 0

        if event.type == pg.KEYDOWN and event.key == pg.K_p:
            self.selected_relay.moving_head.prism = not self.selected_relay.moving_head.prism
        elif event.type == pg.KEYDOWN and event.key == pg.K_c:
            self.selected_relay.moving_head.color += 1
        elif event.type == pg.KEYDOWN and event.key == pg.K_g:
            if mods & pg.KMOD_CTRL:
                self.selected_relay.moving_head.gobo1 += 1
            else:
                self.selected_relay.moving_head.gobo1 -= 1
        elif event.type == pg.KEYDOWN and event.key == pg.K_h:
            if mods & pg.KMOD_CTRL:
                self.selected_relay.moving_head.gobo2 += 1
            else:
                self.selected_relay.moving_head.gobo2 -= 1
        return super().handle_event(event)

    def update(self, tick: int, dt: float, joysticks: dict[int: pg.joystick.JoystickType]):
        max_distance = self.max_speed * dt
        camera_distance = pi / 4 * dt

        for joystick in joysticks.values():
            axes: list[float] = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
            self.selected_relay.moving_head.yaw += axes[0] * abs(axes[0]) * max_distance
            self.selected_relay.moving_head.pitch -= axes[1] * abs(axes[1]) * max_distance
            self.selected_relay.moving_head.gobo2_rotation = axes[2]
            self.selected_relay.moving_head.focus = (axes[3] + 1) / 2
            hat = joystick.get_hat(0)
            self.viewport.camera.yaw += camera_distance * hat[0]
            self.viewport.camera.pitch -= camera_distance * hat[1]

        keys_pressed = pg.key.get_pressed()
        if keys_pressed[pg.K_a]:
            self.selected_relay.moving_head.set_phi(self.selected_relay.moving_head._phi + max_distance)
        if keys_pressed[pg.K_d]:
            self.selected_relay.moving_head.set_phi(self.selected_relay.moving_head._phi - max_distance)
        if keys_pressed[pg.K_w]:
            self.selected_relay.moving_head.set_theta(self.selected_relay.moving_head._theta - max_distance)
        if keys_pressed[pg.K_s]:
            self.selected_relay.moving_head.set_theta(self.selected_relay.moving_head._theta + max_distance)

        self.selected_relay.recalculate_beam_vector()
        self.recalculate_connections()
        self.viewport.flag_as_needing_rerender()

    def next_element(self):
        self.selected_relay.selected = False
        index = self.relays.index(self.selected_relay)
        index += 1
        if index < len(self.relays):
            self.selected_relay = self.relays[index]
            self.selected_relay.selected = True
        elif index >= len(self.relays):
            self.selected_relay = self.relays[0]
            self.selected_relay.selected = True
            super().next_element()
