# Pfeiffer MaxiGauge interface (TPG256A) - Testing branch

This repository provides a simple interface for reading the pressure from a Pfeiffer MaxiGauge. It has been designed for use with the TPG256A and has only been tested with this model; other models may require modification of the serial communication code for the code to function correctly.

## Use

The UI is initiallised by running the script MaxiGauge_viewer.py. Requirements are listed in the file requirements.txt.

To establish a connection to the MaxiGauge, the appropriate COM port must be selected by using the drop down at the top of the UI, and the connect button pressed. If the expected response is returned, it is assumed a MaxiGauge has been connected and the code begins polling the gauge at fixed intervals. In this testing branch, false data is generated for each channel if a MaxiGauge is not connected. The pressures are displayed both numerically and graphically. Numerical values can be found in the Monitor - values tab, where the pressures on each of the six channels are displayed. In the Monitor - graph tab, the pressure for each channel is plotted. Channels can be toggled on and off by clicking on the appropriatly-coloured line in the legend. At the bottom of the tab, the y scale can be toggled between log and linear, the text size for the tick labels can be changed, and the plot line weight can be adjusted. At the bottom of the window, a toggle for logging and the directory in which the log file are noted.

In the Config menu item, the time period between both reading the pressure gauge and writing the log file can be changed, the autorange time window can be modified, and the line colours used in the plot can be adjusted. The application configuration can also be saved or restored to the default values. The configuration relates to the following:

 - COM port (default: COM1)
 - Channel names and plot state (default for the first channel: Channel 1: 1)
 - Pressure gauge polling period (default: 1 s)
 - Graph autorange time (default: 5 min)
 - Log scale for pressure plot (default: 1)
 - Save pressure log (default: 1)
 - Log directory (default: Log files)
 - Log file write period (default: 30 s)
 - Tick font size (default: 12)
 - Plot line width (default: 2.)
 - Plot line colour (default: CSS RGB value of black, orange, blue, cyan, dark red and green)

The log file consists of a header, followed by lines containg the time and pressures recorded each time period set in the configuration.

## Notes

At present, it is assumed that the pressure units are not changed during operation. For the display to update with the correct units, the connection must be toggled off and on. Note that the log file will not note the new units, so a new log file would also need to be created for clarity.

Note that this is the testing branch, so false data are generated for all channels while no pressure gauge is connected for testing purposes. Please use the <a href="https://github.com/Vallance-Research-Group/Pfeiffer-MaxiGauge-TPG256A-interface">main branch</a> for operation of a MaxiGauge.

## Potential upgrades

 - Add option to convert all pressures to units chosen by user to keep units in log file consistent, regardless of units chosen on MaxiGauge.
 - Add capability to poll pressure units during operation, updating display.
 - Handle error which is occasionally raised on disconnecting from the pressure gauge.