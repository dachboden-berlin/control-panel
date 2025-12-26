MODS_PER_ROW = 5
MODS_PER_COLUMN = 3
MOD_SIZE = 4
WIDTH = MODS_PER_ROW * MOD_SIZE
HEIGHT = MODS_PER_COLUMN * MOD_SIZE
TOTAL_KEYS = MODS_PER_COLUMN * MODS_PER_ROW * MOD_SIZE * MOD_SIZE


def button_pos(idx: int):
    rel = idx % 16
    rel_x = rel % 4
    rel_y = (rel // 4 + 2) % 4

    pcb = idx // 16
    pcb_x = pcb % MODS_PER_ROW
    pcb_y = pcb // MODS_PER_ROW

    return rel_x + pcb_x * 4, rel_y + pcb_y * 4


def button_idx(x: int, y: int):
    rel_x = x % 4
    rel_y = (y % 4 - 2) % 4

    pcb_x = x // 4
    pcb_y = y // 4
    pcb = pcb_y * MODS_PER_ROW + pcb_x

    return pcb * 16 + rel_y * 4 + rel_x


def led_idx(x: int, y: int):
    pcb_x = x // 4
    pcb_y = y // 4
    rel_x = x % 4
    rel_y = y % 4
    rel_a = rel_y * 4 + rel_x
    a = rel_a + 16 * pcb_y * MODS_PER_ROW + pcb_x * 16
    return a
