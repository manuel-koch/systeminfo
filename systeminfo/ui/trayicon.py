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

Tray icons with system information.
"""
import logging
import datetime

from PyQt5.QtCore    import QSize, Qt, pyqtSlot
from PyQt5.QtGui     import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtWidgets import QSystemTrayIcon

from systeminfo.ui           import resources  # @UnusedImport Only need this to get access to embedded Qt resources
from systeminfo.sensors.cpu  import CpuInfo
from systeminfo.sensors.mem  import MemInfo


LOGGER = logging.getLogger(__name__)


TRAY_ICON_SIZE = 16 # assuming tray icon of 16x16 pixels


class PercentTrayIcon(QSystemTrayIcon):

    def __init__(self,title,color,parent=None):
        "Construct a tray icon that updates when a percentage value changes, using selected named color for graph"
        super().__init__(parent)
        self._history = [(0,0)]*TRAY_ICON_SIZE
        self._color = QColor(color)
        self._render()
        self.setToolTip(title)

    def _addPercentage(self,percent):
        "Add a new percentage value ( 0...100 ) to history of values, only using the first value within a second"
        now = int( datetime.datetime.now().timestamp() + 0.5 )
        if now == self._history[-1][0]:
            return
        self._history.pop(0)
        self._history.append( (now,percent) )
        self._render()

    def _render(self):
        "Render new tray icon and apply it to system tray"
        pixmap = QPixmap(QSize(TRAY_ICON_SIZE,TRAY_ICON_SIZE))
        painter = QPainter(pixmap)
        painter.fillRect( pixmap.rect(), Qt.black )
        painter.setPen( self._color )
        s = TRAY_ICON_SIZE-1
        for x, data in enumerate(self._history):
            y = data[1]
            painter.drawLine(x,s,x,s-int(y*s/100+0.5))
        if self._history:
            y = self._history[-1][1]
            painter.setPen(QColor("white"))
            painter.setFont( QFont("monospace",pointSize=7) )
            painter.drawText( pixmap.rect(), Qt.AlignCenter|Qt.AlignVCenter, "{:0.0f}".format(y) )
        painter.end() # disconnect painter from pixmap to be able to create icon from pixmap
        self.setIcon(QIcon(pixmap))


class CpuTrayIcon(PercentTrayIcon):

    def __init__(self,parent=None):
        "Construct a tray icon that updates when CPU load changes"
        super().__init__("CPU %","lightgreen",parent)
        self._cpuInfo = CpuInfo()
        self._cpuInfo.updated.connect( self._onUpdated )

    @pyqtSlot()
    def _onUpdated(self):
        "Handle change of CPU load"
        self._addPercentage( self._cpuInfo.percent )


class VmemTrayIcon(PercentTrayIcon):

    def __init__(self,parent=None):
        "Construct a tray icon that updates when avail virtual memory changes"
        super().__init__("VMem %","#ff8080",parent)
        self._memInfo = MemInfo()
        self._memInfo.updated.connect( self._onUpdated )

    @pyqtSlot()
    def _onUpdated(self):
        "Handle change of virtual memory"
        self._addPercentage( self._memInfo.vmemPercent )
