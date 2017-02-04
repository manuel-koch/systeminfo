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

System info related to network interfaces.
"""
import datetime
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty
from PyQt5.QtCore import QObject
from PyQt5.QtQml  import qmlRegisterType

import psutil

from systeminfo.ui      import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.toolbox import WorkerSingleton, bytesToText
from systeminfo.sensors.history import HistoryModel
from systeminfo.sensors.trigger import TriggerSingleton


LOGGER = logging.getLogger(__name__)


class NetworkInterfaceSingleton(QObject):
    "Contains network interface information singleton"

    updated           = pyqtSignal() # signal gets emitted whenever CPU load data has been updated
    interfacesChanged = pyqtSignal()
    ioChanged         = pyqtSignal(str,int,int) # signal gets emitted for recv bytes %2 and sent bytes %3 for selected network interface %1
                                                # empty interface = sum of all interfaces
    isUpChanged       = pyqtSignal(str,bool) # signal gets emitted for up-state of selected network interface %1

    instance = None

    @staticmethod
    def get():
        "Get singleton instance"
        if NetworkInterfaceSingleton.instance == None:
            NetworkInterfaceSingleton.instance = NetworkInterfaceSingleton()
            WorkerSingleton.get().registerSingleton( NetworkInterfaceSingleton.instance )
        return NetworkInterfaceSingleton.instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lastCounters  = None
        self._lastTimestamp = None
        self._interfaces    = []
        TriggerSingleton.get().triggered.connect( self._onTriggered )

    @pyqtSlot(int)
    def _onTriggered(self,trigger):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return
        now = datetime.datetime.now()
        stats = psutil.net_if_stats()
        for interface, stat in stats.items():
            self.isUpChanged.emit(interface,stat.isup)
        counters = psutil.net_io_counters(pernic=True)
        if self._lastCounters:
            dt = now - self._lastTimestamp
            allRecvBytes  = 0
            allSentBytes = 0
            for interface, counter in counters.items():
                if not interface in self._lastCounters:
                    continue
                recvBytes = int( (counter.bytes_recv - self._lastCounters[interface].bytes_recv) / dt.total_seconds() )
                sentBytes = int( (counter.bytes_sent - self._lastCounters[interface].bytes_sent) / dt.total_seconds() )
                allRecvBytes += recvBytes
                allSentBytes += sentBytes
                LOGGER.info("NetworkInterfaceSingleton: {:9d} recv, {:9d} sent for {}".format(recvBytes,sentBytes,interface))
                self.ioChanged.emit(interface,recvBytes,sentBytes)
            LOGGER.info("NetworkInterfaceSingleton: {:9d} recv, {:9d} sent for all".format(allRecvBytes,allSentBytes))
            self.ioChanged.emit("",allRecvBytes,allSentBytes)
        self._lastTimestamp = now
        self._lastCounters  = counters
        self._setInterfaces( list(stats.keys()) )

    @pyqtProperty('QStringList',notify=interfacesChanged)
    def interfaces(self):
        return self._interfaces

    def _setInterfaces(self, interfaces):
        if interfaces != self._interfaces:
            self._interfaces = interfaces
            self.interfacesChanged.emit()


class NetworkInterfacesInfo(QObject):
    "Contains network interfaces information"

    interfacesChanged = pyqtSignal()

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'NetworkInterfacesInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interfaces = []
        NetworkInterfaceSingleton.get().interfacesChanged.connect( self.interfacesChanged )

    @pyqtSlot(int)
    def _onTriggered(self,trigger=TriggerSingleton.TRIGGER_SLOW):
        if trigger != TriggerSingleton.TRIGGER_SLOW:
            return
        interfaces = list(psutil.net_if_addrs().keys())
        interfaces.sort( key=lambda k: k.lower() )
        self._setInterfaces( interfaces )

    @pyqtProperty('QStringList',notify=interfacesChanged)
    def interfaces(self):
        return NetworkInterfaceSingleton.get().interfaces


class NetworkInterfaceInfo(QObject):
    "Contains network interface information"

    nameChanged      = pyqtSignal(str)
    isUpChanged      = pyqtSignal(bool)
    isBusyChanged    = pyqtSignal(bool)
    recvBytesChanged = pyqtSignal(int)
    sentBytesChanged = pyqtSignal(int)
    recvTextChanged  = pyqtSignal(str)
    sentTextChanged  = pyqtSignal(str)

    @classmethod
    def registerToQml(cls):
        qmlRegisterType(cls, 'SystemInfo', 1, 0, 'NetworkInterfaceInfo')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._name      = "" # empty name refers to sum of all interfaces
        self._isUp      = False
        self._isBusy    = False
        self._recvBytes = 0
        self._recvText  = ""
        self._sentBytes = 0
        self._sentText  = ""
        self._history   = HistoryModel(nofCols=2,parent=self)
        NetworkInterfaceSingleton.get().ioChanged.connect(self._onIoChanged)
        NetworkInterfaceSingleton.get().isUpChanged.connect(self._onIsUpChanged)

    @pyqtSlot("QString",int,int)
    def _onIoChanged(self,name,recvBytes,sentBytes):
        if name != self._name:
            return
        self._setRecvBytes(recvBytes)
        self._setRecvText( "{}/sec".format(bytesToText(float(recvBytes))) )
        self._setSentBytes(sentBytes)
        self._setSentText( "{}/sec".format(bytesToText(float(sentBytes))) )
        self._setIsBusy( (recvBytes+sentBytes) != 0 )
        self._history.pushData( recvBytes, sentBytes )

    @pyqtSlot(str,bool)
    def _onIsUpChanged(self,name,isUp):
        if name != self._name:
            return
        self._setIsUp( isUp )

    @pyqtProperty(str,notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != self._name:
            self._name = name
            self.nameChanged.emit( self._name )

    @pyqtProperty(bool,notify=isUpChanged)
    def isUp(self):
        return self._isUp

    def _setIsUp(self, isup):
        if isup != self._isUp:
            self._isUp = isup
            self.isUpChanged.emit( self._isUp )

    @pyqtProperty(bool,notify=isBusyChanged)
    def isBusy(self):
        return self._isBusy

    def _setIsBusy(self, isBusy):
        if isBusy != self._isBusy:
            self._isBusy = isBusy
            self.isBusyChanged.emit( self.isBusy )

    @pyqtProperty(int,notify=recvBytesChanged)
    def recvBytes(self):
        return self._recvBytes

    def _setRecvBytes(self, recvBytes):
        if recvBytes != self._recvBytes:
            self._recvBytes = recvBytes
            self.recvBytesChanged.emit( self._recvBytes )

    @pyqtProperty(str,notify=recvTextChanged)
    def recvText(self):
        return self._recvText

    def _setRecvText(self, recvText):
        if recvText != self._recvText:
            self._recvText = recvText
            self.recvTextChanged.emit( self._recvText )

    @pyqtProperty(int,notify=sentBytesChanged)
    def sentBytes(self):
        return self._sentBytes

    def _setSentBytes(self, sentBytes):
        if sentBytes != self._sentBytes:
            self._sentBytes = sentBytes
            self.sentBytesChanged.emit( self._sentBytes )

    @pyqtProperty(str,notify=sentTextChanged)
    def sentText(self):
        return self._sentText

    def _setSentText(self, sentText):
        if sentText != self._sentText:
            self._sentText = sentText
            self.sentTextChanged.emit( self._sentText )

    @pyqtProperty(HistoryModel,constant=True)
    def history(self):
        return self._history
