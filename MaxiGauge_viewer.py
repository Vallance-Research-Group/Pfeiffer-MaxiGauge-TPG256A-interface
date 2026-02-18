from PyQt6 import QtWidgets
import sys
from Functions.main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()

if __name__ == '__main__':
    main()