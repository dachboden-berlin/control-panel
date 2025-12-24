import webrepl
import utils

# Attempt to establish a network connection: LAN > WLAN (STA) > WLAN (AP)
utils.INTERFACE = utils.establish_connection()

webrepl.start()
print(f"MAC address is {utils.get_mac_address()}")
