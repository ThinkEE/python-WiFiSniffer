# Python WiFi Sniffer
-----------------------

A small python script to use a wifi chip in monitor mode to send packets received through UDP

## Introduction

Working on RPI3 with Raspbian Lite Install

Code used to sniff the packet around the RPI. It catches the mac addresses and send them using UDP.

## Configuration

See `config.json` file in configuration folder

* Interface to listen for incoming packet  `"interface": "wlan0"`
* UDP address to send to `"udp_ip": "localhost"`
* UDP port to send to `"udp_port": 9010`

## Installation

Needs to be install as root user
* `sudo su`

### RPI Installation

* Flash image on RPI
* Boot RPI
* Plug SD card to computer
* Configure [OTG](http://www.circuitbasics.com/raspberry-pi-zero-ethernet-gadget/)
  * Add `modules-load=dwc2,g_ether` at end of file `cmdline.txt`
  * Add `dtoverlay=dwc2` in file `config.txt`
* Create file `ssh` on SD card

* Boot RPI
* Connect as SSH `ssh pi@raspberrypi.local`
  * User: `pi`
  * Password: `raspberry`
* Share Internet connection
  * On Ubuntu :
    * Unplug RPI
    * Open the `edit connexions` settings (top-right bar)
    * Select the `wired connection X` corresponding to the RPI and go to IPv4 tab
    * Set method to `Link-local Only`
    * Plug RPI

### Environment Installation

`Needs to be install as root user`

* The WiFi chip driver need to be changed so you can enable monitor mode.
* We are using [Nexmon](https://github.com/seemoo-lab/nexmon). See github repo for setup information
* Build patches for bcm43430a1 on the RPI3/Zero W or bcm434355c0 on the RPI3+ using Raspbian (recommended). Duplicate from [Nexmon github repo](https://github.com/seemoo-lab/nexmon)
  * Log as root `sudo su`
  * `apt-get update && apt-get upgrade`
  * Install the kernel headers to build the driver and some dependencies: `apt install raspberrypi-kernel-headers git libgmp3-dev gawk qpdf bison flex make`
  * Clone `git clone https://github.com/seemoo-lab/nexmon.git`
  * `cd nexmon`
  * Check if `ls /usr/lib/arm-linux-gnueabihf/libisl.so.10` exists, if not, compile it from source:
    * `cd buildtools/isl-0.10`
    * `./configure`
    * `make`
    * `make install`
    * `ln -s /usr/local/lib/libisl.so /usr/lib/arm-linux-gnueabihf/libisl.so.10`
    * `cd ../..`
  * Then you can setup the build environment for compiling firmware patches
    * Setup the build environment: `source setup_env.sh`
    * Compile some build tools and extract the ucode and flashpatches from the original firmware files: `make`
  * Go to the patches folder for the `bcm43430a1/bcm43455c0` chipset: `cd patches/bcm43430a1/7_45_41_46/nexmon/`
    * Compile a patched firmware: `make`
    * Generate a backup of your original firmware file: `make backup-firmware`
    * Install the patched firmware on your RPI3: `make install-firmware`
    * `cd ../../../..`
  * Install nexutil from the root directory of our repository
    * Switch to the nexutil folder: `cd utilities/nexutil/`
    * Compile and install nexutil: `make && make install`
  * Remove wpa_supplicant for better control over the WiFi interface: `apt-get remove wpasupplicant`
  * Execute: `iw phy `iw dev wlan0 info | gawk '/wiphy/ {printf "phy" $2}'` interface add mon0 type monitor`
  * Set the interface up: `ifconfig mon0 up`
  * Check `iwconfig`
  * To make the RPI3 load the modified driver after reboot:
    * Find the path of the default driver at reboot: `modinfo brcmfmac` #the first line should be the full path
    * Backup the original driver: `mv "<PATH TO THE DRIVER>" "<PATH TO THE DRIVER>.orig"`
    * Copy the modified driver (Kernel 4.14): `cp /home/pi/nexmon/patches/bcm43430a1/7_45_41_46/nexmon/brcmfmac_4.14.y-nexmon/brcmfmac.ko "<PATH TO THE DRIVER>/"`
    * Probe all modules and generate new dependency: `depmod -a`
    * `cd ../../..`
  * Start interface at Start
    * Open file `nano /etc/rc.local`
    * Add following lines
    ```
    echo "Creating Interface mon0"
    iw phy `iw dev wlan0 info | gawk '/wiphy/ {printf "phy" $2}'` interface add mon0 type monitor
    ifconfig mon0 up
    ifconfig wlan0 down
    ifconfig gprs up
    echo "Interface mon0 created"
    ```
  * Reboot `reboot`

### Module Installation

* Install packages `apt-get install build-essential python-dev libssl-dev libffi-dev python-virtualenv libpcap-dev`
* Create Virtualenv (Instruction for Raspbian)
  * `virtualenv Sniffee`
  * `cd Sniffee`
  * `source bin/activate`
* Clone [WiFiSniffer](https://github.com/ThinkEE/python-WiFiSniffer) in newly created virtualenv
  * `git clone -b master https://github.com/ThinkEE/python-WiFiSniffer.git sniffee`
* Install dependencies `pip install -r requirements.txt`

### Initialisation

* Works for Raspbian System
  * Create `.sniffee` in root folder `mkdir /root/.sniffee/`
  * Create `receiver` in root `mkdir /root/.sniffee/receiver/`
  * Create `config.json` in root `nano /root/.sniffee/receiver/config.json`
  * Create `sender` in root `mkdir /root/.sniffee/sender/`
  * Create `config.json` in root `nano /root/.sniffee/sender/config.json`  

### Systemd Automatic Startup and Restart
#### Receiver service

* Create a systemd service file (see `receiver.service` file in examples)
  * `nano /etc/systemd/system/receiver.service`
* Add service to systemd
  * `systemctl daemon-reload`
* Start automatically at boot
  * `systemctl enable receiver.service`
* To control the systemct
  * `systemctl start receiver`
  * `systemctl stop receiver`
  * `systemctl restart receiver`
  * `systemctl status receiver -l`
  * `journalctl -u receiver`

#### Sender service

* Create a systemd service file (see `sender.service` file in examples)
  * `nano /etc/systemd/system/sender.service`
* Add service to systemd
  * `systemctl daemon-reload`
* Start automatically at boot
  * `systemctl enable sender.service`
* To control the systemct
  * `systemctl start sender`
  * `systemctl stop sender`
  * `systemctl restart sender`
  * `systemctl status sender -l`
  * `journalctl -u sender`

### GSM Installation

* Install packages `apt-get install ppp usb-modeswitch usb-modeswitch-data`
* Get TargetVendor and product information `lsusb`
* Run command to check if it can be switch to modem `usb_modeswitch -v 12d1 -p 15d2 -M '5553424312345678000000000000001106200000010000000000000000000'`
* Check if it switched `lsusb`
* Check if modem ready `dmesg|grep USB`
* Open file `nano /etc/usb_modeswitch.d/12d1:15d2`
* Add following lines
```
# Huawei E353 (3.se)

TargetVendor=  0x12d1
TargetProduct= 0x15d2

MessageContent="55534243123456780000000000000011062000000100000000000000000000"
NoDriverLoading=1
```
* Create script `nano switchModem`
```
#!/bin/bash

echo "Switching modem"
echo $1
echo $2
CONFIG=/etc/usb_modeswitch.d/$1\:$2

sleep 15

usb_modeswitch -D -c $CONFIG

echo "Done Swicthing"
```
* Activate script `chmod +x switchModem`
* Create rule `nano /etc/udev/rules.d/41-usb_modeswitch.rules`
`ATTRS{idVendor}=="12d1", ATTR{bInterfaceNumber}=="00", ATTR{bInterfaceClass}=="08", RUN+="/home/pi/switchModem %s{idVendor} %s{idProduct}"`
* Open file `nano /etc/network/interfaces`
* Add following lines
```
auto gprs
iface gprs inet ppp
provider gprs
```
* Create file `nano /etc/ppp/peers/gprs`
```
user "swisscom"
connect "/usr/sbin/chat -v -f /etc/chatscripts/gprs -T gprs.swisscom.ch"
/dev/ttyUSB0
noipdefault
defaultroute
replacedefaultroute
hide-password
noauth
persist
usepeerdns
```
* Reboot `reboot`

### Console

* Go to virtualenv folder (`Sniffee`)
* Activate Virtualenv `source bin/activate`
