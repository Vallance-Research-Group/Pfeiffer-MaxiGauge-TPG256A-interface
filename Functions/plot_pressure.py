import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from numpy import nan as np_nan, array as np_array, roll as np_roll, empty as np_empty, log10 as np_log10
import time
import os

class pressurePlot():
    def __init__(self, graph_widget):
        self.data_points = 0

        # Set up the plotting
        self.graphWidget = graph_widget

        self.graphWidget.setBackground("w")
        styles = {"color": "black", "font-size": "14px"}
        self.graphWidget.setLabel("left", "Pressure / mbar", **styles)
        self.graphWidget.setLabel("bottom", "Time", **styles)
        x_axis = pg.DateAxisItem()
        legend = self.graphWidget.addLegend()
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.show()
        self.plotItem = self.graphWidget.getPlotItem()

        self.plotItem.setAxisItems({'bottom': x_axis})

        # Initialise plot for each channel
        self.pressurePlots = [pg.PlotDataItem([1,2], [1,2], name=f'Ch. {i+1}', pen={'color':colour, 'width': 2}) for i, colour in enumerate(['black','orange','blue','cyan','darkRed','green'])]
        [self.plotItem.addItem(_) for _ in self.pressurePlots]

        # Make arrays to store the time and pressures
        self.time_array = np_empty(50000); self.time_array[:] = np_nan
        self.pressure_array = np_empty((6,50000)); self.pressure_array[:] = np_nan


    def set_plot_visibility(self, idx, newState):
        self.pressurePlots[idx].setVisible(newState)


    def set_y_scale_type(self, newState):
        # Update axis label
        self.log_scale = newState
        self.update_y_axis_pressure_label('mbar')

        # Plot data if there is data to plot
        try: self.plot_data()
        except AttributeError: pass


    def set_auto_graph_time(self, time):
        # Time is provided in minutes, so convert to seconds for plotting purposes
        self.autoGraphTime = time * 60

        # Plot data if there is data to plot
        try: self.set_graph_range()
        except AttributeError: pass


    def set_font_size(self, size):
        self.font_size = size

        # Generate new font and assign to the tick axes
        font=QtGui.QFont()
        font.setPixelSize(size)
        self.graphWidget.getAxis("bottom").setStyle(tickFont = font)
        self.graphWidget.getAxis("left").setStyle(tickFont = font)


    def plot_data(self):
        # Add data
        if self.log_scale:
            [self.pressurePlots[i].setData(x=self.time_array[-self.data_points:], y=np_log10(self.pressure_array[i,-self.data_points:])) for i in range(6)]
        else:
            [self.pressurePlots[i].setData(x=self.time_array[-self.data_points:], y=self.pressure_array[i,-self.data_points:]) for i in range(6)]

        self.set_graph_range()


    def set_graph_range(self):
        # A bit of a janky way of making the display range work.
        if self.time_array[-1] - self.start_time < self.autoGraphTime:
            if self.plotItem.vb.state['autoRange'][1]:
                self.plotItem.vb.setXRange(self.start_time, self.time_array[-1])
                self.plotItem.vb.setAutoVisible(y=True)
            else:
                self.plotItem.vb.setAutoVisible(y=False)

        else:
            if self.plotItem.vb.state['autoRange'][1]:
                self.plotItem.vb.setXRange(self.time_array[-1] - self.autoGraphTime, self.time_array[-1])
                self.plotItem.vb.setAutoVisible(y=True)
            else:
                self.plotItem.vb.setAutoVisible(y=False)


    def update_pressure(self, pressures):
        # Gets first time, for auto-scale purposes
        if self.data_points == 0: self.start_time = time.time()

        # Always add from end, and cycle round such that 
        # Add time data
        self.time_array = np_roll(self.time_array, -1)
        self.time_array[-1] = time.time()

        # Add pressure data
        self.pressure_array = np_roll(self.pressure_array, -1, axis=1)
        self.pressure_array[:,-1] = pressures

        # Not particularly necessary, but is used to define range of data plotted
        if self.data_points < 50000: self.data_points += 1
        self.plot_data()


    def update_units(self, read_pressures):
        # Check units consistent
        if self.P_units != units.strip():
            self.P_units = units.strip()
            self.update_y_axis_pressure_label(self.P_units)


    def update_y_axis_pressure_label(self, units):
        if self.log_scale:
            self.plotItem.getAxis('left').setLabel(f'log<sub>10</sub>(Pressure / (1 {units}))')
        else:
            self.plotItem.getAxis('left').setLabel(f'Pressure / {units}')

            
def process_pressures(value):
    # Check whether the pressure is a number or not
    try:
        float(value)
        return value
    except ValueError:
        return np_nan