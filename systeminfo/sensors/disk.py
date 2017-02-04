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

System info related to disks / partitions.
"""
import datetime
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty
from PyQt5.QtCore import QObject
from PyQt5.QtQml  import qmlRegisterType

import psutil

from systeminfo.ui              import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.toolbox         import bytesToText, WorkerSingleton
from systeminfo.sensors.history import HistoryModel
from systeminfo.sensors.trigger import TriggerSingleton


LOGGER = logging.getLogger(__name__)


class PartitionsInfo(QObject):
    "Contains partitions information"

    pathsChanged = pyqtSignal()

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'PartitionsInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = []
        TriggerSingleton.get().triggered.connect( self._onTriggered )
        self._onTriggered()

    @pyqtSlot(int)
    def _onTriggered(self,trigger=TriggerSingleton.TRIGGER_SLOW):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return
        paths = [partition.mountpoint for partition in psutil.disk_partitions()]
        paths.sort( key=lambda k: k.lower() )
        self._setPaths( paths )

    @pyqtProperty('QStringList',notify=pathsChanged)
    def paths(self):
        return self._paths

    def _setPaths(self, paths):
        if paths != self._paths:
            self._paths = paths
            self.pathsChanged.emit()


class PartitionInfo(QObject):
    "Contains partition information"

    pathChanged      = pyqtSignal('QString')
    diskChanged      = pyqtSignal('QString')
    percentChanged   = pyqtSignal(float)
    availChanged     = pyqtSignal(bool)
    freeBytesChanged = pyqtSignal(int)
    freeTextChanged  = pyqtSignal('QString')

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'PartitionInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path      = ""
        self._disk      = ""
        self._percent   = 0
        self._avail     = False
        self._freeBytes = 0
        self._freeText  = ""
        TriggerSingleton.get().triggered.connect( self._onTriggered )

    @pyqtSlot(int)
    def _onTriggered(self,trigger):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return

        if sys.platform == "win32" or sys.platform == "cygwin":
            # need to disable special windows error handling that causes a popup dialog
            # when drive has been ejected and we try to access it ( e.g. via isdir call ).
            import win32api
            oldError = win32api.SetErrorMode( 1 ) # SEM_FAILCRITICALERRORS = 1
            pathValid = os.path.isdir(self._path)
            win32api.SetErrorMode( oldError )
        else:
            pathValid = os.path.isdir(self._path)

        if not pathValid:
            self._setPercent( 0 )
            self._setAvail(False)
            return
        try:
            usage = psutil.disk_usage(self._path)
            LOGGER.info("PartitionInfo: [{}] {:5.1f}%".format(self._path,usage.percent))
            self._setPercent( usage.percent )
            self._setFreeBytes( usage.free )
            self._setAvail(True)
            self._setFreeText( bytesToText(float(usage.free)) )
        except FileNotFoundError:
            self._setPercent( 0 )
            self._setAvail(False)

    @pyqtProperty('QString',notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        if path != self._path:
            self._path = path
            self.pathChanged.emit( self._path )
            partition = [p for p in psutil.disk_partitions() if p.mountpoint == self._path][0]
            self._setDisk( partition.device )

    @pyqtProperty('QString',notify=diskChanged)
    def disk(self):
        return self._disk

    def _setDisk(self, disk):
        if disk != self._disk:
            self._disk = disk
            self.diskChanged.emit( self._disk )

    @pyqtProperty(float,notify=percentChanged)
    def percent(self):
        return self._percent

    def _setPercent(self, percent):
        if percent != self._percent:
            self._percent = percent
            self.percentChanged.emit( self._percent )

    @pyqtProperty(bool,notify=availChanged)
    def avail(self):
        return self._avail

    def _setAvail(self, avail):
        if avail != self._avail:
            self._avail = avail
            self.availChanged.emit( self._avail )

    @pyqtProperty(int,notify=freeBytesChanged)
    def freeBytes(self):
        return self._freeBytes

    def _setFreeBytes(self, freeBytes):
        if freeBytes != self._freeBytes:
            self._freeBytes = freeBytes
            self.freeBytesChanged.emit( self._freeBytes )

    @pyqtProperty('QString',notify=freeTextChanged)
    def freeText(self):
        return self._freeText

    def _setFreeText(self, freeText):
        if freeText != self._freeText:
            self._freeText = freeText
            self.freeTextChanged.emit( self._freeText )


class DiskSingleton(QObject):
    "Contains disk information singleton"

    updated      = pyqtSignal() # signal gets emitted whenever disk data has been updated
    disksChanged = pyqtSignal('QStringList') # signal gets emitted whenever list of disks has been updated
    ioChanged    = pyqtSignal("QString",int,int) # signal gets emitted for read bytes %2 and write bytes %3 for selected disk %1
                                                 # empty disk = sum of all disks

    instance = None

    @staticmethod
    def get():
        "Get singleton instance"
        if DiskSingleton.instance == None:
            DiskSingleton.instance = DiskSingleton()
            WorkerSingleton.get().registerSingleton( DiskSingleton.instance )
        return DiskSingleton.instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lastCounters  = None
        self._lastTimestamp = None
        self._disks         = []
        TriggerSingleton.get().triggered.connect( self._onTriggered )

    @pyqtSlot(int)
    def _onTriggered(self,trigger):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return

        now = datetime.datetime.now()
        counters = psutil.disk_io_counters(perdisk=True)

        disks = list( counters.keys() )
        disks.sort(key=lambda d: d.lower())
        if self._disks != disks:
            self._disks = disks
            LOGGER.info("DiskSingleton: Disks {}".format(", ".join(self._disks)))
            self.disksChanged.emit( self._disks )

        if self._lastCounters:
            dt = now - self._lastTimestamp
            allReadBytes  = 0
            allWriteBytes = 0
            for disk, counter in counters.items():
                if not disk in self._lastCounters:
                    continue
                readBytes  = int( (counter.read_bytes - self._lastCounters[disk].read_bytes) / dt.total_seconds() )
                writeBytes = int( (counter.write_bytes - self._lastCounters[disk].write_bytes) / dt.total_seconds() )
                allReadBytes  += readBytes
                allWriteBytes += writeBytes
                LOGGER.info("DiskSingleton: {:9d} read, {:9d} write for {}".format(readBytes,writeBytes,disk))
                self.ioChanged.emit(disk,readBytes,writeBytes)
            LOGGER.info("DiskSingleton: {:9d} read, {:9d} write for all".format(allReadBytes,allWriteBytes))
            self.ioChanged.emit("",allReadBytes,allWriteBytes)
            self.updated.emit()

        self._lastTimestamp = now
        self._lastCounters  = counters


class DisksInfo(QObject):
    "Contains disks information"

    disksChanged    = pyqtSignal()
    nofDisksChanged = pyqtSignal(int)

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'DisksInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disks = []
        DiskSingleton.get().disksChanged.connect( self._setDisks )

    @pyqtProperty(int,notify=nofDisksChanged)
    def nofDisks(self):
        return len(self._disks)

    @pyqtProperty('QStringList',notify=disksChanged)
    def disks(self):
        return self._disks

    def _setDisks(self, disks):
        if disks != self._disks:
            self._disks = disks
            LOGGER.info("DisksInfo {}".format(disks))
            self.disksChanged.emit()
            self.nofDisksChanged.emit(len(self._disks))


class DiskInfo(QObject):
    "Contains disk information"

    diskChanged       = pyqtSignal('QString')
    isBusyChanged     = pyqtSignal(bool)
    readBytesChanged  = pyqtSignal(int)
    writeBytesChanged = pyqtSignal(int)
    readTextChanged   = pyqtSignal('QString')
    writeTextChanged  = pyqtSignal('QString')

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'DiskInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disk       = "" # empty disk refers to sum of all disks
        self._isBusy     = False
        self._readBytes  = 0
        self._readText   = ""
        self._writeBytes = 0
        self._writeText  = ""
        self._history    = HistoryModel(nofCols=2,parent=self)
        DiskSingleton.get().ioChanged.connect(self._onIoChanged)

    @pyqtSlot("QString",int,int)
    def _onIoChanged(self,disk,readBytes,writeBytes):
        if disk != self._disk:
            return
        self._setReadBytes(readBytes)
        self._setReadText( "{}/sec".format(bytesToText(float(readBytes))) )
        self._setWriteBytes(writeBytes)
        self._setWriteText( "{}/sec".format(bytesToText(float(writeBytes))) )
        self._setIsBusy( (readBytes+writeBytes) != 0 )
        self._history.pushData( readBytes, writeBytes )

    @pyqtProperty('QString',notify=diskChanged)
    def disk(self):
        return self._disk

    @disk.setter
    def disk(self, disk):
        if disk != self._disk:
            self._disk = disk
            self.diskChanged.emit( self._disk )

    @pyqtProperty(bool,notify=isBusyChanged)
    def isBusy(self):
        return self._isBusy

    def _setIsBusy(self, isBusy):
        if isBusy != self._isBusy:
            self._isBusy = isBusy
            self.isBusyChanged.emit( self.isBusy )

    @pyqtProperty(int,notify=readBytesChanged)
    def readBytes(self):
        return self._readBytes

    def _setReadBytes(self, readBytes):
        if readBytes != self._readBytes:
            self._readBytes = readBytes
            self.readBytesChanged.emit( self._readBytes )

    @pyqtProperty('QString',notify=readTextChanged)
    def readText(self):
        return self._readText

    def _setReadText(self, readText):
        if readText != self._readText:
            self._readText = readText
            self.readTextChanged.emit( self._readText )

    @pyqtProperty(int,notify=writeBytesChanged)
    def writeBytes(self):
        return self._writeBytes

    def _setWriteBytes(self, writeBytes):
        if writeBytes != self._writeBytes:
            self._writeBytes = writeBytes
            self.writeBytesChanged.emit( self._writeBytes )

    @pyqtProperty('QString',notify=writeTextChanged)
    def writeText(self):
        return self._writeText

    def _setWriteText(self, writeText):
        if writeText != self._writeText:
            self._writeText = writeText
            self.writeTextChanged.emit( self._writeText )

    @pyqtProperty(HistoryModel,constant=True)
    def history(self):
        return self._history
