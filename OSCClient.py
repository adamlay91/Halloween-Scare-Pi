from pythonosc.udp_client import SimpleUDPClient

grandMAIP = "192.168.1.5"
oscPort = 64300
oscClient = SimpleUDPClient(grandMAIP, oscPort)

oscClient.send_message("/gma3/cmd", "Toggle Exec 111")
oscClient.send_message("/gma3/cmd", "Toggle Exec 203")