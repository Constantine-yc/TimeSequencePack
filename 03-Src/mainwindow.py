# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QMainWindow
from mainwindow_ui import Ui_MainWindow
from projectdefines import globaldefines
from timeseqs import TimeSeq


class MainWindow(QMainWindow):
    ui = Ui_MainWindow()
    time_seq = None

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.ui.setupUi(self)

        self.ui.leModel.setText(globaldefines.model)
        self.ui.leModel.setReadOnly(True)
        self.ui.leModel.setEnabled(False)

        self.ui.lePath.setText(globaldefines.path)
        self.ui.lePath.setReadOnly(True)
        self.ui.lePath.setEnabled(False)

        self.ui.leName.setText(globaldefines.output_name)
        self.ui.leName.setReadOnly(True)
        self.ui.leName.setEnabled(False)

        self.ui.leVersion.setText(globaldefines.output_version_str())
        self.ui.leVersion.setReadOnly(True)
        self.ui.leVersion.setEnabled(False)

        self.ui.leSupport.setText('')
        self.ui.leSupport.setReadOnly(True)
        self.ui.leSupport.setEnabled(False)

        self.ui.leDone.setText('')
        self.ui.leDone.setReadOnly(True)
        self.ui.leDone.setEnabled(False)

        self.ui.lstFiles.itemClicked.connect(self.on_lstFiles_itemClicked)

    @pyqtSlot()
    def slotShow(self):
        self.show()

        self.ui.leModel.setText(globaldefines.model)
        self.ui.leName.setText(globaldefines.output_name)
        self.ui.leVersion.setText(globaldefines.output_version_str())

        self.time_seq = TimeSeq(globaldefines.path)

        self.time_seq.sig_support_done.connect(self.slot_timeseq_support_done)
        self.time_seq.sig_write_done.connect(self.slot_timeseq_write_done)
        self.time_seq.sig_init.connect(self.slot_timeseq_init)
        self.time_seq.sig_uninit.connect(self.slot_timeseq_uninit)
        self.time_seq.sig_changed.connect(self.slot_timeseq_changed)

        self.time_seq.start()

    @pyqtSlot(str)
    def slot_timeseq_init(self, file_path):
        globaldefines.other_trace()
        find_items = self.ui.lstFiles.findItems(file_path, Qt.MatchStartsWith)
        if len(find_items) != 0:
            globaldefines.other_trace("slot_timeseq_init but count incorrect")
        self.ui.lstFiles.addItem(file_path + '-init')

    @pyqtSlot(str)
    def slot_timeseq_uninit(self, file_path):
        globaldefines.other_trace()
        find_items = self.ui.lstFiles.findItems(file_path, Qt.MatchStartsWith)
        for find_item in find_items:
            self.ui.lstFiles.removeItemWidget(find_item)

    @pyqtSlot(str)
    def slot_timeseq_changed(self, file_path):
        globaldefines.other_trace()
        find_items = self.ui.lstFiles.findItems(file_path, Qt.MatchStartsWith)
        if len(find_items) != 1:
            globaldefines.other_trace("%s not found or too much")
        find_items[0].setText(file_path + '-' + self.time_seq.get_status(file_path))

    def on_lstFiles_itemClicked(self, current):
        globaldefines.other_trace()
        file_path = current.text()[0:current.text().find('-')]
        self.ui.lstInfo.clear()
        infos = self.time_seq.get_info(file_path)
        for info in infos:
            self.ui.lstInfo.addItem(str(info))

    @pyqtSlot(str)
    def slot_timeseq_support_done(self, support_info):
        self.ui.leSupport.setText(support_info)

    @pyqtSlot(str)
    def slot_timeseq_write_done(self, done_info):
        self.ui.leDone.setText(done_info)
