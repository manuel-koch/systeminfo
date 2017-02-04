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

Rectangle {
    id: theSensor

    property real percent:      0
    property alias showValue:   theText.visible
    property string label:      ""
    property string postfix:    ""
    property alias bgColor:     theBg.color
    property var percentRanges: [0,80,90,95]                      /// Array of percent ranges, value denotes start of a range, final range is implicitly 100
    property var colorRanges:   ["green","yellow","orange","red"] /// Array of colors to be used for the corresponding range
    property alias txtColor:    theText.color

    Behavior on percent {
        SmoothedAnimation { velocity: 50 }
    }

    QtObject {
        id: internal
        function widthForPart(idx) {
            var sp = theSensor.percentRanges[idx]
            var ep = Math.min( idx+1 < theSensor.percentRanges.length ? theSensor.percentRanges[idx+1] : 100, theSensor.percent )
            return Math.max( 0, (ep - sp) * theSensor.width / 100 )
        }
        function gradientStopForPart(idx) {
            var sp = theSensor.percentRanges[idx]
            var ep = idx+1 < theSensor.percentRanges.length ? theSensor.percentRanges[idx+1] : 100
            return 1 / ( (Math.min(ep,theSensor.percent)-sp) / (ep-sp) )
        }
    }

    Rectangle {
        id: theBg
        anchors.fill: parent
        color:        "black"
    }

    Row {
        id: theBar
        anchors.left:   parent.left
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        spacing:        0
        Repeater {
            model: theSensor.percentRanges
            Item {
                width:   internal.widthForPart(index)
                visible: width>0
                height:  parent.height
                transformOrigin: Item.TopLeft
                Rectangle {
                    y:        width
                    width:    parent.height
                    height:   parent.width
                    rotation: -90
                    transformOrigin: Item.TopLeft
                    gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color:    theSensor.colorRanges[index]
                            }
                            GradientStop {
                                position: internal.gradientStopForPart(index)
                                color:    (index+1<theSensor.colorRanges.length) ? theSensor.colorRanges[index+1] : theSensor.colorRanges[index]
                            }
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill:        theText
        anchors.leftMargin:  -2
        anchors.rightMargin: -2
        color:               theSensor.bgColor
        opacity:             0.1
        visible:             theText.visible
    }

    Text {
        id: theText
        anchors.left:           parent.left
        anchors.leftMargin:     2
        anchors.verticalCenter: parent.verticalCenter
        text:                   theSensor.label + ": " + theSensor.percent.toFixed(1) + " %" + postfix
        font.pixelSize:         Math.min( 10, parent.height-2 )
        color:                  "white"
    }
}
