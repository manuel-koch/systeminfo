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

Using timer singleton to sync updates of sensors.
"""
import logging

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from systeminfo.toolbox import WorkerSingleton


LOGGER = logging.getLogger(__name__)


class TriggerSingleton(QObject):
    "A timer to sync updates of sensors"

    TRIGGER_FAST = 1
    TRIGGER_MED  = 4
    TRIGGER_SLOW = 8
    ALL_TRIGGERS = ( TRIGGER_FAST, TRIGGER_MED, TRIGGER_SLOW )

    triggered = pyqtSignal(int) # signal gets emitted frequently with given trigger identifier

    instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = -1
        self._refreshTimer = QTimer(self)
        self._refreshTimer.setSingleShot(False)
        self._refreshTimer.setInterval(200)
        self._refreshTimer.start()
        self._refreshTimer.timeout.connect( self._onTriggered )

    @staticmethod
    def get():
        "Get singleton instance"
        if TriggerSingleton.instance == None:
            TriggerSingleton.instance = TriggerSingleton()
            WorkerSingleton.get().registerSingleton( TriggerSingleton.instance )
        return TriggerSingleton.instance

    @pyqtSlot()
    def _onTriggered(self):
        self._count += 1
        for t in TriggerSingleton.ALL_TRIGGERS:
            if self._count % t == 0:
                self.triggered.emit(t)
