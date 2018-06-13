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

import os, sys, json, struct, socket, dpkt, random
import multiprocessing, Queue, pcapy, datetime, time

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
CHANNELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13] # 2.4GHz only

SUBTYPES_MANAGEMENT = {
    0: 'association-request',
    1: 'association-response',
    2: 'reassociation-request',
    3: 'reassociation-response',
    4: 'probe-request',
    5: 'probe-response',
    8: 'beacon',
    9: 'announcement-traffic-indication-message',
    10: 'disassociation',
    11: 'authentication',
    12: 'deauthentication',
    13: 'action'
}

SUBTYPES_CONTROL = {
    8: 'block-acknowledgement-request',
    9: 'block-acknowledgement',
    10: 'power-save-poll',
    11: 'request-to-send',
    12: 'clear-to-send',
    13: 'acknowledgement',
    14: 'contention-free-end',
    15: 'contention-free-end-plus-acknowledgement'
}

SUBTYPES_DATA = {
    0: 'data',
    1: 'data-and-contention-free-acknowledgement',
    2: 'data-and-contention-free-poll',
    3: 'data-and-contention-free-acknowledgement-plus-poll',
    4: 'null',
    5: 'contention-free-acknowledgement',
    6: 'contention-free-poll',
    7: 'contention-free-acknowledgement-plus-poll',
    8: 'qos-data',
    9: 'qos-data-plus-contention-free-acknowledgement',
    10: 'qos-data-plus-contention-free-poll',
    11: 'qos-data-plus-contention-free-acknowledgement-plus-poll',
    12: 'qos-null',
    14: 'qos-contention-free-poll-empty'
}

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

# ------- Manage Channels
def rotate(stop):
    while not stop.is_set():
        try:
            channel = str(random.choice(CHANNELS))
            # print("DEBUG: Changing to channel {0}".format(channel))
            os.system("iw dev {0} set channel {1}".format(interface, channel))
            time.sleep(1) # seconds
        except Exception as err:
            print("ERROR: Rotating channel failed", err)

stop_rotating = multiprocessing.Event()
multiprocessing.Process(target=rotate, args=[stop_rotating]).start()

# ------- Decode a MAC or BSSID address
def to_address(address):
    return ':'.join('%02x' % ord(b) for b in address)

# ------- Start Sniffing
print("INFO: --------- Start Sniffer -----------")
max_packet_size = 256 # bytes
promiscuous = 0 # boolean masquerading as an int
timeout = 100 # milliseconds

try:
    packets = pcapy.open_live(interface, max_packet_size, promiscuous, timeout)
    packets.setfilter('') # bpf syntax (empty string = everything)
    def loop(header, data):
        timestamp = datetime.datetime.now().isoformat()
        try:
            packet = dpkt.radiotap.Radiotap(data)
            packet_signal = -(256 - packet.ant_sig.db) # dBm
            frame = packet.data
            if frame.type == dpkt.ieee80211.MGMT_TYPE:
                mac = to_address(frame.mgmt.src)
                # print("DEBUG: Sending mac {0}, type: dpkt.ieee80211.MGMT_TYPE".format(mac))
                payload = '{"id": "%s", "mac":"%s"}'%(device_id, mac)
                udp_socket.sendto(payload, server_address)
            elif frame.type == dpkt.ieee80211.DATA_TYPE:
                mac = to_address(frame.data_frame.src)
                # print("DEBUG: Sending mac {0}, type: dpkt.ieee80211.MGMT_TYPE".format(mac))
                payload = '{"id": "%s", "mac":"%s"}'%(device_id, mac)
                udp_socket.sendto(payload, server_address)
        except Exception as err:
            print("ERROR: Packet invalid", err)
    packets.loop(-1, loop)

except KeyboardInterrupt:
    print("")
    print("INFO: Sniffer stopped on Ctrl-C")

stop_rotating.set() # Stop changing channels

print("INFO: ------------ End Sniffer ----------")

rawSocket.close() # Close listening socket
print("INFO: Socket closed")
print("")
print("-------------------------------------------------------------------")
