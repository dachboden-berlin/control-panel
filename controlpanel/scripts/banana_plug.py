import random

from controlpanel import api

PLUGS = ["A", "B", "C", "D"]
SOCKETS = [1, 2, 3, 4, 5, 6]

# e.g.: {"A": 2, "C": 5}
required_solution = {}
puzzle_solved = False


def generate_new_puzzle(num_plugs_required=3):
    global required_solution, puzzle_solved
    puzzle_solved = False

    selected_plugs = random.sample(PLUGS, num_plugs_required)
    selected_sockets = random.sample(SOCKETS, num_plugs_required)

    required_solution = dict(zip(selected_plugs, selected_sockets))

    print(f"New Puzzle Generated! Connect: {required_solution}")


def check_banana_puzzle():
    global puzzle_solved
    if puzzle_solved:
        return True

    device = api.get_device("BananaPlugs")
    current_connections = device.connections

    # tranlate
    # plug_pins: [33, 2, 32, 4] -> 0=A, 1=B, 2=C, 3=D
    # socket_pins: [15, 13, 12, 14, 27, 26] -> 0=1, 1=2, etc.

    for plug_label, req_socket_label in required_solution.items():
        plug_idx = PLUGS.index(plug_label)
        socket_idx = SOCKETS.index(req_socket_label)

        # TODO: How do I see, that plug is connected? - ButtonPressed?!
        if current_connections.get(plug_idx) != socket_idx:
            return False

    puzzle_solved = True
    on_puzzle_complete()
    return True


# kein callback, weil loop mir zuverlässiger erscheint und performance egal ist
def on_puzzle_complete():
    print("Puzzle Solved! Activating UV Strobe.")
    # Example feedback: Flash the UV Strobe
    api.get_device("UVStrobe").duty = 1.0

    return
    # leds = api.get_device("PilzLEDs")
    # for i in range(5):
    #     leds.set_pixel(i, (0, 255, 0))
    # leds.show()


@api.call_with_frequency(1)
def loop():
    check_banana_puzzle()
