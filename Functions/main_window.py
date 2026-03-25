from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
import os
import time
import pyqtgraph as pg
from Functions.serial_connection import pressureSerial as pSerial
from Functions.plot_pressure import pressurePlot
from math import ceil
from pathlib import Path

pg.setConfigOption('foreground', 'k')
pg.setConfigOption('background', 'w')


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI
        uic.loadUi(os.path.join(Path.cwd(), 'Pfeiffer_TPG256A.ui'), self)

        # Compile the displays and plot checkboxes into arrays since they are used together.
        self.pressure_displays = [self.pressureDisplayCh1, self.pressureDisplayCh2,
                                  self.pressureDisplayCh3, self.pressureDisplayCh4,
                                  self.pressureDisplayCh5, self.pressureDisplayCh6]

        # Add class to process the serial connection
        self.pressureGaugeSerial = pSerial(self.pressureComPort, self.comRefreshButton, self.pressureConnectButton)
        self.pressureGaugeSerial.pressure_displays = self.pressure_displays

        # GRAPHICAL INTERFACE #########################################################
        # Initialise the pressure graph
        self.pressure_plot = pressurePlot(self.pressureGraphWidget)
        # Set graph state (y scale type, time range to display on autorange)
        self.pressure_plot.set_y_scale_type(self.logScaleCheck.isChecked())

        # Connections to change graphing defaults
        self.logScaleCheck.stateChanged.connect(self.pressure_plot.set_y_scale_type)
        self.spinFontSize.valueChanged.connect(self.pressure_plot.set_font_size)

        # Add plot update function to the serial connection class
        self.pressureGaugeSerial.update_pressure = self.pressure_plot.update_pressure

        ###############################################################################

        # Set configuration, either from user config file (if present) or preset values
        self.load_defaults()

        # Start timers to call pressure reading and log writing
        self.initialise_timers()

        # Menu options
        self.actionSaveConfig.triggered.connect(self.save_defaults)
        self.actionRestoreDefaults.triggered.connect(self.delete_config)
        self.actionPressureReadPeriod.triggered.connect(self.update_pressure_query_timer)
        self.actionLogWritePeriod.triggered.connect(self.update_log_timer)
        self.actionSetAutorangeWindow.triggered.connect(self.update_plot_autorange_time_window)

        self.changeLogButton.clicked.connect(self.change_log_path)
        # Initialise for writing log
        self.date = None


    # Timers ##########################################################################
    def initialise_timers(self):
        # Set up query and logging timers, which cause the pressure to be queried
        # and the log file to be written (if appropriate conditions are met) at
        # regular intervals
        self.query_timer = QTimer()
        self.log_timer = QTimer()

        self.query_timer.timeout.connect(self.execute_gauge_query)
        self.log_timer.timeout.connect(self.execute_log_write)

        self.query_timer.start(self.pressure_read_period)
        self.log_timer.start(self.log_write_period)


    def update_pressure_query_timer(self):
        value, res = QtWidgets.QInputDialog.getDouble(self,
                            'Set pressure poll rate',
                            'Set pressure polling rate (in s) between 0.25 s and 10 s.',
                            self.pressure_read_period / 1000, # Initial value
                            0.25,                             # Minimum value
                            10,                               # Maximum value
                            2)                                # Decimal places

        # Update timer time period if updated. Timer takes ms input.
        if res:
            self.pressure_read_period = int(value * 1000)
            self.query_timer.start(self.pressure_read_period)


    def update_log_timer(self):
        value, res = QtWidgets.QInputDialog.getInt(self, 
                            'Set log time period',
                            'Set log write time period (in s) between polling rate of pressure gauge (rounded up to nearest second) and one hour.',
                            int(self.log_write_period / 1000),            # Initial value
                            int(ceil(self.pressure_read_period / 1000)),  # Minimum value is the pressure poll rate
                            60 * 60)                                      # Maximum value is one hour

        # Update timer time period if updated. Timer takes ms input.
        if res:
            self.log_write_period = value * 1000
            self.log_timer.start(self.log_write_period)

    ###############################################################################

    # Functions run on timers #####################################################
    def execute_gauge_query(self):
        if self.pressureGaugeSerial.connected:
            self.pressureGaugeSerial.queryGauge.emit()

    def execute_log_write(self):
        if self.pressureGaugeSerial.connected and self.saveLogCheck.isChecked():
            self.write_log()

    ###############################################################################

    # Action menu #################################################################

    def update_plot_autorange_time_window(self):
        value, res = QtWidgets.QInputDialog.getDouble(self,
                            'Set autorange time window',
                            'Set autorange time window (in minutes) between 0.5 min and 120 min.',
                            round(self.pressure_plot.autoGraphTime / 60, 2), # Initial value
                            0.5,                             # Minimum value
                            120,                               # Maximum value
                            2)                                # Decimal places

        # Update timer time period if updated. Timer takes ms input.
        if res:
            self.pressure_plot.set_auto_graph_time(value)

    ###############################################################################

    # Read and write config file ##################################################
    # Config file format by line:
    # COM port
    # Channels name and plot state (tab delimited, state 1/0)
    # Pressure read time period / ms
    # Autorange time / minutes
    # log scale for pressure plot (1/0)
    # Save pressure log (1/0)
    # Log directory
    # Log write time period / ms

    def load_defaults(self, *, reset_config=False):
        try:
            # Ignore presence of config file if resetting config
            if reset_config: raise FileNotFoundError

            with open('user_config.txt', 'r') as f:
                # Update variables from the user_config file.
                f.readline()
                self.pressureGaugeSerial.update_com_port_list(f.readline().strip())

                for i in range(6):
                    ch_name, plot_state = f.readline().strip().split('\t')
                    exec(f"self.pLabelCh{i+1}.setText('{ch_name}')")
                    self.pressure_plot.set_plot_visibility(i, int(plot_state))

                self.pressure_read_period = int(f.readline().strip())
                self.pressure_plot.set_auto_graph_time(float(f.readline().strip()))
                self.logScaleCheck.setChecked(int(f.readline().strip()))
                self.saveLogCheck.setChecked(int(f.readline().strip()))
                self.log_dir = f.readline().strip()
                self.log_write_period = int(f.readline().strip())
        except FileNotFoundError:
            # Most options are initialised to their default values
            self.pressure_read_period = 1000
            self.log_write_period = 30000
            self.log_dir = 'Log files'
            self.pressure_plot.set_auto_graph_time(5.)

            # These options are set by default in the GUI, so only need to be used when resetting the configuration
            if reset_config:
                for i in range(6):
                    exec(f"self.pLabelCh{i+1}.setText('Channel {i+1}:')")
                    self.pressure_plot.set_plot_visibility(i, True)
                self.logScaleCheck.setChecked(True)
                self.saveLogCheck.setChecked(True)

        if self.logFileName.text() == '':
            self.logFileName.setText(os.path.join(self.log_dir, time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.txt'))



    def save_defaults(self):
        with open('user_config.txt', 'w') as f:
            f.write('For format details, see MaxiGauge_viewer.py or Readme.md (https://github.com/Vallance-Research-Group/Pfeiffer-MaxiGauge-TPG256A-interface)\n')
            # Write all the variables according to the config format
            f.write(self.pressureComPort.currentText() + '\n')
            for i in range(6):
                f.write(f'{eval(f'self.pLabelCh{i+1}.text()')}\t')
                f.write(f'{int(self.pressure_plot.pressurePlots[i].isVisible())}\n')
            f.write(f'{self.pressure_read_period}\n')
            f.write(f'{self.pressure_plot.autoGraphTime}\n')
            f.write(f'{int(self.logScaleCheck.isChecked())}\n')
            f.write(f'{int(self.saveLogCheck.isChecked())}\n')
            f.write(f'{self.log_dir}\n')
            f.write(f'{self.log_write_period}\n')


    def delete_config(self):
        if not os.path.isfile("user_config.txt"):
            msg = QtWidgets.QMessageBox(text='No user config file found.', windowTitle='File not found')
            msg.exec(); return

        msgbox = QtWidgets.QMessageBox(icon=QtWidgets.QMessageBox.Icon.Question)
        msgbox.setWindowTitle('Config reset')
        msgbox.setText("Do you also want to delete the user config file?")
        msgbox.setInformativeText("Cancel to retain current state.")

        msgbox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel
        )

        msgbox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        res = msgbox.exec()
        
        if res == QtWidgets.QMessageBox.StandardButton.Yes:
            self.load_defaults(reset_config=True)
            os.remove("user_config.txt")

        elif res == QtWidgets.QMessageBox.StandardButton.No:
            self.load_defaults(reset_config=True)

    ###############################################################################

    # Logging #####################################################################
    def change_log_path(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Set log file name', self.logFileName.text(), 'Text files (*.txt);;Dat files (*.dat);;All files(*.*)')
        
        if fname[0] != '':
            self.log_dir = os.path.dirname(fname[0])
            self.logFileName.setText(fname[0])


    def write_log(self):
        fname = self.logFileName.text()

        if not os.path.isfile(fname):
            # Write the headings
            with open(fname, 'a') as f:
                f.write(f'All pressure units: {self.pressureGaugeSerial.P_units}\n')

                f.write('Time\t')

                labels = [eval(f'self.pLabelCh{i+1}.text()') for i in range(6)]
                for i in range(6):
                    if labels[i][-1] == ':': labels[i] = labels[i][:-1]

                f.write('\t'.join(labels) + '\n')


        with open(fname, 'a') as f:
            # Get date and time
            datetime = time.strftime('%y-%m-%d:%H-%M-%S', time.localtime(self.pressure_plot.time_array[-1]))

            # Write time (and date on first instance)
            if self.date != datetime[:8]:
                f.write(f'Date: {datetime[:8]}\n')
                self.date = datetime[:8]

            f.write(datetime[-8:] + '\t')

            # Pressure
            f.write('\t'.join([f'{self.pressure_plot.pressure_array[i,-1]}\t' for i in range(6)]))
            f.write('\n')
            
    ###############################################################################



    def closeEvent(self, event):
        # Close connection to pressure gauge on closing the window
        if self.pressureGaugeSerial.connected:
            self.pressureGaugeSerial.worker.process_disconnect()

        time.sleep(0.3)