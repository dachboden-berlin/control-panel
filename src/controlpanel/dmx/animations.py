def red_strobe(t: float) -> tuple[int, ...]:
    # return (255, 255, 0, 0) if t % 2 < 1 else (0, 0, 0, 0)
    return (255, 0, 64, 0) if t % 2 < 1 else (0, 0, 0, 0)  # pink
    # return (255, 64, 128, 0) if t % 2 < 1 else (0, 0, 0, 0)


def starbar_strobe1(t: float) -> tuple[int, ...]:
    return (255, 0, 0, 255) if (t*2) % 2 < 1 else (255, 0, 0, 0)


def starbar_strobe2(t: float) -> tuple[int, ...]:
    return (255, 0, 0, 0) if (t*2) % 2 < 1 else (255, 0, 0, 255)
