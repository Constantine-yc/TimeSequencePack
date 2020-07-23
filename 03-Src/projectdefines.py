# -*- coding: utf-8 -*-

from enum import IntEnum
import os
import inspect
from functools import reduce
from win32api import GetFileVersionInfo, LOWORD, HIWORD
from win32api import GetCommandLine, GetFileAttributes
import sys



class GlobalDefines:
    _model = ""
    _path = os.getcwd()
    _sw_name = ""
    _sw_version = ""
    _output_name = ""
    _output_version = [1, 0, 0, 0]
    _project_exe = None

    def __init__(self):
        try:
            run_file = sys.argv[0]
            info = self.getFileProperties(run_file)
            print(info)
            self._sw_name = info['StringFileInfo']['ProductName']
            self._sw_version = info['FileVersion']
        except Exception as e:
            self._sw_name = '时序编译工具'
            self._sw_version = 'V???'
            print("except:%s" % e)
        pass

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def sw_name(self):
        return self._sw_name

    @property
    def sw_version(self):
        return self._sw_version

    @property
    def output_name(self):
        return self._output_name

    @output_name.setter
    def output_name(self, output_name):
        self._output_name = output_name

    @property
    def output_version(self):
        return self._output_version

    def output_version_str(self):
        return reduce(lambda x, y: str(x) + '.' + str(y), self._output_version)

    @output_version.setter
    def output_version(self, version):
        if type(version) == list and len(version) == 4:
            self._output_version = version

    def get_exe(self):
        if not self._project_exe:
            self._project_exe = ProjectExe()
        return self._project_exe

    def release_exe(self):
        if self._project_exe:
            self._project_exe = None

    def useroptrace(self, log=''):
        if len(log) != 0:
            print('userop: %s : %s' % (inspect.stack()[1][3], log))
        else:
            print('userop: %s' % inspect.stack()[1][3])

    def other_trace(self, log=''):
        if len(log) != 0:
            print('other: %s:%s---%s:%s' % (inspect.stack()[1][3], log, inspect.stack()[1][1], inspect.stack()[1][2]))
        else:
            print('other: %s---%s:%s' % (inspect.stack()[1][3], inspect.stack()[1][1], inspect.stack()[1][2]))

    @staticmethod
    def getFileProperties(fname):
        """
        读取给定文件的所有属性, 返回一个字典.
        """
        propNames = ('Comments', 'InternalName', 'ProductName',
            'CompanyName', 'LegalCopyright', 'ProductVersion',
            'FileDescription', 'LegalTrademarks', 'PrivateBuild',
            'FileVersion', 'OriginalFilename', 'SpecialBuild')

        props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

        try:
            fixedInfo = GetFileVersionInfo(fname, '\\')
            props['FixedFileInfo'] = fixedInfo
            props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                    fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
                    fixedInfo['FileVersionLS'] % 65536)

            # \VarFileInfo\Translation returns list of available (language, codepage)
            # pairs that can be used to retreive string info. We are using only the first pair.
            lang, codepage = GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

            # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
            # two are language/codepage pair returned from above

            strInfo = {}
            for propName in propNames:
                strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
                ## print str_info
                strInfo[propName] = GetFileVersionInfo(fname, strInfoPath)

            props['StringFileInfo'] = strInfo
        except:
            pass

        return props

globaldefines = GlobalDefines()
