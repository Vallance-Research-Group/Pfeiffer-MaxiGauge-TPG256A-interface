from PyQt6.QtCore import *
import time
import serial

class pressureGauge_Qthread(QObject):
    output = pyqtSignal(int, int, str)
    no_response = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        # Set up the required variables
        self.response = True

        # Set up connection to close process on disconnect
        self.finished.connect(self.process_disconnect)

        # Open the serial port and query 
        with serial.Serial(port=self.comPort, timeout=1, write_timeout=1) as pressureSer:
            self.pressureSer = pressureSer
            time.sleep(0.1)

            # This loop runs until the disconnect button is pressed
            while self.response:
                # Sleep most of the time to reduce resource usage
                time.sleep(0.1)

            # Flush out any remaining commands and responses
            time.sleep(0.3)

        self.finished.emit()

    def process_disconnect(self):
        # Will stop after the next iteration
        self.response = False

    def query_gauge(self):
        # Read pressure for all sensors
        for sensor_no in range(1,7):
            try:
                # Initialise communication regarding the sensor. Expected response is b'\x06'.
                self.pressureSer.write(bytes(f'PR{sensor_no}\r', 'ascii'))
                self.pressureSer.flush()
                response = self.pressureSer.read_until(expected=b'\r\n')

                if response[:1] != b'\x06':
                    self.response = False
                    self.output.emit(-1, 'unexpected response', f'PR{sensor_no}\r' + response.decode())
                    print(f'PR{sensor_no}\r' + response.decode())
                    self.no_response.emit('Unexpected response from the MaxiGauge.')
                    return b''

                # Then read the pressure for the channel from the MaxiGauge.
                self.pressureSer.write(b'\x05')
                self.pressureSer.flush()
                response = self.pressureSer.read_until(expected=b'\r\n')

            except serial.serialutil.SerialTimeoutException:            
                self.response = False
                self.no_response.emit('No response from the MaxiGauge.')
                return b''

            # Process and output the response
            status, response = self.process_response(response)
            self.output.emit(status, sensor_no - 1, response)

    def process_response(self, response):
        response = response.decode()

        # Process cases with no numberical output
        if response[0] == '3':
            return -1, 'Sen. err.'
        elif response[0] == '4':
            return -1, 'Sen. off'
        elif response[0] == '5':
            return -1, 'No sen.'
        elif response[0] == '6':
            return -1, response

        return 0, str(float(response[2:-2]))
