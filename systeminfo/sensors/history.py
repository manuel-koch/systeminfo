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

Data model for history of system sensor values.
"""
import datetime
import logging

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal
from PyQt5.QtCore import QAbstractItemModel


LOGGER = logging.getLogger(__name__)


class HistoryModel(QAbstractItemModel):
    """Model of history data arranged in rows, where column 0 is the timestamp ( sec since epoch )
    and following columns are data.
    """

    durationChanged = pyqtSignal(int)

    def __init__(self, duration=60, nofCols=1, parent=None):
        """Construct  history model, keeping max number of seconds of recent pushed data and
        given number of data columns. Use tuple of defaultValues to initialize history in the past."""
        super().__init__(parent)
        self._rows     = []
        self._duration = duration
        self._columns  = nofCols

    def pushData(self,*dataColumns):
        assert len(dataColumns) == self._columns
        self.beginResetModel()
        while self._rows and self._rows[0][0] + self._duration < self._rows[-1][0]:
            self._rows.pop( 0 )
        self._rows.append( (datetime.datetime.now().timestamp(),) + dataColumns )
        self.endResetModel()

    def index(self,row,col,parent=None):
        return self.createIndex(row,col)

    def rowCount(self,parent=None):
        return len(self._rows)

    def columnCount(self,idx):
        if self._rows:
            return len(self._rows[0])
        return 0

    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid():
            return None
        if idx.row() >= len(self._rows):
            return None
        row = self._rows[idx.row()]
        if idx.column() >= len(row):
            return None
        if role == Qt.DisplayRole:
            return row[idx.column()]

    @pyqtProperty(int,notify=durationChanged)
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, secs):
        if secs != self._duration:
            self._duration = secs
            self.durationChanged.emit( self._duration )
