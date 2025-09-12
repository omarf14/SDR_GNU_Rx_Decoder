# Copyright (c) 2016 Jeppe Ledet-Pedersen <jlp@satlab.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

import sys
import platform
import errno
import time
import struct
import subprocess
import usb


class Bluebox(object):
    # USB VID/PID
    VENDOR = 0x1d50
    PRODUCT = 0x6054

    # Atmel bootloader VID/PID
    ATMEL_VENDOR = 0x03eb
    ATMEL_PRODUCT = 0x2ff4

    # MCU type
    MCU = "atmega32u2"

    # Data Endpoints
    DATA_IN = (usb.util.ENDPOINT_IN | 1)
    DATA_OUT = (usb.util.ENDPOINT_OUT | 2)

    # RF Control
    REQUEST_REGISTER = 0x01
    REQUEST_FREQUENCY = 0x02
    REQUEST_MODINDEX = 0x03
    REQUEST_CSMA_RSSI = 0x04
    REQUEST_POWER = 0x05
    REQUEST_AFC = 0x06
    REQUEST_IFBW = 0x07
    REQUEST_TRAINING = 0x08
    REQUEST_SYNCWORD = 0x09
    REQUEST_RXTX_MODE = 0x0A
    REQUEST_BITRATE = 0x0B
    REQUEST_TX = 0x0C
    REQUEST_RX = 0x0D
    REQUEST_TX_FREQUENCY = 0x0E
    REQUEST_RX_FREQUENCY = 0x0F

    # Bootloader Control
    REQUEST_SERIALNUMBER = 0xFC
    REQUEST_FWREVISION = 0xFD
    REQUEST_RESET = 0xFE
    REQUEST_DFU = 0xFF

    # Registers
    REGISTER_N = 0
    REGISTER_VCO_OSC = 1
    REGISTER_TXMOD = 2
    REGISTER_TXRXCLK = 3
    REGISTER_DEMOD = 4
    REGISTER_IFFILTER = 5
    REGISTER_IFFINECAL = 6
    REGISTER_READBACK = 7
    REGISTER_PWRDWN = 8
    REGISTER_AGC = 9
    REGISTER_AFC = 10
    REGISTER_SWD = 11
    REGISTER_SWDTHRESHOLD = 12
    REGISTER_3FSK4FSK = 13
    REGISTER_TESTDAC = 14
    REGISTER_TESTMODE = 15

    # Readback select
    READBACK_RSSI = 0x0014
    READBACK_VERSION = 0x001c
    READBACK_AFC = 0x0016

    # Testmode values
    TESTMODE_OFF = 0
    TESTMODE_PATTERN_CARR = 1
    TESTMODE_PATTERN_HIGH = 2
    TESTMODE_PATTERN_LOW = 3
    TESTMODE_PATTERN_1010 = 4
    TESTMODE_PATTERN_PN9 = 5
    TESTMODE_PATTERN_SWD = 6

    # Sync word
    SW_LENGTH_12BIT = 0
    SW_LENGTH_16BIT = 1
    SW_LENGTH_20BIT = 2
    SW_LENGTH_24BIT = 3
    SW_TOLERANCE_0BER = 0
    SW_TOLERANCE_1BER = 1
    SW_TOLERANCE_2BER = 2
    SW_TOLERANCE_3BER = 3

    # Data length and format
    DATALEN = 289
    DATAEPSIZE = 300
    DATAFMT = "<HHhhBH{0}s".format(DATALEN)

    def find_bluebox(self, index=None, serial=None):
        devs = list(usb.core.find(idVendor=self.VENDOR, idProduct=self.PRODUCT, find_all=True))

        if len(devs) < 1:
            raise Exception("No devices found")

        if serial is not None:
            for dev in devs:
                if usb.util.get_string(dev, dev.iSerialNumber) == serial:
                    return dev
            raise Exception("No BlueBox with serial {0} found".format(serial))
        elif index is not None:
            if len(devs) < index + 1:
                raise Exception("No BlueBox at index {0}".format(index))
            return devs[index]
        else:
            return devs[0]

    def __init__(self, index=None, serial=None, timeout=0):
        self.timeout = timeout

        if index is not None and serial is not None:
            raise Exception("Use either -s or -i but not both")

        self.dev = self.find_bluebox(index, serial)

        if platform.system() != "Windows" and self.dev.is_kernel_driver_active(0) is True:
            self.dev.detach_kernel_driver(0)

        self.dev.set_configuration()

        self.manufacturer = usb.util.get_string(self.dev, self.dev.iManufacturer)
        self.product = usb.util.get_string(self.dev, self.dev.iProduct)
        self.serial = usb.util.get_string(self.dev, self.dev.iSerialNumber)
        self.bus = self.dev.bus
        self.address = self.dev.address

    def _ctrl_write(self, request, data, wValue=0, wIndex=0):
        bmRequestType = usb.util.build_request_type(
            usb.util.CTRL_OUT,
            usb.util.CTRL_TYPE_CLASS,
            usb.util.CTRL_RECIPIENT_INTERFACE)
        self.dev.ctrl_transfer(bmRequestType, request, wValue, wIndex, data, self.timeout)

    def _ctrl_read(self, request, length, wValue=0, wIndex=0):
        bmRequestType = usb.util.build_request_type(
            usb.util.CTRL_IN,
            usb.util.CTRL_TYPE_CLASS,
            usb.util.CTRL_RECIPIENT_INTERFACE)
        return self.dev.ctrl_transfer(bmRequestType, request, wValue, wIndex, length, self.timeout)

    def reg_read(self, reg):
        return struct.unpack("<I", self._ctrl_read(self.REQUEST_REGISTER, 4, wValue=reg))[0] & 0xffff

    def reg_write(self, reg, value):
        value = struct.pack("<I", (value & ~0xff) | reg)
        self._ctrl_write(self.REQUEST_REGISTER, value, wValue=reg)

    def set_tx_frequency(self, freq):
        freq = struct.pack("<I", freq)
        self._ctrl_write(self.REQUEST_TX_FREQUENCY, freq)

    def get_tx_frequency(self):
        freq = self._ctrl_read(self.REQUEST_TX_FREQUENCY, 4)
        freq = struct.unpack("<I", freq)[0]
        return freq

    def set_rx_frequency(self, freq):
        freq = struct.pack("<I", freq)
        self._ctrl_write(self.REQUEST_RX_FREQUENCY, freq)

    def get_rx_frequency(self):
        freq = self._ctrl_read(self.REQUEST_RX_FREQUENCY, 4)
        freq = struct.unpack("<I", freq)[0]
        return freq

    def set_frequency(self, freq):
        freq = struct.pack("<I", freq)
        self._ctrl_write(self.REQUEST_FREQUENCY, freq)

    def get_frequency(self):
        freq = self._ctrl_read(self.REQUEST_FREQUENCY, 4)
        freq = struct.unpack("<I", freq)[0]
        return freq

    def set_modindex(self, mod):
        mod = struct.pack("<B", mod)
        self._ctrl_write(self.REQUEST_MODINDEX, mod)

    def get_modindex(self):
        mod = self._ctrl_read(self.REQUEST_MODINDEX, 1)
        mod = struct.unpack("<B", mod)[0]
        return mod

    def set_bitrate(self, br):
        br = struct.pack("<H", br)
        self._ctrl_write(self.REQUEST_BITRATE, br)

    def get_bitrate(self):
        br = self._ctrl_read(self.REQUEST_BITRATE, 2)
        br = struct.unpack("<H", br)[0]
        return br

    def set_ifbw(self, ifbw):
        ifbw = struct.pack("<B", ifbw)
        self._ctrl_write(self.REQUEST_IFBW, ifbw)

    def get_ifbw(self):
        ifbw = self._ctrl_read(self.REQUEST_IFBW, 1)
        ifbw = struct.unpack("<B", ifbw)[0]
        return ifbw

    def set_syncword(self, sw):
        sw = struct.pack("<I", sw)
        self._ctrl_write(self.REQUEST_SYNCWORD, sw)

    def get_syncword(self):
        sw = self._ctrl_read(self.REQUEST_SYNCWORD, 4)
        sw = struct.unpack("<I", sw)[0]
        return sw

    def set_power(self, power):
        power = struct.pack("<B", power)
        self._ctrl_write(self.REQUEST_POWER, power)

    def get_power(self):
        power = self._ctrl_read(self.REQUEST_POWER, 1)
        power = struct.unpack("<B", power)[0]
        return power

    def set_csma(self, level):
        level = struct.pack("<h", level)
        self._ctrl_write(self.REQUEST_CSMA_RSSI, level)

    def get_csma(self):
        level = self._ctrl_read(self.REQUEST_CSMA_RSSI, 2)
        level = struct.unpack("<h", level)[0]
        return level

    def set_afc(self, state, r, p, i):
        afc = struct.pack("<BBBB", int(state), r, p, i)
        self._ctrl_write(self.REQUEST_AFC, afc)

    def get_afc(self):
        afc = self._ctrl_read(self.REQUEST_AFC, 4)
        state, r, p, i = struct.unpack("<BBBB", afc)
        return bool(state), r, p, i

    def set_training(self, training):
        training = struct.pack("<H", training)
        self._ctrl_write(self.REQUEST_TRAINING, training)

    def get_training(self):
        training = self._ctrl_read(self.REQUEST_TRAINING, 2)
        training = struct.unpack("<H", training)[0]
        return training

    def set_serialnumber(self, serial):
        serial = struct.pack("<I", serial)
        self._ctrl_write(self.REQUEST_SERIALNUMBER, serial)

    def get_serialnumber(self):
        serial = self._ctrl_read(self.REQUEST_SERIALNUMBER, 4)
        serial = struct.unpack("<I", serial)[0]
        return serial

    def version(self):
        return self.reg_read(self.READBACK_VERSION)

    def rssi(self, tests=10):
        gain_correction = (86, 0, 0, 0, 58, 38, 24, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        acc = 0.0
        for i in range(0, tests):
            rb = self.reg_read(self.READBACK_RSSI)
            rssi = rb & 0x7f
            gc = (rb & 0x780) >> 7
            dbm = ((rssi + gain_correction[gc]) * 0.5) - 130
            acc += dbm
        acc = acc / tests
        return int(round(acc))

    def testmode(self, mode):
        self.reg_write(self.REGISTER_TESTMODE, mode << 8)

    def tx_mode(self):
        self._ctrl_write(self.REQUEST_RXTX_MODE, None, wValue=1)

    def rx_mode(self):
        self._ctrl_write(self.REQUEST_RXTX_MODE, None, wValue=0)

    def get_received(self):
        rx = self._ctrl_read(self.REQUEST_RX, 4)
        rx = struct.unpack("<I", rx)[0]
        return rx

    def get_transmitted(self):
        tx = self._ctrl_read(self.REQUEST_TX, 4)
        tx = struct.unpack("<I", tx)[0]
        return tx

    def dfu(self):
        try:
            self._ctrl_write(self.REQUEST_DFU, None, 0)
        except:
            pass

        time.sleep(1)

        self.dev = usb.core.find(idVendor=self.ATMEL_VENDOR)
        if self.dev is None:
            raise Exception("Failed to set device in DFU mode")

    def flash(self, filename):
        self.dfu()

        subprocess.check_output(["dfu-programmer", self.MCU, "erase"], stderr=subprocess.STDOUT)
        subprocess.check_output(["dfu-programmer", self.MCU, "flash", filename], stderr=subprocess.STDOUT)
        subprocess.check_output(["dfu-programmer", self.MCU, "start"], stderr=subprocess.STDOUT)

        time.sleep(1)

        self.dev = usb.core.find(idVendor=self.VENDOR, idProduct=self.PRODUCT)
        if self.dev is None:
            raise Exception("Failed to set device in DFU mode")

        print("Device updated succesfully")

    def reset(self):
        try:
            self._ctrl_write(self.REQUEST_RESET, None, 0)
        except:
            pass

    def get_fwrevision(self):
        fwrev = self._ctrl_read(self.REQUEST_FWREVISION, 8)
        fwrev = struct.unpack("<8s", fwrev)[0]
        return fwrev.decode("ascii")

    def transmit(self, text, timeout=None):
        if not timeout:
            timeout = self.timeout
        if len(text) > self.DATALEN:
            raise Exception("Data too long")
        data = struct.pack(self.DATAFMT, len(text), 0, 0, 0, 0, 0, text)
        self.dev.write(self.DATA_OUT, data, timeout=timeout)

    def receive(self, timeout=None):
        if not timeout:
            timeout = self.timeout
        try:
            ret = self.dev.read(self.DATA_IN, self.DATAEPSIZE, timeout=timeout)
            size, progress, rssi, freq, flags, training, data = struct.unpack(self.DATAFMT, ret)
            data = bytes(data)[0:size]
        except KeyboardInterrupt:
            raise
        except:
            data = None
            rssi = 0
            freq = 0

        return data, rssi, freq
