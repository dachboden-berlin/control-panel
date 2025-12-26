from keyboard import WIDTH, HEIGHT, button_pos, led_idx
from controlpanel import api
from enum import Enum, auto


class CellState(Enum):
    ALIVE = auto()
    DEAD = auto()


BOARD = [[CellState.DEAD for _ in range(HEIGHT)] for _ in range(WIDTH)]
COLORS = {
    CellState.ALIVE: (50, 50, 80),
    CellState.DEAD: (0, 0, 0),
}


@api.callback(source="MainframeKeys", action="ButtonsChanged")
def toggle_cells(event):
    for button_id, pressed in event.value:
        if pressed:
            x, y = button_pos(button_id)
            BOARD[x][y] = CellState.ALIVE if BOARD[x][y] is CellState.DEAD else CellState.DEAD


def count_alive_neighbors(x: int, y: int) -> int:
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            if BOARD[(x + dx) % WIDTH][(y + dy) % HEIGHT] is CellState.ALIVE:
                count += 1
    return count


@api.callback(source="DialReset")
def reset():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            BOARD[x][y] = CellState.DEAD


def render_board():
    leds = [(0, 0, 0) for _ in range(WIDTH * HEIGHT)]
    for x in range(WIDTH):
        for y in range(HEIGHT):
            leds[led_idx(x, y)] = COLORS.get(BOARD[x][y])

    api.get_device("MainframeLEDs").set_pixels(leds)


@api.call_with_frequency(10)
def conway():
    new_board = [[BOARD[x][y] for y in range(HEIGHT)] for x in range(WIDTH)]

    for x in range(WIDTH):
        for y in range(HEIGHT):
            cell = BOARD[x][y]
            n = count_alive_neighbors(x, y)
            if cell is CellState.ALIVE and (n < 2 or n > 3):
                new_board[x][y] = CellState.DEAD
            elif cell is CellState.DEAD and n == 3:
                new_board[x][y] = CellState.ALIVE

    for x in range(WIDTH):
        for y in range(HEIGHT):
            BOARD[x][y] = new_board[x][y]

    render_board()
