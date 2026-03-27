from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QColorDialog
from PyQt6.QtGui import QColor
import sys
from copy import deepcopy

class plotColourWindow(QDialog):
    def __init__(self, colour_list=[(0,0,0),(255,165,0),(0,0,255),(0,255,255),(139,0,0),(0,128,0)]):
        super().__init__()

        self.original_colour_list = colour_list
        self.new_colour_list = deepcopy(colour_list)

        self.setWindowTitle("Choose line colours")
        self.setFixedSize(350, 100)

        # Initialise colour picker dialogue
        self.colourPicker = QColorDialog()

        self.colourButtons = [0]*6
        for i, colour in enumerate(colour_list):
            self.colourButtons[i] = QPushButton(text=str(i+1), parent=self)
            self.setButtonColour(i, colour)
            self.colourPicker.setCustomColor(i, QColor(*colour))
        
        # Connect buttons (not working in loop for some reason)
        self.colourButtons[0].clicked.connect(lambda: self.getColour(0))
        self.colourButtons[1].clicked.connect(lambda: self.getColour(1))
        self.colourButtons[2].clicked.connect(lambda: self.getColour(2))
        self.colourButtons[3].clicked.connect(lambda: self.getColour(3))
        self.colourButtons[4].clicked.connect(lambda: self.getColour(4))
        self.colourButtons[5].clicked.connect(lambda: self.getColour(5))

        self.colourButtonBox = QHBoxLayout()
        [self.colourButtonBox.addWidget(_) for _ in self.colourButtons]
        
        # Set up the Ok and Cancel buttons
        # self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.addButton('Apply', QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonBox.addButton('Reset', QDialogButtonBox.ButtonRole.ResetRole)
        self.buttonBox.addButton('Close', QDialogButtonBox.ButtonRole.RejectRole)

        # Activate close button
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.rejected.connect(self.resetColours)

        # self.buttonBox.accepted.connect(self.accept)

        # Connect the reset button
        for i in range(3):
            if self.buttonBox.buttonRole(self.buttonBox.buttons()[i]) == QDialogButtonBox.ButtonRole.ResetRole:
                self.buttonBox.buttons()[i].clicked.connect(self.resetColours)
    
        # Generate the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Click on the appropriate box below to change the plot colour."))
        layout.addLayout(self.colourButtonBox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


    def setButtonColour(self, idx, colour):
        # Set the background colour of the button to match the line, and adjust the text colour to white or black
        if sum(colour)/3 < 127.5:
            self.colourButtons[idx].setStyleSheet(f'background-color:rgb{colour}; color:white; font-weight:bold')
        else:
            self.colourButtons[idx].setStyleSheet(f'background-color:rgb{colour}; color:black; font-weight:bold')


    def getColour(self, idx):
        # Open colour picker, and set colour if chosen
        colour = self.colourPicker.getColor(QColor(*self.new_colour_list[idx]), self, f'Select colour for line {idx}')

        if colour.isValid():
            self.new_colour_list[idx] = colour.getRgb()[:3]
            self.setButtonColour(idx, self.new_colour_list[idx])
        

    def resetColours(self):
        self.new_colour_list = deepcopy(self.original_colour_list)
        [self.setButtonColour(i, _) for i, _ in enumerate(self.new_colour_list)]


    def accept(self):
        self.original_colour_list = deepcopy(self.new_colour_list)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = plotColourWindow()
    window.show()
    app.exec()