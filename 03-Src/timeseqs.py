# -*- coding: utf-8 -*-
import copy
import json
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QMutex, QMutexLocker
import os
import re
import struct
from projectphaser import ProjectFile
from projectdefines import globaldefines


class TimeSeq(QObject):
    _thread = None

    sig_support_done = pyqtSignal(str)
    sig_write_done = pyqtSignal(str)

    sig_init = pyqtSignal(str)
    sig_uninit = pyqtSignal(str)
    sig_changed = pyqtSignal(str)

    _path = None

    _bases = {}
    # _func = None
    # _assi = None

    _BASE_PAT = r'^\d\d\d.*$'
    _BASE_EXT = '.mpp'
    # _FUNC_NAME = 'func.tim'
    # _ASSIST_NAME = 'def.tim'

    def __init__(self, path, parent=None):
        # globaldefines.other_trace()
        super(TimeSeq, self).__init__(parent)
        self._path = path
        self._object_name = '%s_V%s.bin' % (globaldefines.output_name, globaldefines.output_version_str())
        self._translate_name = '%s_translate.txt' % globaldefines.model
        self._check_name = '%s_check.txt' % globaldefines.model
        self._translate_rules = {}
        self._check_rules = {}
        self._thread = QThread(None)
        self._thread.start()

    def _is_valid_files_path(self, file_path):
        pre, ext = os.path.splitext(file_path)
        if ext == self._BASE_EXT and re.match(self._BASE_PAT, pre):
            return True
        return False

    def _get_file_paths(self):
        return [filepath for filepath in os.listdir(self._path) if self._is_valid_files_path(filepath)]

    def _clear(self):
        for base in self._bases:
            base.sig_init.disconnect(self.sig_init)
            base.sig_uninit.disconnect(self.sig_uninit)
            base.sig_changed.disconnect(self.sig_changed)
            base.sig_changed.disconnect(self.write)
            del base

    def _create(self):
        globaldefines.other_trace()

        translate_info = 'translate ok'
        try:
            with open(self._translate_name) as _translate_file:
                self._translate_rules = json.loads(_translate_file.read())
        except Exception as e:
            globaldefines.other_trace("Except: %s" % str(e))
            translate_info = 'translate err'
        else:
            if len(self._translate_rules) == 0:
                translate_info = 'translate empty'

        check_info = 'check ok'
        try:
            with open(self._check_name) as _check_file:
                self._check_rules = json.loads(_check_file.read())
        except Exception as e:
            globaldefines.other_trace("Except: %s" % str(e))
            check_info = 'check err'
        else:
            if len(self._check_rules) == 0:
                check_info = 'check empty'

        support_info = translate_info + ' ' + check_info
        self.sig_support_done.emit(support_info)

        for file_path in self._get_file_paths():
            basetime = BaseTime(file_path, self._translate_rules, self._check_rules, self._thread)
            self._bases[file_path] = basetime
            basetime.sig_init.connect(self.sig_init)
            basetime.sig_uninit.connect(self.sig_uninit)
            basetime.sig_changed.connect(self.sig_changed)
            basetime.sig_changed.connect(self.write)
            basetime.start()

    def _check(self):
        globaldefines.other_trace('1')
        for basetime in self._bases.values():
            if len(basetime.errs) != 0 or len(basetime.items) == 0:
                globaldefines.other_trace('2')
                return False
        globaldefines.other_trace('3')
        return True

    def _write(self):
        globaldefines.other_trace()
        try:
            with open(self._object_name, 'wb') as file:
                # write version 4 Byte
                version = struct.pack('<BBBB', *globaldefines.output_version)
                file.write(version)

                # write file head 2 Byte
                file_head = struct.pack('<H', len(self._bases))
                file.write(file_head)

                # write list head
                list_head = bytes()
                content_addr = 6 + 10 * len(self._bases)
                for file_name, base_time in self._bases.items():
                    file_index = int(file_name[0:3])
                    list_head += struct.pack('<HII', file_index, content_addr, len(base_time.item_bytes))
                    content_addr += len(base_time.item_bytes)
                file.write(list_head)

                # write content
                for file_name, base_time in self._bases.items():
                    file.write(base_time.item_bytes)

            self.sig_write_done.emit('done')
        except FileNotFoundError:
            globaldefines.useroptrace("Except: File %s is not found." % self.ASSIST_FILE_NAME)
        except PermissionError:
            globaldefines.useroptrace("Except: You don't have permission to access the file %s." % self.ASSIST_FILE_NAME)
        except Exception as e:
            globaldefines.useroptrace("Except: %s" % str(e))

    def start(self):
        globaldefines.other_trace('1')
        self._clear()
        self._create()
        globaldefines.other_trace('2')

    def write(self):
        globaldefines.other_trace('1')
        if self._check():
            self._write()
        globaldefines.other_trace('2')

    def get_status(self, file_path):
        if file_path not in self._bases:
            return 'invalid'

        if len(self._bases[file_path].items) == 0 and len(self._bases[file_path].errs) == 0:
            return 'init'

        if len(self._bases[file_path].errs) != 0:
            return 'errs'

        return 'done'

    def get_info(self, file_path):
        if file_path not in self._bases:
            return ['invalid']

        if len(self._bases[file_path].items) == 0 and len(self._bases[file_path].errs) == 0:
            return ['init']

        if len(self._bases[file_path].errs) != 0:
            return self._bases[file_path].errs

        return self._bases[file_path].items


