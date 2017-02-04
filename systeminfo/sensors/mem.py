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

System info related to memory.
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty
from PyQt5.QtCore import QObject
from PyQt5.QtQml  import qmlRegisterType

import psutil

from systeminfo.ui      import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.toolbox import bytesToText
from systeminfo.sensors.history import HistoryModel
from systeminfo.sensors.trigger import TriggerSingleton


LOGGER = logging.getLogger(__name__)


class MemInfo(QObject):
    "Contains memory information"

    updated               = pyqtSignal()
    vmemPercentChanged    = pyqtSignal(float)
    vmemAvailBytesChanged = pyqtSignal(int)
    vmemAvailTextChanged  = pyqtSignal('QString')
    swapmemPercentChanged = pyqtSignal(float)

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'MemInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vmemPercent    = 0
        self._vmemAvailBytes = 0
        self._vmemAvailText  = ""
        self._swapmemPercent = 0
        self._history = HistoryModel(nofCols=2,parent=self)
        TriggerSingleton.get().triggered.connect( self._onTriggered )

    @pyqtSlot(int)
    def _onTriggered(self,trigger):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return
        vmem    = psutil.virtual_memory()
        swapmem = psutil.swap_memory()
        LOGGER.info("MemInfo: {:5.1f}% vmem {:5.1f}% swapmem".format(vmem.percent,swapmem.percent))
        self._setVmemPercent( vmem.percent )
        self._setVmemAvailBytes( vmem.available )
        self._setVmemAvailText( bytesToText(float(vmem.available)) )
        self._setSwapmemPercent( swapmem.percent )
        self._history.pushData( vmem.percent, swapmem.percent )
        self.updated.emit()

    @pyqtProperty(float,notify=vmemPercentChanged)
    def vmemPercent(self):
        return self._vmemPercent

    def _setVmemPercent(self, percent):
        if percent != self._vmemPercent:
            self._vmemPercent = percent
            self.vmemPercentChanged.emit( self._vmemPercent )

    @pyqtProperty(int,notify=vmemAvailBytesChanged)
    def vmemAvailBytes(self):
        return self._vmemAvailBytes

    def _setVmemAvailBytes(self, availBytes):
        if availBytes != self._vmemAvailBytes:
            self._vmemAvailBytes = availBytes
            self.vmemAvailBytesChanged.emit( self._vmemAvailBytes )

    @pyqtProperty('QString',notify=vmemAvailTextChanged)
    def vmemAvailText(self):
        return self._vmemAvailText

    def _setVmemAvailText(self, availText):
        if availText != self._vmemAvailText:
            self._vmemAvailText = availText
            self.vmemAvailTextChanged.emit( self._vmemAvailText )

    @pyqtProperty(float,notify=swapmemPercentChanged)
    def swapmemPercent(self):
        return self._swapmemPercent

    def _setSwapmemPercent(self, percent):
        if percent != self._swapmemPercent:
            self._swapmemPercent = percent
            self.swapmemPercentChanged.emit( self._swapmemPercent )

    @pyqtProperty(HistoryModel,constant=True)
    def history(self):
        return self._history
