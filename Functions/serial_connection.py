import serial
import serial.tools.list_ports
from Functions.monitor_pressure_gauge import pressureGauge_Qthread
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QMessageBox
import time
from numpy import nan as np_nan

def get_com_port_list():
    # May have to try opening and closing all the ports if it does
    # not find the ports from the USB adaptor (just catch exceptions
    # up to perhaps 256)
    return [p.device for p in serial.tools.list_ports.comports()]

def communications_error(error_message):
    msg = QMessageBox()
    msg.setWindowTitle('Serial connection error')
    msg.setText(f'Serial connection to the MaxiGauge lost.\n\nError: {error_message}')
    msg.exec()

class SerialPort(QObject):

    def __init__(self, comPortCombo, comRefresh, defaultCOM='COM1'):
        QObject.__init__(self)
        # Add the COM port combo to the class, set to the preset value, check
        # which ports are available
        self.comPortCombo = comPortCombo

        self.comPortCombo.addItem(defaultCOM)
        self.comPortCombo.setEditable(False)
        self.update_com_port_list()

        # Connect the button to update the COM port list
        comRefresh.clicked.connect(lambda: self.update_com_port_list())

        # Initialise the connected status and current pressure values
        self.connected = False
        self.current_pressures = [None] * 6

    def update_com_port_list(self, currentPort=None):
        com_port_list = get_com_port_list()

        # Get the current port if required
        if currentPort == None:
            currentPort = self.comPortCombo.currentText()

        # Reset the list
        self.comPortCombo.clear()
        self.comPortCombo.addItems(com_port_list)

        # Set the value back to its previous value if it exists
        if currentPort in com_port_list:
            self.comPortCombo.setCurrentIndex(com_port_list.index(currentPort))
        else:
            self.comPortCombo.setCurrentIndex(0)


# THE INITIALISATION FUNCTION IN THIS CLASS JUST CONFIRMS THE CORRECT PORT HAS 
# BEEN ACCESSED. THE MAIN SERIAL CONNECTION ARE RUN IN A SEPARATE THREAD.
class pressureSerial(SerialPort):
    queryGauge = pyqtSignal()

    def __init__(self, comPortCombo, comRefresh, connectButton, defaultCOM='COM1'):
        # Initialise general serial port options
        super().__init__(comPortCombo, comRefresh, defaultCOM)

        # Initialise pressure units lookup, and guess initial units of pressure
        self.P_units = ' mbar?'
        self.measurement_unit_lookup = {b'0': 'mbar', b'1': 'Torr', b'2': 'Pascal'}

        # Add the connect button to the class, so properties can be modified, and
        # connect to function to toggle state of connection.
        self.connectButton = connectButton
        self.connectButton.clicked.connect(lambda: self.initialise_pressure_gauge())

    def initialise_pressure_gauge(self):
        if self.connected:
            self.worker.process_disconnect()
            return

        # Get the set COM port
        self.com_port = self.comPortCombo.currentText()

        # Open a connection over the COM port, and attempt to read the units of pressure from
        # the MaxiGauge. If units are not able to be read, the COM port is not a MaxiGauge.
        # Note that a box which responds to UNI\r in the same way as a MaxiGauge would pass
        # this test, but this seems somewhat unlikely.
        with serial.Serial(port=self.com_port, timeout=1, write_timeout=1) as pressureSer:
            try:
                # Test to confirm this is the pressure gauge (and get the pressure units)
                pressureSer.write(b'UNI\r')
                pressureSer.flush()
                response = pressureSer.read_until(expected=b'\r\n')

                # Check for acknowledgement from the gauge
                if response[:1] == b'\x06':
                    pressureSer.write(b'\x05')
                    pressureSer.flush()
                    response = pressureSer.read_until(expected=b'\r\n')
                    self.P_units = ' ' + self.measurement_unit_lookup[response[:1]]
                else:
                    response = b''

            except serial.serialutil.SerialTimeoutException:
                response = b''
            
        if response == b'':
            # No connection established
            print('Cannot establish connection.')
            return

        # Connection established
        self.comPortCombo.setEnabled(False)
        self.connectButton.setText('Connected')
        self.connectButton.setStyleSheet('background-color: rgb(50, 188, 12);')
        self.connected = True

        self.set_up_monitoring_thread()


    def process_responses(self, status, idx, response):
        try:
            # This is the usual response
            if status == 0:
                # Set display, with numbers rounded to 2 d.p.
                response = float(response)
                if response > 1:
                    self.pressure_displays[idx].setText(f'{response:.2f}{self.P_units}')
                else:
                    self.pressure_displays[idx].setText(f'{response:.2e}{self.P_units}')

            else:
                self.pressure_displays[idx].setText(response)
                response = np_nan

            self.current_pressures[idx] = response

            # Update the plot once all pressures have been read. 
            # Note the function used here is from plot_pressure, and is added to the class in MainWindow, 
            if idx == 5:
                self.update_pressure(self.current_pressures)

        except ValueError:
            if idx == 'unexpected response':
                with open('Log files/error_log.txt', 'a') as f:
                    f.write(time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()))
                    f.write(f': Unexpected response from MaxiGauge. Command and response: {response}\n')


    def disconnect_pressure_gauge(self):
        # Make changes to reflect the fact the pressure gauge is not connected
        self.connected = False

        # Close monitoring thread
        self.monitor_thread.quit()

        # Allow COM port to be changed
        self.comPortCombo.setEnabled(True)

        # Update connection button
        self.connectButton.setText('Connect')
        self.connectButton.setStyleSheet('background-color: rgb(255, 188, 188);')

        # Clear pressure display
        for display_widget in self.pressure_displays:
            display_widget.setText('')


    def set_up_monitoring_thread(self):
        self.monitor_thread = QThread()

        # Initialise the worker class
        self.worker = pressureGauge_Qthread()

        # Set variables from main thread
        self.worker.comPort = self.com_port

        self.queryGauge.connect(self.worker.query_gauge)

        # Move the worker to the thread
        self.worker.moveToThread(self.monitor_thread)

        # Connect signals and slots
        self.monitor_thread.started.connect(self.worker.run)
        # Connect responses to the correct processes
        self.worker.no_response.connect(communications_error)
        self.worker.output.connect(self.process_responses)
        # Clean up for when thread completes
        self.worker.finished.connect(self.monitor_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)
        self.worker.finished.connect(self.disconnect_pressure_gauge)

        # Start the thread
        self.monitor_thread.start()
