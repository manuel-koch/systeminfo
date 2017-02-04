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

Main window of system info.
"""
import logging
import os

from PyQt5 import QtCore
from PyQt5.QtCore import qInstallMessageHandler, QSize, Qt, pyqtSlot
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QGuiApplication, QIcon, QPixmap, QPainter, QColor, QFont, QTextOption
from PyQt5.QtWidgets import QSystemTrayIcon
from PyQt5.QtQuick import QQuickView

from systeminfo.ui import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.ui.trayicon import CpuTrayIcon, VmemTrayIcon
from systeminfo.sensors.cpu import CpuInfo
from systeminfo.sensors.mem import MemInfo
from systeminfo.sensors.disk import PartitionsInfo, PartitionInfo, DisksInfo, DiskInfo
from systeminfo.sensors.network import NetworkInterfacesInfo, NetworkInterfaceInfo

LOGGER = logging.getLogger(__name__)


def messageHandler(msgType, context, msg):
    if msgType == QtCore.QtCriticalMsg or msgType == QtCore.QtFatalMsg:
        logfunc = LOGGER.error
    if msgType == QtCore.QtWarningMsg:
        logfunc = LOGGER.warning
    if msgType == QtCore.QtDebugMsg:
        logfunc = LOGGER.debug
    else:
        logfunc = LOGGER.info
    logfunc("{}({}): {}".format(context.file, context.line, msg))


class MainWindow(QQuickView):
    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot()
    def toggleVisiblity(self):
        if self.isVisible():
            self.setVisible(False)
        else:
            self.setVisible(True)


def run_gui():
    "Run GUI application"
    # Customize application
    app = QGuiApplication([])
    app.setOrganizationName("MKO")
    app.setOrganizationDomain("mko.systeminfo.com")
    app.setApplicationName("systeminfo")
    app.setWindowIcon(QIcon(':/icon.png'))
    QThread.currentThread().setObjectName('mainThread')

    qInstallMessageHandler(messageHandler)

    CpuInfo.registerToQml()
    MemInfo.registerToQml()
    PartitionsInfo.registerToQml()
    PartitionInfo.registerToQml()
    DisksInfo.registerToQml()
    DiskInfo.registerToQml()
    NetworkInterfacesInfo.registerToQml()
    NetworkInterfaceInfo.registerToQml()

    settings = QSettings()
    settings.beginGroup("MainWindow")
    x = settings.value("x")
    y = settings.value("y")
    w = settings.value("width", 300)
    h = settings.value("height", 600)
    settings.endGroup()

    view = MainWindow()
    view.engine().setOutputWarningsToStandardError(True)
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl('qrc:/qml/main.qml'));
    for err in view.errors():
        LOGGER.error("{}".format(err.toString()))
    view.setTitle("{}".format(app.applicationName()))
    view.setWidth(w)
    view.setHeight(h)
    if x is not None:
        view.setX(x)
    if y is not None:
        view.setY(y)
    view.show()

    memTrayIcon = VmemTrayIcon(view)
    memTrayIcon.show()
    memTrayIcon.activated.connect(view.toggleVisiblity)

    cpuTrayIcon = CpuTrayIcon(view)
    cpuTrayIcon.show()
    cpuTrayIcon.activated.connect(view.toggleVisiblity)

    # Run the application
    result = app.exec_()

    # cleanup tray icons
    cpuTrayIcon.hide()
    memTrayIcon.hide()

    settings = QSettings()
    settings.beginGroup("MainWindow")
    settings.setValue("x", view.x())
    settings.setValue("y", view.y())
    settings.setValue("width", view.width())
    settings.setValue("height", view.height())
    settings.endGroup()

    return result
