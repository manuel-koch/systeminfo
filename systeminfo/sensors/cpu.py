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

System info related to cpu.
"""
import datetime
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty
from PyQt5.QtCore import QObject
from PyQt5.QtQml  import qmlRegisterType

import psutil

from systeminfo.ui              import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.sensors.history import HistoryModel
from systeminfo.sensors.trigger import TriggerSingleton
from systeminfo.toolbox         import WorkerSingleton

LOGGER = logging.getLogger(__name__)


class CpuSingleton(QObject):
    "Contains cpu information singleton"

    updated     = pyqtSignal() # signal gets emitted whenever CPU load data has been updated
    loadChanged = pyqtSignal(int,float,float) # signal gets emitted for new cpu %1 load update in percent %2 and system percent %3
                                              # cpu 0 = avg of all CPUs
                                              # cpu 1 = 1st CPU
                                              # cpu 2 = 2nd CPU
    nofCpuChanged = pyqtSignal(int) # signal gets emitted for change of total number of CPUs
    nofProcChanged = pyqtSignal(int) # signal gets emitted for change of total number of processes

    instance = None

    @staticmethod
    def get():
        "Get singleton instance"
        if CpuSingleton.instance == None:
            CpuSingleton.instance = CpuSingleton()
            WorkerSingleton.get().registerSingleton( CpuSingleton.instance )
        return CpuSingleton.instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nofCpu  = 0
        self._nofProc = 0
        TriggerSingleton.get().triggered.connect( self._onTriggered )
        self._setNofCpu( len(psutil.cpu_times_percent(0.1, percpu=True)) )

    @pyqtSlot(int)
    def _onTriggered(self,trigger):
        if trigger != TriggerSingleton.TRIGGER_FAST:
            return
        cpuTimes = psutil.cpu_times_percent(percpu=True)
        usrLoads = [100-t.idle for t in cpuTimes]
        sysLoads = [t.system for t in cpuTimes]
        self._setNofCpu( len(cpuTimes) )
        usrLoads.insert(0, sum(usrLoads) / len(usrLoads))
        sysLoads.insert(0, sum(sysLoads) / len(sysLoads))
        for i in range(len(usrLoads)):
            u = usrLoads[i]
            s = sysLoads[i]
            LOGGER.info("CpuSingleton: [{}] {:5.1f}% {:5.1f}%".format(i,u,s))
            self.loadChanged.emit(i,u,s)
        self._setNofProc( len(psutil.pids()) )
        self.updated.emit()

    @pyqtProperty(int,notify=nofCpuChanged)
    def nofCpu(self):
        return self._nofCpu

    def _setNofCpu(self, nof):
        if self._nofCpu != nof:
            self._nofCpu = nof
            LOGGER.info("CpuSingleton: {} CPUs".format(self._nofCpu))
            self.nofCpuChanged.emit( self._nofCpu )

    @pyqtProperty(int,notify=nofProcChanged)
    def nofProc(self):
        return self._nofProc

    def _setNofProc(self, nof):
        if self._nofProc != nof:
            self._nofProc = nof
            LOGGER.info("CpuSingleton: {} Processes".format(self._nofProc))
            self.nofProcChanged.emit( self._nofProc )


class CpuInfo(QObject):
    "Contains cpu information"

    updated           = pyqtSignal()
    nofCpuChanged     = pyqtSignal(int)
    cpuChanged        = pyqtSignal(int)
    percentChanged    = pyqtSignal(float)
    percentSysChanged = pyqtSignal(float)
    nofProcChanged    = pyqtSignal(int)

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'CpuInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        CpuSingleton.get().updated.connect( self.updated )
        CpuSingleton.get().nofCpuChanged.connect( self.nofCpuChanged )
        CpuSingleton.get().nofProcChanged.connect( self.nofProcChanged )
        CpuSingleton.get().nofProcChanged.connect( self._onNofProcChanged )
        CpuSingleton.get().loadChanged.connect( self._onLoadChanged )
        self._cpu         = 0
        self._percent     = 0
        self._percentSys  = 0
        self._cpuHistory  = HistoryModel(nofCols=2,parent=self)
        self._procHistory = HistoryModel(nofCols=1,parent=self)

    @pyqtSlot(int,float,float)
    def _onLoadChanged(self,cpu,usrPercent,sysPercent):
        if cpu != self._cpu:
            return
        self._setPercent(usrPercent)
        self._setPercentSys(sysPercent)
        self._cpuHistory.pushData( usrPercent, sysPercent )

    @pyqtSlot(int)
    def _onNofProcChanged(self,nof):
        self._procHistory.pushData( nof )

    @pyqtProperty(float,notify=nofCpuChanged)
    def nofCpu(self):
        return CpuSingleton.get().nofCpu

    @pyqtProperty(int,notify=cpuChanged)
    def cpu(self):
        return self._cpu

    @cpu.setter
    def cpu(self,i):
        if self._cpu != i:
            self._cpu = i
            self.cpuChanged.emit(self._cpu)

    @pyqtProperty(float,notify=percentChanged)
    def percent(self):
        return self._percent

    def _setPercent(self, percent):
        if self._percent != percent:
            self._percent = percent
            self.percentChanged.emit( self._percent )

    @pyqtProperty(float,notify=percentSysChanged)
    def percentSys(self):
        return self._percentSys

    def _setPercentSys(self, percent):
        if self._percentSys != percent:
            self._percentSys = percent
            self.percentSysChanged.emit( self._percentSys )

    @pyqtProperty(int,notify=nofProcChanged)
    def nofProc(self):
        return CpuSingleton.get().nofProc

    @pyqtProperty(HistoryModel,constant=True)
    def cpuHistory(self):
        return self._cpuHistory

    @pyqtProperty(HistoryModel,constant=True)
    def procHistory(self):
        return self._procHistory
