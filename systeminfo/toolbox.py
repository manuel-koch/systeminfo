# -*- coding: utf-8 -*-
"""
This file is part of Systeminfo.

Systeminfo is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Systeminfo is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Systeminfo. If not, see <http://www.gnu.org/licenses/>.

Copyright 2017 Manuel Koch

----------------------------
Helper functions.
"""
import datetime
import inspect

from PyQt5.QtCore import QObject, QThread


class MeasureContext(object):
    "Measure time spent in current scope"

    def __init__(self,msg):
        self._msg   = msg
        self._start = None
        self._end   = None

    def __enter__(self):
        "Enter context"
        self._start = datetime.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        "Leave context"
        self._end = datetime.datetime.now()
        dt = self._end - self._start
        print("{}: {}".format(self._msg,dt))
        return False


class WorkerSingleton(QObject):

    instance = None

    @staticmethod
    def get():
        "Get singleton instance"
        if WorkerSingleton.instance == None:
            WorkerSingleton.instance = WorkerSingleton()
        return WorkerSingleton.instance

    def __init__(self):
        self._worker = QThread()
        self._worker.setObjectName("WorkerSingleton")
        self._worker.start()

    def registerSingleton(self,obj):
        obj.moveToThread(self._worker)


def bytesToText(num):
    units = ["B","KB","MB","GB"]
    while num > 1024:
        num /= 1024
        units.pop(0)
    return "{:0.2f} {}".format(num,units[0])
