// This file is part of Systeminfo.
//
// Systeminfo is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Systeminfo is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Systeminfo. If not, see <http://www.gnu.org/licenses/>.
//
// Copyright 2017 Manuel Koch
//
import QtQuick 2.5
import QtQuick.Layouts 1.2
import SystemInfo 1.0

Rectangle {
    id: root
    anchors.fill: parent
    color:        "silver"

    property real barHeight: 16

    ColumnLayout {
        anchors.fill: parent
        spacing:      0

        PercentSensor {
            id: theAllCpuSensor
            percent:                cpuInfo.percent
            label:                  "CPU"
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight
        }

        HistoryGraph {
            id: theCpuHistory
            Layout.fillWidth:  true
            Layout.fillHeight: true
            model:             cpuInfo.cpuHistory
            lineColors:        ["#bbbbff","#ffbbbb"]
            autoYRange:        false
            minYData:          0
            maxYData:          100
            showMinLabel:      false
            unitTxts:          [{"min":0, "max":100, "unit":"%"}]
        }

        Item {
            Layout.fillWidth:       true
            Layout.preferredHeight: 4
        }

        Repeater {
            model: cpuInfo.nofCpu
            PercentSensor {
                id: theCpuSensor
                percent:                curCpuInfo.percent
                showValue:              false
                Layout.fillWidth:       true
                Layout.preferredHeight: root.barHeight/2
                CpuInfo {
                    id: curCpuInfo
                    cpu: index+1
                }
            }
        }

        Item {
            Layout.fillWidth:       true
            Layout.preferredHeight: 4
        }

        HistoryGraph {
            id: theProcHistory
            Layout.fillWidth:  true
            Layout.fillHeight: true
            model:             cpuInfo.procHistory
            discrete:          true
            autoYRangeZero:    false
            lineColors:        ["#bbbbff"]
            unitTxts:          [ {"min":0,   "max":100,  "ticks": 10},
                                 {"min":100, "max":1000, "ticks": 25} ]
            Text {
                id: theProcText
                anchors.left:       parent.left
                anchors.leftMargin: 2
                text:               "Processes: "+cpuInfo.nofProc
                color:              "white"
            }
        }

        Item {
            Layout.fillWidth:       true
            Layout.preferredHeight: 4
        }

        PercentSensor {
            id: theVmemSensor
            percent:                memInfo.vmemPercent
            label:                  "Virtual Mem"
            postfix:                ", " + memInfo.vmemAvailText + " avail"
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight
            txtColor:               (memInfo.vmemPercent >= 95 && syncedAlarmTimer.highlight) ? "red" : normalTxtColor
            property color normalTxtColor: "#bbbbff"
        }

        PercentSensor {
            id: theSwapmemSensor
            percent:                memInfo.swapmemPercent
            label:                  "Swap Mem"
            txtColor:               (memInfo.swapmemPercent >= 95 && syncedAlarmTimer.highlight) ? "red" : normalTxtColor
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight
            property color normalTxtColor: "#ffbbbb"
        }

        HistoryGraph {
            id: theMemHistory
            Layout.fillWidth:  true
            Layout.fillHeight: true
            model:             memInfo.history
            discrete:          true
            lineColors:        [theVmemSensor.normalTxtColor,theSwapmemSensor.normalTxtColor]
            autoYRange:        false
            minYData:          0
            maxYData:          100
            showMinLabel:      false
            unitTxts:          [{"min":0, "max":100, "unit":"%"}]
        }

        Item {
            Layout.fillWidth:       true
            Layout.preferredHeight: 4
        }

        Repeater {
            model: netInterfaces.interfaces.length
            Rectangle {
                Layout.fillWidth:       true
                Layout.preferredHeight: root.barHeight
                color:                  "black"
                visible:                netInfo.isUp
                NetworkInterfaceInfo {
                    id: netInfo
                    name: netInterfaces.interfaces[index]
                }
                RowLayout {
                    anchors.fill: parent
                    Text {
                        id: netIfLabel
                        Layout.fillHeight:   true
                        Layout.fillWidth:    true
                        Layout.leftMargin:   2
                        text:                "Interface : "+netInfo.name
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment:   Text.AlignVCenter
                        color:               "white"
                    }
                    Rectangle {
                        Layout.alignment:       Qt.AlignVCenter
                        Layout.preferredHeight: 6
                        Layout.preferredWidth:  6
                        Layout.rightMargin:     5
                        radius:                 width/2
                        color:                  netInfo.recvBytes ? "magenta" : "transparent"
                    }
                    Rectangle {
                        Layout.alignment:       Qt.AlignVCenter
                        Layout.preferredHeight: 6
                        Layout.preferredWidth:  6
                        Layout.rightMargin:     5
                        radius:                 width/2
                        color:                  netInfo.sentBytes ? "lightgreen" : "transparent"
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight
            color:                  "black"
            RowLayout {
                anchors.fill: parent
                Text {
                    id: netIoLabel
                    Layout.fillHeight:   true
                    Layout.leftMargin:   2
                    Layout.rightMargin:  5
                    text:                "Net IO:"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                    color:               "white"
                }
                Text {
                    id: netIoRecv
                    Layout.preferredWidth: parent.width/3
                    Layout.fillHeight:     true
                    text:                  "RX "+netInfoAll.recvText
                    verticalAlignment:     Text.AlignVCenter
                    color:                 "magenta"
                }
                Text {
                    id: netIoSend
                    Layout.preferredWidth: parent.width/3
                    Layout.fillHeight:     true
                    text:                  "TX "+netInfoAll.sentText
                    verticalAlignment:     Text.AlignVCenter
                    color:                 "lightgreen"
                }
            }
        }

        HistoryGraph {
            id: theNetIoHistory
            Layout.fillWidth:  true
            Layout.fillHeight: true
            model:             netInfoAll.history
            discrete:          true
            showMinLabel:      false
            lineColors:        [netIoRecv.color,netIoSend.color]
            unitTxts:          [ {"min":0,            "max":1024,           "factor":1,           "unit":"B/sec",  "ticks": 256},
                                 {"min":1024,         "max":1024*1024,      "factor":1/1024,      "unit":"KB/sec", "ticks": 32*1024},
                                 {"min":1024*1024,    "max":20*1024*1024,   "factor":1/1024/1024, "unit":"MB/sec", "ticks": 1*1024*1024},
                                 {"min":20*1024*1024, "max":1024*1024*1024, "factor":1/1024/1024, "unit":"MB/sec", "ticks": 5*1024*1024}]
        }

        Item {
            Layout.fillWidth:       true
            Layout.preferredHeight: 4
        }

        Item {
            id: disksContainer
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight*diskRepeater.count
            Column {
                anchors.fill: parent
                spacing:      0
                Repeater {
                    id: diskRepeater
                    model: disksInfo.nofDisks
                    Rectangle {
                        width:  disksContainer.width
                        height: root.barHeight
                        color:  "black"
                        DiskInfo {
                            id: diskInfo
                            disk: disksInfo.disks[index]
                        }
                        RowLayout {
                            anchors.fill: parent
                            Text {
                                id: diskLabel
                                Layout.fillHeight:   true
                                Layout.fillWidth:    true
                                Layout.leftMargin:   2
                                text:                "Disk : "+diskInfo.disk
                                horizontalAlignment: Text.AlignLeft
                                verticalAlignment:   Text.AlignVCenter
                                color:               "white"
                            }
                            Rectangle {
                                Layout.alignment:       Qt.AlignVCenter
                                Layout.preferredHeight: 6
                                Layout.preferredWidth:  6
                                Layout.rightMargin:     5
                                radius:                 width/2
                                color:                  diskInfo.readBytes ? "magenta" : "transparent"
                            }
                            Rectangle {
                                Layout.alignment:       Qt.AlignVCenter
                                Layout.preferredHeight: 6
                                Layout.preferredWidth:  6
                                Layout.rightMargin:     5
                                radius:                 width/2
                                color:                  diskInfo.writeBytes ? "lightgreen" : "transparent"
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth:       true
            Layout.preferredHeight: root.barHeight
            color:                  "black"
            RowLayout {
                anchors { left: parent.left; right: parent.right; top: parent.top; bottom: parent.bottom; }
                Text {
                    id: diskIoLabel
                    Layout.fillHeight:   true
                    Layout.leftMargin:   2
                    Layout.rightMargin:  5
                    text:                "Disk IO:"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                    color:               "white"
                }
                Text {
                    id: diskIoRead
                    Layout.preferredWidth: parent.width/3
                    Layout.fillHeight:     true
                    text:                  "R "+diskInfoAll.readText
                    verticalAlignment:     Text.AlignVCenter
                    color:                 "magenta"
                }
                Text {
                    id: diskIoWrite
                    Layout.preferredWidth: parent.width/3
                    Layout.fillHeight:     true
                    text:                  "W "+diskInfoAll.writeText
                    verticalAlignment:     Text.AlignVCenter
                    color:                 "lightgreen"
                }
            }
        }

        HistoryGraph {
            id: theDiskIoHistory
            Layout.fillWidth:  true
            Layout.fillHeight: true
            model:             diskInfoAll.history
            discrete:          true
            showMinLabel:      false
            lineColors:        [diskIoRead.color,diskIoWrite.color]
            unitTxts:          [ {"min":0,            "max":1024,           "factor":1,           "unit":"B/sec",  "ticks": 256},
                                 {"min":1024,         "max":1024*1024,      "factor":1/1024,      "unit":"KB/sec", "ticks": 32*1024},
                                 {"min":1024*1024,    "max":20*1024*1024,   "factor":1/1024/1024, "unit":"MB/sec", "ticks": 1*1024*1024},
                                 {"min":20*1024*1024, "max":1024*1024*1024, "factor":1/1024/1024, "unit":"MB/sec", "ticks": 5*1024*1024}]
        }

        Repeater {
            model: partitionsInfo.paths.length
            PercentSensor {
                id: theDiskSensor
                percent:                partitionInfo.percent
                label:                  "Partition (" + partitionInfo.path + ")"
                postfix:                ", " + partitionInfo.freeText + " free"
                visible:                partitionInfo.avail
                Layout.fillWidth:       true
                Layout.preferredHeight: root.barHeight
                txtColor:               (partitionInfo.percent >= 98 && syncedAlarmTimer.highlight) ? "red" : "white"
                PartitionInfo {
                    id: partitionInfo
                    path: partitionsInfo.paths[index]
                }
            }
        }
    }

    CpuInfo {
        id: cpuInfo
    }

    MemInfo {
        id: memInfo
    }

    PartitionsInfo {
        id: partitionsInfo
    }

    DisksInfo {
        id: disksInfo
    }

    DiskInfo {
        id: diskInfoAll
    }

    NetworkInterfacesInfo {
        id: netInterfaces
    }

    NetworkInterfaceInfo {
        id: netInfoAll
    }

    Timer {
        id: syncedRenderTimer
        interval: 250
        repeat:   true
        running:  true
        onTriggered: {
            theCpuHistory.rerender()
            theProcHistory.rerender()
            theMemHistory.rerender()
            theNetIoHistory.rerender()
            theDiskIoHistory.rerender()
        }
    }

    Timer {
        id: syncedAlarmTimer
        interval: 500
        repeat:   true
        running:  true
        property bool highlight: false
        onTriggered: highlight = !highlight
    }
}
