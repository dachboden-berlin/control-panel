import sys
from threading import Thread
from artnet import ArtNet
from controlpanel.game_manager import GameManager
from controlpanel.dmx import DMXUniverse, DMXDevice
from controlpanel import api
import argparse
from controlpanel.server import app
import uvicorn


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description='Control Panel')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--no-gui', action='store_true',
                       help='Disable the GUI (enabled by default)')
    group.add_argument('-f', '--fullscreen', action='store_true',
                       help='Run in fullscreen mode (windowed is default)')
    parser.add_argument('--height', type=int, default=540,
                        help='Height of the game window')
    parser.add_argument('--width', type=int, default=960,
                        help='Width of the game window')
    parser.add_argument('--shaders', action='store_true',
                        help='Enable shaders (shaders are disabled by default)')
    group.add_argument('--stretch-to-fit', action='store_true',
                       help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--pythonpath', nargs='*', default=[],
                        help='Directories to add to PYTHONPATH (to import scripts (modules/packages) from')
    parser.add_argument('--load-scripts', nargs='*', default=[],
                        help='Load script files (in controlpanel/scripts), all by default. '
                             'Alternatively, supply the filenames of the script files (or presets) to load.'
                             'A preset is a .txt file containing newline-separated script file names')
    parser.add_argument('--cheats', '-c', action='store_true', default=False,
                        help='Enable cheat-protected console commands (disabled by default)')
    parser.add_argument('--start-server', action='store_true',
                        help='Start the script upload server (disabled by default)')
    parser.add_argument('--unrestricted', action='store_true',
                        help='Run all scripts in unrestricted mode')
    parser.add_argument('--log-level', type=str, default='INFO',
                        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO')
    return parser.parse_known_args()



def main():
    args, unknown_args = parse_args()
    
    # Set log level immediately
    api.logger.set_log_level(args.log_level)

    artnet = ArtNet()  # This is where we initialise our one and ONLY ArtNet instance for the entire program.
    api.services.artnet = artnet

    event_manager = api.EventManager(artnet)
    api.services.event_manager = event_manager
    # needs to be called after services.event_manager has been set
    event_manager.instantiate_devices([api.dummy,])

    game_manager = GameManager(resolution=(args.width, args.height) if not args.no_gui else None,
                               dev_args=unknown_args,
                               is_fullscreen=args.fullscreen,
                               use_shaders=args.shaders,
                               stretch_to_fit=args.stretch_to_fit,
                               enable_cheats=args.cheats,
                               )
    api.services.game_manager = game_manager

    try:
        api.services.dmx = DMXUniverse(None, devices=[device for device in event_manager.devices.values() if isinstance(device, DMXDevice)], target_frequency=10)
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')  # occurred on macOS
        print(err)

    for path in args.pythonpath:
        sys.path.append(path)

    api.load_scripts(args.load_scripts, force_unrestricted = args.unrestricted)

    if args.start_server:
        server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8000, log_config=None))
        Thread(target=server.run, daemon=True).start()

    game_manager_thread = Thread(target=game_manager.run, daemon=False)
    game_manager_thread.run()


if __name__ == "__main__":
    main()