from PyQt6.QtCore import *
import time
import serial

class pressureGauge_Qthread(QObject):
    output = pyqtSignal(int, int, str)
    no_response = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._disconnecting = False
        self.poll_timer = None
        self.serial_context = None

    def run(self):
        # Connect to COM port
        self.serial_context = serial.Serial(port=self.comPort, timeout=1, write_timeout=1)
        self.pressureSer = self.serial_context.__enter__()

        # Start up polling timer 
        self.poll_timer = QTimer(self)
        self.poll_timer.setSingleShot(True)
        self.poll_timer.timeout.connect(self.query_gauge)
        self.poll_timer.start(self.poll_rate)


    @pyqtSlot(int)
    def update_poll_rate(self, poll_rate):
        self.poll_rate = poll_rate


    @pyqtSlot()
    def process_disconnect(self):
        if self._disconnecting:
            return

        self._disconnecting = True

        if self.poll_timer is not None:
            self.poll_timer.stop()
            self.poll_timer.deleteLater()
            self.poll_timer = None

        if self.serial_context is not None:
            self.serial_context.__exit__(None,None,None)
            self.serial_context = None

        self.finished.emit()
        

    def query_gauge(self):
        if self._disconnecting:
            return

        # Start the next timer
        self.poll_timer.start(self.poll_rate)

        # Read pressure for all sensors
        for sensor_no in range(1,7):
            try:
                # Initialise communication regarding the sensor. Expected response is b'\x06'.
                self.pressureSer.write(bytes(f'PR{sensor_no}\r', 'ascii'))
                self.pressureSer.flush()
                response = self.pressureSer.read_until(expected=b'\r\n')

                if not response.endswith(b"\r\n"):
                    print(f'Incomplete gauge response from the MaxiGauge. {sensor_no}: {response!r}')
                    continue

                if response[:1] != b'\x06':
                    self.response = False
                    self.output.emit(-1, -1, f'PR{sensor_no}\r' + response.decode())
                    print(f'Unexpected response from the MaxiGauge. {sensor_no}: {response!r}')
                    continue

                # Then read the pressure for the channel from the MaxiGauge.
                self.pressureSer.write(b'\x05')
                self.pressureSer.flush()
                response = self.pressureSer.read_until(expected=b'\r\n')

                if not response.endswith(b"\r\n"):
                    print(f'Incomplete gauge response from the MaxiGauge. {sensor_no}: {response!r}')
                    continue

            except serial.serialutil.SerialTimeoutException:            
                self.response = False
                self.no_response.emit('No response from the MaxiGauge.')
                return b''

            # Process and output the response
            status, response = self.process_response(response)
            self.output.emit(status, sensor_no - 1, response)



    def process_response(self, response):
        raw_response = response

        text = response.decode("ascii").strip()

        status_text, separator, value_text = text.partition(",")

        # Process cases with no numberical output
        if status_text == '3':
            return -1, 'Sen. err.'
        elif status_text == '4':
            return -1, 'Sen. off'
        elif status_text == '5':
            return -1, 'No sen.'
        elif status_text == '6':
            return -1, response

        try:
            pressure = float(value_text)
        except ValueError as exc:
            print(f'Unexpected value: {value_text}')
            return -1, raw_response.decode()

        return 0, str(pressure)
