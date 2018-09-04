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

import os, sys, json, time, treq

from twisted.internet import reactor, task
from twisted.internet.protocol import DatagramProtocol
from twisted.internet.defer import inlineCallbacks, returnValue

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
FOLDER_NAME = "sender"
CMD_COUNT = "count"
MAC = "mac"
POWER = "power"

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

class UDP(DatagramProtocol):

    def __init__(self):
        self.device_id = get_setting("device_id")
        self.send_all = get_setting("send_all")
        self.udp_port = get_setting("udp_port")
        self.period = get_setting("period")
        self.expiration = get_setting("expiration")
        self.interface = get_setting("interface")
        self.post_url = get_setting("post_url")

        # Mac addresses map per device.
        # It includes time at which it was added.
        # All addresses older than XXmin (see config.json) are removed
        self.mac_addresses_device = []

        # Next payload to send
        self.payload = []

        # Number of device
        self.nb_devices = 0

        # Watchdog cheking for mac address validity
        # self.watchDog = task.LoopingCall(self.checkExpiredMac)
        self.watchDog = task.LoopingCall(self.sendMacAddresses)

    def start(self, reactor):
        print("INFO: Start Sender")

        reactor.listenUDP(self.udp_port, self, self.interface)

        # Start watch dog removing old mac addresses
        self.watchDog.start(self.period).addErrback(self.error)

    def datagramReceived(self, data, address):
        try:
            msg = json.loads(data)
        except Exception as err:
            print("ERROR: Invalid json {0}".format(err))
        else:
            # print("DEBUG: Received mac address {0} from device {1}"
            #       .format(msg["mac"], msg["id"]))
            mac = msg["mac"]
            if not mac in self.mac_addresses_device:
                # print("DEBUG: Adding mac address {0}".format(mac))
                self.nb_devices += 1
                self.mac_addresses_device.append(mac)

            # self.payload.append({"id": MAC, "data": mac, "timestamp": msg["timestamp"]})
            # self.payload.append({"id": POWER, "data": msg["power"], "timestamp": msg["timestamp"]})
            self.payload.append({"id": MAC, "data": {"mac": mac, "power": msg["power"]}, "timestamp": msg["timestamp"]})

    # ------------------- Sniffer Related Functions ----------------------------

    def error(self, error):
        print("ERROR: Error in task looping call", error)
        if self.watchDog.running:
            self.watchDog.stop()

        self.watchDog.start(self.period, now=False).addErrback(self.error)

    def sendMacAddresses(self):
        self.payload, payload = [], self.payload
        self.nb_devices, nb_devices = 0, self.nb_devices
        self.mac_addresses_device = []

        if self.send_all:
            payload.append({ "id": CMD_COUNT, "data": nb_devices })
        else:
            payload = [{ "id": CMD_COUNT, "data": nb_devices }]

        message = {
            "dev_id": self.device_id,
            "cmd_keys": payload
        }

        message = json.dumps(message).encode('ascii')
        # print("DEBUG: Payload length {0}".format(len(message)), message)
        d = treq.post(self.post_url, message,
                      headers={b'Content-Type': [b'application/json']})
        d.addCallback(self.response)

    @inlineCallbacks
    def response(self, _response):
        # print("**** Received Response ********", _response)
        if _response.code == 200:
            # print("DEBUG: Message sent")
            pass
        else:
            content = yield _response.content()
            print("ERROR: {0}".format(content))

if __name__ == '__main__':
    print("INFO: Starting Reactor")
    udp = UDP()
    udp.start(reactor)
    reactor.run()
    print("INFO: Reactor closed. Shutting down")

print("")
print("-------------------------------------------------------------------")
