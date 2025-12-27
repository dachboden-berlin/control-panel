from controlpanel import api

ip_mapping: dict[str, str] = {
    "reaktor": "151.219.202.216",
    "telegraph": "151.219.195.106",
    "mainframe": "151.219.192.175",  # '08:D1:F9:E0:D8:E8'
    "waehlscheibe": "151.219.204.205", #  '08:D1:F9:E1:F6:94'
    "kommunikation": "151.219.193.189",  #'08:D1:F9:E1:0F:FC'
    "pilz": "151.219.205.112", # 'CC:DB:A7:6A:13:FC'
    "kuehlwasser": "151.219.217.50", # 'A0:DD:6C:0E:6F:B4'
    "fourteensegment": "151.219.222.191", # '08:D1:F9:E0:03:80'
    "ladestation": "151.219.205.10", #
    "chronometer": "151.219.201.103", #'0C:B8:15:75:A4:98'
}

for node in api.services.event_manager._nodes:
    for name, ip in ip_mapping.items():
        if node.name == name:
            node.ip = ip
    api.services.artnet.send_poll(ip_override=node.ip)
