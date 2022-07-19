import re
import time

import serial
from serial.tools import list_ports

BAUDRATE = 115200
TIMEOUT = .1
CONN_ATTEMPTS = 5


class ArduinoConnectionException(Exception):
    pass


class ArduinoConnection:
    def __init__(self):
        self.arduino = None

    def _parse_response(self, data):
        if re.match("^[01]:[01]:[01]:[01];$", data):
            return dict(zip(
                ["b1_stat", "b2_stat", "b1_lock", "b2_lock"],
                map(lambda x: x.strip(), data[:-1].split(":"))
            ))
        else:
            return None

    def _write_read(self, msg, parse_res=True):
        if self.arduino:
            self.arduino.read_all()  # flush buffer
            self.arduino.write(bytes(msg, 'utf-8'))
            time.sleep(0.5)
            data = self.arduino.read_all().decode().strip()
            if parse_res:
                data = self._parse_response(data)
            return data
        else:
            raise ArduinoConnectionException("Not connected")

    def get_box_status(self):
        return self._write_read("AT")

    def open_box_1(self):
        return self._write_read("O1")

    def close_box_1(self):
        return self._write_read("C1")

    def open_box_2(self):
        return self._write_read("O2")

    def close_box_2(self):
        return self._write_read("C2")

    def open_connection(self, port, attempts=CONN_ATTEMPTS):
        for _ in range(attempts):
            try:
                self.arduino = serial.Serial(
                    port=port, baudrate=BAUDRATE, timeout=TIMEOUT)
                time.sleep(0.2)
                box_status = self.get_box_status()
                if box_status:
                    return True
            except:
                continue
        self.arduino = None
        return False

    def close_connection(self):
        if self.arduino:
            self.arduino.close()
            self.arduino = None

    def get_available_ports(self):
        return [p.device for p in list_ports.comports()]

    def is_connected(self):
        return self.arduino is not None
