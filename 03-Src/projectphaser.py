# -*- coding: utf-8 -*-
import os
import pythoncom
import win32com.client
from enum import IntEnum
from projectdefines import globaldefines
from PyQt5.QtCore import QMutex, QMutexLocker


class ProjectExe:
    def __init__(self):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        self._project_exe = win32com.client.DispatchEx("MSProject.Application")
        self._project_exe.Visible = False
        self._project_exe.DisplayAlerts = False
        self._project_exe.FileCloseAllEx(Save=0)

    def __del__(self):
        self._project_exe.FileCloseAllEx(Save=0)
        self._project_exe.Quit(SaveChanges=0)
        pythoncom.CoUninitialize()

    def get_tasks(self, path):
        if self._project_exe.FileOpenEx(Name=path, ReadOnly=True):
            return self._project_exe.Projects.item(path).tasks
        else:
            return []


class State(IntEnum):
        Init = 0,
        CoInitialize = 1,
        DispatchEx = 2,
        FileOpenEx = 3,
        Done = 4


class ProjectFile:
    DESCRIPTION_INDEX = 'index'
    DESCRIPTION_CHAPTER = 'chapter'
    DESCRIPTION_STARTTIME = 'start_time'
    DESCRIPTION_ENDTIME = 'end_time'
    DESCRIPTION_CMD = 'cmd'
    DESCRIPTION_PARAM1 = 'p1'
    DESCRIPTION_PARAM2 = 'p2'
    DESCRIPTION_PARAM3 = 'p3'
    DESCRIPTION_PARAM4 = 'p4'

    @staticmethod
    def get(file_name):
        path = os.path.join(globaldefines.path, file_name)
        tasks = []
        errs = []
        try:
            state = State.Init
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            state = State.CoInitialize
            globaldefines.other_trace('%s get state = %s' % (file_name, state))

            project_exe = win32com.client.DispatchEx("MSProject.Application")
            project_exe.Visible = False
            project_exe.DisplayAlerts = False
            state = State.DispatchEx
            globaldefines.other_trace('%s get state = %s' % (file_name, state))

            project_exe.FileOpenEx(Name=path, ReadOnly=True)
            count = project_exe.Projects.count
            project_tasks = project_exe.Projects.item(path).tasks
            state = State.FileOpenEx
            globaldefines.other_trace('%s get state = %s(%s)' % (file_name, state, str(count)))

            for project_task in project_tasks:
                task = {
                    ProjectFile.DESCRIPTION_INDEX: str(project_task.ID)
                    , ProjectFile.DESCRIPTION_CHAPTER: str(project_task.WBS)
                    , ProjectFile.DESCRIPTION_STARTTIME: round(float('%.2f' % project_task.Number6) * 100)
                    , ProjectFile.DESCRIPTION_ENDTIME: round(float('%.2f' % project_task.Number7) * 100)
                    , ProjectFile.DESCRIPTION_CMD: str(project_task.Name).strip().upper()
                    , ProjectFile.DESCRIPTION_PARAM1: int(project_task.Number1)
                    , ProjectFile.DESCRIPTION_PARAM2: int(project_task.Number2)
                    , ProjectFile.DESCRIPTION_PARAM3: int(project_task.Number3)
                    , ProjectFile.DESCRIPTION_PARAM4: int(project_task.Number4)}
                tasks.append(task)
            state = State.Done
            globaldefines.other_trace('%s get state = %s\n\t%s' % (file_name, state, str(tasks)))
        except Exception as e:
            globaldefines.other_trace("Except: other except %s" % str(e))
            if state >= State.FileOpenEx:
                errs.append('file read error')
            elif state >= State.DispatchEx:
                errs.append('project open error')
            elif state >= State.CoInitialize:
                errs.append('init com environment fail')
        except BaseException as e:
            globaldefines.other_trace("Except: other except %s" % str(e))
            raise e
        finally:
            globaldefines.other_trace("%s get finally state = %s" % (file_name, state))
            if state >= State.FileOpenEx:
                project_exe.FileCloseEx(Save=0)

            if state >= State.DispatchEx:
                project_exe.Quit(SaveChanges=0)

            if state >= State.CoInitialize:
                pythoncom.CoUninitialize()
        globaldefines.other_trace("%s get return" % file_name)
        return tasks, errs

