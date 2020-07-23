# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets
from selectdialog import SelectDialog
from mainwindow import MainWindow

if __name__ == "__main__":
    application = QtWidgets.QApplication(sys.argv)
    mainwindow = MainWindow()
    selectdialog = SelectDialog(mainwindow)

    selectdialog.show()
    sys.exit(application.exec_())
