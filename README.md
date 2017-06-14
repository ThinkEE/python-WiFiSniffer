# Python WiFi Sniffer
-----------------------

A small python script to use a wifi chip in monitor mode to send packets received through UDP

## Introduction

Working on RPI3 with Raspbian Lite Install

Code used to sniff the packet around the RPI. It catches the mac addresses and send them using UDP.

`Needs to be install as root user`

## Configuration

See `config.json` file in configuration folder

* Interface to listen for incoming packet  `"interface": "wlan0"`
* UDP address to send to `"udp_ip": "localhost"`
* UDP port to send to `"udp_port": 9010`

## Installation

Needs to be install as root user
* `sudo su`

### Environment Installation

* The WiFi chip driver need to be changed so you can enable monitor mode.

* We are using [Nexmon](https://github.com/seemoo-lab/nexmon). See github repo for setup information

* For Pi Zero Change files according to this [pull request](https://github.com/seemoo-lab/nexmon/pull/55)
* Build patches for bcm43438 on the RPI3/Zero W using Raspbian 8 (recommended). Duplicate from [Nexmon github repo](https://github.com/seemoo-lab/nexmon)
  * Log as root `sudo su`
  * `apt-get update && apt-get upgrade`
  * Install the kernel headers to build the driver and some dependencies: `apt install raspberrypi-kernel-headers git libgmp3-dev gawk qpdf flex bison`
  * Clone `git clone https://github.com/seemoo-lab/nexmon.git`
  * `cd nexmon`
    * Setup the build environment: `source setup_env.sh`
    * Compile some build tools and extract the ucode and flashpatches from the original firmware files: `make`
  * `cd patches/bcm43438/7_45_41_26/nexmon/`
    * Compile a patched firmware: `make`
    * Generate a backup of your original firmware file: `make backup-firmware`
    * Install the patched firmware on your RPI3: `make install-firmware`
  * `cd utilities/nexutil/`
    * Compile and install nexutil: `make && make install`
  * Optional: remove wpa_supplicant for better control over the WiFi interface: `apt-get remove wpasupplicant`

  * Activate monitor mode `nexutil -m2`
  * Check `iwconfig`

### Patch for new version

* Change Makefile according to pull [request](https://github.com/seemoo-lab/nexmon/pull/55/files)
* Change `4.4.9-v7l+` by `4.9.24+` in Makefile

I used the [branch brcmfmac_kernel410](https://github.com/seemoo-lab/nexmon/tree/brcmfmac_kernel410) according to the instruction of issue [#85](https://github.com/seemoo-lab/nexmon/issues/85) then I had to change `4.4.9-v7l+` by `4.9.24+` in file `patches/bcm43438/7_45_41_26/nexmon/Makefile`. Finally, I followed the steps described in [#55]((https://github.com/seemoo-lab/nexmon/pull/55/files)) . The only difference is in file `utilities/libnexio/Makefile` line 5 instead of `ifeq ($(shell uname -m), $(filter $(shell uname -m), armv7l armv6l))` I had to put `ifneq ($(shell uname -m), $(filter $(shell uname -m), armv7l armv6l))` or it will try to compile for an android target.

### Modules Installation

* Create Virtualenv (Instruction for Raspbian)
  * `virtualenv WiFiSniffer`
  * `cd WiFiSniffer`
  * `source bin/activate`

* Clone [WiFiSniffer](https://github.com/ThinkEE/python-WiFiSniffer) in newly created virtualenv

### Packages Dependencies

* Install dependencies `pip install -r requierements.txt`

* Install [dpkt](https://github.com/kbandla/dpkt) `pip install dpkt`

### Initialization

* Works for Raspbian System
  * Create `.deembox` in root folder `sudo mkdir /root/.lyla/`
  * Create `sniffer` in root `sudo mkdir /root/.lyla/wifisniffer/`
  * Create `config.json` in root `sudo nano /root/.lyla/wifisniffer/config.json`

## Run

* Activate WiFi monitor mode (Needs to be done after each restart)
  * Log as root `sudo su`
  * Go to home directory `cd`
  * Activate driver
    * `cd nexmon/patches/bcm43438/7_45_41_26/nexmon/`
    * `rmmod brcmfmac`
    * `insmod brcmfmac/brcmfmac.ko`
    * `nexutil`
    * `nexutil -m2`
  * Check config `iwconfig`

### Systemd Automatic Startup and Restart

* Create a systemd service file (see `wifisniffer.service` file in examples)
  * `sudo nano /etc/systemd/system/wifisniffer.service`

* Add lylaMain service to systemd
  * `sudo systemctl daemon-reload`

* Start automatically at boot
  * `sudo systemctl enable wifisniffer.service`

* To control the systemct
  * `sudo systemctl start wifisniffer`
  * `sudo systemctl stop wifisniffer`
  * `sudo systemctl restart wifisniffer`
  * `sudo systemctl status wifisniffer -l`
  * `sudo journalctl -u wifisniffer`

### Console

* Go to virtualenv folder (`WiFiSniffer`)
* Activate Virtualenv `source bin/activate`
* Go to WiFiSniffer `cd python-WiFiSniffer`
* Execute command `python run.py`
