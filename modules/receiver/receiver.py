################################################################################
#
# Copyright (c) 2017 Jean-Charles Fosse & Johann Bigler
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

import os, sys, json, struct, socket, dpkt

# ------- BANNER
BANNER =  r"""
 __       _________ __
/__`|\ |||__|__|__ |__)
.__/| \|||  |  |___|  \

"""
print("-----------------------------------------------------------------------")
print(BANNER)
print("-----------------------------------------------------------------------")

# ------- CONSTANTS
FOLDER_PATH = ".sniffee"
FOLDER_NAME = "receiver"
SOCKET_PROTOCOL = 0x0003
BYTE_READ = 2048

# ------- Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ------- Create a raw socket to listen to WiFi chip
rawSocket  = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                           socket.htons(SOCKET_PROTOCOL))

# ------- Settings
def get_setting(setting):
    """
    Get setting from config.json file.
    """
    path = os.path.join(os.path.expanduser("~"), FOLDER_PATH,
                        FOLDER_NAME, 'config.json')
    with open(path) as data_file:
        data = json.load(data_file)

        if setting in data:
            return data[setting]
        else:
            raise Exception("ERROR: Setting {0} not in config file"
                            .format(setting))

# ------- Get Device id/Address
device_id = get_setting("device_id")

# ------- Bind to socket define in setting interface
interface = get_setting("interface")
rawSocket.bind((interface, SOCKET_PROTOCOL))
print("INFO: Bind to raw socket {0}".format(interface))

# ------- UDP server address to use
address = get_setting("udp_ip")
port = get_setting("udp_port")
server_address = (address, port)
print("INFO: UPD socket on ip {0}, port {1}".format(address, port))

print("INFO: --------- Start Sniffer -----------")
try:
    while True:
        data = rawSocket.recvfrom(BYTE_READ)[0]
        t_len = struct.unpack("B", data[2:3])[0]
        wlan = None
        try:
            wlan = dpkt.ieee80211.IEEE80211(data[t_len:])
        except Exception as err:
            pass

        if wlan and wlan.type == 0 and wlan.subtype == 4:
            ssid = wlan.ies[0].info
            if not ssid:
                mac = ":".join([format(x, '02x')
                                for x in struct.unpack("BBBBBB",
                                                       wlan.mgmt.src)])
                if not "da:a1:19" in mac:
                    # print("DEBUG: ssid {0}, mac {1}".format(ssid, mac))
                    payload = '{"id": "%s", "mac":"%s"}'%(device_id, mac)
                    udp_socket.sendto(payload, server_address)

except KeyboardInterrupt:
    print("")
    print("INFO: Sniffer stopped on Ctrl-C")

print("INFO: ------------ End Sniffer ----------")

rawSocket.close()
print("INFO: Socket closed")
