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
        self.udp_port = get_setting("udp_port")
        self.period = get_setting("period")
        self.expiration = get_setting("expiration")
        self.interface = get_setting("interface")
        self.post_url = get_setting("post_url")

        # Mac addresses map per device.
        # It includes time at which it was added.
        # All addresses older than XXmin (see config.json) are removed
        self.mac_addresses_device = {}

        # Number of device
        self.nb_devices = 0

        # Watchdog cheking for mac address validity
        self.watchDog = task.LoopingCall(self.checkExpiredMac)

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
            self.new_mac_address(msg["id"], msg["mac"])

    # ------------------- Sniffer Related Functions ----------------------------

    def error(self, error):
        print("ERROR: Error in task looping call", error)
        if self.watchDog.running:
            self.watchDog.stop()

        self.watchDog.start(self.period, now=False).addErrback(self.error)

    def new_mac_address(self, device_id, mac):
        _time = int(time.time())

        if not device_id in self.mac_addresses_device:
            self.mac_addresses_device[device_id] = {}

        if not mac in self.mac_addresses_device[device_id]:
            # print("DEBUG: Adding mac address {0}".format(mac))
            self.mac_addresses_device[device_id][mac] = _time
            self.nb_devices += 1

        else: # Update last update
            self.mac_addresses_device[device_id][mac] = _time

    def remove_mac_address(self, device_id, mac):
        del self.mac_addresses_device[device_id][mac]
        self.nb_devices -= 1

    def checkExpiredMac(self):
        # print("DEBUG: Start checking expired Mac Address")

        _time = int(time.time())
        expiration = _time - self.expiration
        for device_id, mac_addresses in self.mac_addresses_device.items():
            for mac, _time in mac_addresses.items():
                if _time < expiration:
                    # print("DEBUG: Removing mac address {0}".format(mac))
                    self.remove_mac_address(device_id, mac)

            self.sendData(device_id, CMD_COUNT, self.nb_devices)

        # print("DEBUG: Check done")

    def sendData(self, device_id, cmd, data):
        @inlineCallbacks
        def response(_response):
            # print("**** Received Response ********", _response)
            if _response.code == 200:
                # print("DEBUG: Message sent")
                pass
            else:
                content = yield _response.content()
                print("ERROR: {0}".format(content))

        # print("DEBUG: Send to device: {0}, cmd: {1}, data: {2}"
        #       .format(device_id, cmd, data))

        payload = {
            "dev_id": device_id,
            "cmd_keys": [
                { "id": cmd, "data": data }
            ]
        }
        d = treq.post(self.post_url,
                      json.dumps(payload).encode('ascii'),
                      headers={b'Content-Type': [b'application/json']})
        d.addCallback(response)

if __name__ == '__main__':
    print("INFO: Starting Reactor")
    udp = UDP()
    udp.start(reactor)
    reactor.run()
    print("INFO: Reactor closed. Shutting down")

print("")
print("-------------------------------------------------------------------")
