from controlpanel import api


@api.callback(source="PowerSwitch", action="ButtonPressed")
def power_off(event=None):
    print("PowerSwitch pressed: Initiating Blackout...")
    for fixture in api.Services.event_manager._fixture_dict.values():
        try:
            fixture.blackout()
        except AttributeError:
            pass


@api.callback(source="PowerSwitch", action="ButtonReleased")
def power_on(event=None):
    print("PowerSwitch released: Restoring systems...")
    for fixture in api.Services.event_manager._fixture_dict.values():
        try:
            fixture.whiteout()
        except AttributeError:
            pass
