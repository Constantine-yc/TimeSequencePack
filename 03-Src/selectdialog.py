# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog
from selectdialog_ui import Ui_SelectDialog
from projectdefines import globaldefines
import re


class SelectDialog(QDialog):
    sig_Confirmed = pyqtSignal()
    ui = Ui_SelectDialog()

    def __init__(self, parent=None):
        super(SelectDialog, self).__init__(parent=parent)
        self.ui.setupUi(self)

        self.ui.leModel.setText("")

        self.ui.lePath.setText(globaldefines.path)
        self.ui.lePath.setReadOnly(True)

        self.ui.leOutputName.setText("")
        self.ui.leVersion.setText("1.0.0.0")
        self.ui.lbInfo.setText("")

        self.setWindowTitle('%s %s' % (globaldefines.sw_name, globaldefines.sw_version))

        self.sig_Confirmed.connect(parent.slotShow)

    @pyqtSlot()
    def on_btnConfirm_clicked(self):
        globaldefines.useroptrace()

        model_pattern = r'^[-_a-zA-Z0-9]+$'
        model_info = re.match(model_pattern, self.ui.leModel.text())
        if not model_info:
            self.ui.lbInfo.setText("机型错误")
            return

        name_pattern = r'^[-._a-zA-Z0-9]+$'
        name_info = re.match(name_pattern, self.ui.leOutputName.text())
        if not name_info:
            self.ui.lbInfo.setText("文件名错误")
            return

        version_pattern = r'^(\s*)(\d+)\.(\d+)\.(\d+)\.(\d+)(\s*)$'
        version_info = re.match(version_pattern, self.ui.leVersion.text())

        if not version_info \
                or int(version_info.group(2)) >= 256\
                or int(version_info.group(3)) >= 256\
                or int(version_info.group(4)) >= 256\
                or int(version_info.group(5)) >= 256:
            self.ui.lbInfo.setText("版本号错误")
            return

        globaldefines.model = self.ui.leModel.text()
        globaldefines.output_name = self.ui.leOutputName.text()
        globaldefines.output_version = [int(version_info.group(2)), int(version_info.group(3)), int(version_info.group(4)), int(version_info.group(5))]
        print(globaldefines.model)
        print(globaldefines.output_name)
        print(globaldefines.output_version)
        print(globaldefines.output_version_str())
        self.done(self.Accepted)

        self.sig_Confirmed.emit()