class BaseTime(QObject):
    sig_init = pyqtSignal(str)
    sig_uninit = pyqtSignal(str)
    sig_changed = pyqtSignal(str)
    sig_start = pyqtSignal()

    def __init__(self, file_path, translate_rules, check_rules, thread, parent=None):
        super(BaseTime, self).__init__(parent)
        self._file_path = file_path
        self._items = []
        self._errs = []
        self._item_bytes = bytes()
        self._all_translate_rules = translate_rules
        self._all_check_rules = check_rules
        self._mutex = QMutex(QMutex.Recursive)
        print(thread)
        if thread == None:
            globaldefines.other_trace('new')
            self._thread = QThread(parent)
            self._thread.start()
        else:
            globaldefines.other_trace('use old')
            self._thread = thread

        self.moveToThread(self._thread)
        self.sig_start.connect(self.slot_start)

    def __del__(self):
        self.sig_uninit.emit(self._file_path)
        super(BaseTime, self).__del__()

    def start(self):
        self.sig_start.emit()

    @property
    def file_path(self):
        return self._file_path

    @property
    def items(self):
        with QMutexLocker(self._mutex):
            return self._items

    @items.setter
    def items(self, items):
        with QMutexLocker(self._mutex):
            self._items = items

    @property
    def errs(self):
        with QMutexLocker(self._mutex):
            return self._errs

    @errs.setter
    def errs(self, errs):
        with QMutexLocker(self._mutex):
            self._errs = errs

    @property
    def item_bytes(self):
        with QMutexLocker(self._mutex):
            return self._item_bytes

    @item_bytes.setter
    def item_bytes(self, item_bytes):
        with QMutexLocker(self._mutex):
            self._item_bytes = item_bytes

    @pyqtSlot()
    def slot_start(self):
        globaldefines.other_trace()
        self.sig_init.emit(self._file_path)
        items, errs, item_bytes = self._phase()
        globaldefines.other_trace('\nitems:%s\nerrs:%s\nitemBytes:%d' % (str(items), str(errs), len(item_bytes)))
        with QMutexLocker(self._mutex):
            self.items = items
            self.errs = errs
            self.item_bytes = item_bytes
            self.sig_changed.emit(self._file_path)

    def _task_filter(self, task):
        cmdExclude = ['MPPVER', 'SUBVER']
        return '.' in task[ProjectFile.DESCRIPTION_CHAPTER] and task[ProjectFile.DESCRIPTION_CMD] not in cmdExclude

    def _task_sort(self, task):
        return task[ProjectFile.DESCRIPTION_STARTTIME]

    def _task_translate(self, task):
        if task[ProjectFile.DESCRIPTION_CMD] in self._all_translate_rules:
            self._translate_params(task, self._all_translate_rules[task[ProjectFile.DESCRIPTION_CMD]])
        return task

    def _task_check(self, task):
        if task[ProjectFile.DESCRIPTION_CMD] in self._all_check_rules:
            return self._check_params(task, self._all_check_rules[task[ProjectFile.DESCRIPTION_CMD]])
        else:
            return False

    def _translate_params(self, task, translaterules):
        task_copy = copy.deepcopy(task)

        def set_err_name():
            task[ProjectFile.DESCRIPTION_CMD] = task[ProjectFile.DESCRIPTION_CMD].strip().lower()

        def get_trans_param(param_name):
            return translaterules[param_name]

        def get_negative_param(param_name):
            return -task_copy[param_name]

        def get_duration_param(param_name):
            return task_copy[ProjectFile.DESCRIPTION_ENDTIME] - task_copy[ProjectFile.DESCRIPTION_STARTTIME]

        def get_lowbyte_param(param_name):
            return struct.unpack('<hh', struct.pack('<i', task_copy[param_name]))[0]

        def get_highbyte_param(param_name):
            if param_name == ProjectFile.DESCRIPTION_PARAM1:
                raise ValueError
            if param_name == ProjectFile.DESCRIPTION_PARAM2:
                return struct.unpack('<hh', struct.pack('<i', task_copy[ProjectFile.DESCRIPTION_PARAM1]))[1]
            if param_name == ProjectFile.DESCRIPTION_PARAM3:
                return struct.unpack('<hh', struct.pack('<i', task_copy[ProjectFile.DESCRIPTION_PARAM2]))[1]
            if param_name == ProjectFile.DESCRIPTION_PARAM4:
                return struct.unpack('<hh', struct.pack('<i', task_copy[ProjectFile.DESCRIPTION_PARAM3]))[1]

        _trans_param = \
            {
                'N': get_negative_param,
                'T': get_duration_param,
                'L': get_lowbyte_param,
                'H': get_highbyte_param,
            }

        try:
            if ProjectFile.DESCRIPTION_CMD in translaterules:
                task[ProjectFile.DESCRIPTION_CMD] = str(get_trans_param(ProjectFile.DESCRIPTION_CMD)).strip().upper()
            if ProjectFile.DESCRIPTION_PARAM1 in translaterules:
                task[ProjectFile.DESCRIPTION_PARAM1] = int(_trans_param.get(translaterules[ProjectFile.DESCRIPTION_PARAM1], get_trans_param)(ProjectFile.DESCRIPTION_PARAM1))
            if ProjectFile.DESCRIPTION_PARAM2 in translaterules:
                task[ProjectFile.DESCRIPTION_PARAM2] = int(_trans_param.get(translaterules[ProjectFile.DESCRIPTION_PARAM2], get_trans_param)(ProjectFile.DESCRIPTION_PARAM2))
            if ProjectFile.DESCRIPTION_PARAM3 in translaterules:
                task[ProjectFile.DESCRIPTION_PARAM3] = int(_trans_param.get(translaterules[ProjectFile.DESCRIPTION_PARAM3], get_trans_param)(ProjectFile.DESCRIPTION_PARAM3))
            if ProjectFile.DESCRIPTION_PARAM4 in translaterules:
                task[ProjectFile.DESCRIPTION_PARAM4] = int(_trans_param.get(translaterules[ProjectFile.DESCRIPTION_PARAM4], get_trans_param)(ProjectFile.DESCRIPTION_PARAM4))
        except Exception:
            set_err_name()

    def _check_params(self, task, checkrules):
        def _check_param(value, checkrule):
            matchs = re.match(r'(-?\d+):(-?\d+)', checkrule)
            if matchs:
                minvalue = int(matchs.group(1))
                maxvalue = int(matchs.group(2))
                return minvalue <= value <= maxvalue
            return False

        rtn = True
        if ProjectFile.DESCRIPTION_PARAM1 in checkrules:
            rtn = rtn and _check_param(task[ProjectFile.DESCRIPTION_PARAM1], checkrules[ProjectFile.DESCRIPTION_PARAM1])
        if ProjectFile.DESCRIPTION_PARAM2 in checkrules:
            rtn = rtn and _check_param(task[ProjectFile.DESCRIPTION_PARAM2], checkrules[ProjectFile.DESCRIPTION_PARAM2])
        if ProjectFile.DESCRIPTION_PARAM3 in checkrules:
            rtn = rtn and _check_param(task[ProjectFile.DESCRIPTION_PARAM3], checkrules[ProjectFile.DESCRIPTION_PARAM3])
        if ProjectFile.DESCRIPTION_PARAM4 in checkrules:
            rtn = rtn and _check_param(task[ProjectFile.DESCRIPTION_PARAM4], checkrules[ProjectFile.DESCRIPTION_PARAM4])
        return rtn

    def _process_tasks(self, tasks, errs):
        globaldefines.other_trace("_process_tasks 0")
        # do some filtration
        tasks[:] = list(filter(self._task_filter, tasks))
        globaldefines.other_trace("_process_tasks 1")

        # do some tranlation
        tasks[:] = list(map(self._task_translate, tasks))
        globaldefines.other_trace("_process_tasks 2")

        # sort and index
        tasks[:] = sorted(tasks, key=self._task_sort)
        globaldefines.other_trace("_process_tasks 3")

        # check
        if len(tasks) == 0:
            errs.append('empty')

        for task in tasks:
            if not self._task_check(task):
                errs.append(task)

        globaldefines.other_trace("_process_tasks 4")
        return tasks

    def _convert_to_bytes(self, tasks, errs):
        byte_temp = bytes()
        if len(errs) == 0:
            for task in tasks:
                try:
                    one_task_byte = bytes()
                    one_task_byte += struct.pack("8s", task[ProjectFile.DESCRIPTION_CMD].encode(encoding='utf-8'))
                    one_task_byte += struct.pack("<H", int(task[ProjectFile.DESCRIPTION_INDEX]))
                    one_task_byte += struct.pack("<H", int(task[ProjectFile.DESCRIPTION_STARTTIME]))
                    one_task_byte += struct.pack("<H", int(task[ProjectFile.DESCRIPTION_ENDTIME]))
                    one_task_byte += struct.pack("<h", int(task[ProjectFile.DESCRIPTION_PARAM1]))
                    one_task_byte += struct.pack("<h", int(task[ProjectFile.DESCRIPTION_PARAM2]))
                    one_task_byte += struct.pack("<h", int(task[ProjectFile.DESCRIPTION_PARAM3]))
                    one_task_byte += struct.pack("<h", int(task[ProjectFile.DESCRIPTION_PARAM4]))
                    checksum = 0
                    for byte in one_task_byte:
                        checksum += byte
                    one_task_byte += struct.pack("<H", int(checksum))
                    byte_temp += one_task_byte
                except Exception as e:
                    globaldefines.other_trace("Except: %s" % str(e))
                    errs.append(task)
                    errs.append(str(e))
                    byte_temp = bytes()
                    break
        return byte_temp

    def _phase(self):
        globaldefines.other_trace("_phase")
        tasks, errs = ProjectFile.get(self._file_path)
        self._process_tasks(tasks, errs)

        return tasks, errs, self._convert_to_bytes(tasks, errs)
