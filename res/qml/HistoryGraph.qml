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

Item {
    id: theHistory

    // assuming a model of rows of data where each row contains two columns, 1st is x-value in seconds any other column is y-value
    property var model

    // whether model data is considered discrete and different graph drawing is used
    property bool discrete: false

    // render data of one second duration within given pixels
    property real pixelPerSec: 10

    property int lineWidth:       2
    property var lineColors:      ["red"]
    property color fillColor:     "black"
    property bool autoYRange:     true
    property bool autoYRangeZero: true // whether to force min value of graph to zero
    property real maxYData:       0
    property real minYData:       0
    property var unitTxts:        [{"min": 0, "max":0, "factor":1, "decimals": 0, "unit":""}] // list of ranges for y-axis units
    property bool showMaxLabel:   true
    property bool showMinLabel:   true

    signal rerender()

    onLineWidthChanged:  theCanvas.requestPaint()
    onLineColorsChanged: theCanvas.requestPaint()
    onFillColorChanged:  theCanvas.requestPaint()
    onRerender:          theCanvas.requestPaint()

    onWidthChanged: theHistory.model.duration = Math.ceil( theCanvas.xDuration ) * 1.1

    Canvas {
        id: theCanvas
        anchors.fill: parent
        renderTarget: Canvas.Image
        property real xDuration: ( width / theHistory.pixelPerSec )
        property real xMin
        property real xMax
        property real yMin
        property real yMax
        property real yDim: yMax-yMin
        property string yMinText: getAxisTxtForY(yMin)
        property string yMaxText: getAxisTxtForY(yMax)

        Binding {
            target:   theCanvas
            property: "yMin"
            value:    theHistory.minYData
            when:     !theHistory.autoYRange
        }

        Binding {
            target:   theCanvas
            property: "yMax"
            value:    theHistory.maxYData
            when:     !theHistory.autoYRange
        }

        function xy2pt(x,y) {
            var h = height - theHistory.lineWidth
            var o = theHistory.lineWidth / 2
            if( yDim )
                return Qt.point( (x-xMin) * width / (xMax-xMin), o + h - (y-yMin) * h / (yMax-yMin) )
            else
                return Qt.point( (x-xMin) * width / (xMax-xMin), o )
        }

        function getUnitsKey(idx,key,defaultValue) {
            if( idx < theHistory.unitTxts.length && theHistory.unitTxts[idx][key] !== undefined )
                return theHistory.unitTxts[idx][key]
            else
                return defaultValue
        }

        function getAxisTxtForY(y) {
            var txt = "" + y
            for( var i=theHistory.unitTxts.length-1; i>=0; i-- ) {
                var vmin = getUnitsKey(i,"min",0)
                var vmax = getUnitsKey(i,"max",0)
                var f    = getUnitsKey(i,"factor",1)
                var d    = getUnitsKey(i,"decimals",0)
                var u    = getUnitsKey(i,"unit","")
                if( vmin !== vmax && y >= vmin && y <= vmax ) {
                    txt = "" + (y * f).toFixed(d) + (u ? " " : "" ) + u
                    break
                }
            }
            return txt
        }

        function getAxisValueForY(y,lower) {
            var y_ = y
            for( var i=theHistory.unitTxts.length-1; i>=0; i-- ) {
                var vmin = getUnitsKey(i,"min",0)
                var vmax = getUnitsKey(i,"max",0)
                var t    = getUnitsKey(i,"ticks",0)
                if( t != 0 && vmin !== vmax && y >= vmin && y <= vmax ) {
                    y_ = t * (lower ? Math.floor( y / t ) : Math.ceil( y / t ))
                    break
                }
            }
            return y_
        }

        function getXData(row) {
            return theHistory.model.data( theHistory.model.index(row,0) )
        }

        function getYData(row,idx) {
            return theHistory.model.data( theHistory.model.index(row,1+idx) )
        }

        function updateYRange(y) {
            yMin = theHistory.autoYRangeZero ? 0 : Math.min(yMin,getAxisValueForY(y,true))
            yMax = Math.max(yMax,getAxisValueForY(y,false))
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.fillStyle = theHistory.fillColor
            ctx.fillRect( 0, 0, width, height )

            var x, y, x_, y_;
            var nofRows = theHistory.model.rowCount()
            var nofSets = theHistory.model.columnCount()-1
            if( !nofRows )
                return

            // auto scale y-axis from current history data
            xMax = new Date().getTime() / 1000 // convert ms since epoch to secs
            xMin = xMax - xDuration
            if( theHistory.autoYRange ) {
                var rangeFound = false
                yMin = theHistory.autoYRangeZero ? 0 : 1e10
                yMax = -1e10
                for( var rowIdx=0; rowIdx<nofRows; rowIdx++ ) {
                    x = getXData(rowIdx)
                    if( xMin <= x && x <= xMax ) {
                        for( var setIdx=0; setIdx<nofSets; setIdx++ ) {
                            rangeFound = true
                            updateYRange( getYData(rowIdx,setIdx) )
                        }
                    }
                }
                if( !rangeFound ) {
                    // fallback to last known values from history
                    for( var setIdx=0; setIdx<nofSets; setIdx++ ) {
                        updateYRange( getYData(nofRows-1,setIdx) )
                    }
                }
                if( yMin == yMax ) {
                    yMin = Math.floor(yMin*0.95)
                    yMax = Math.ceil(yMax*1.05)
                }
            }

            // render the history lines
            var pt, pt_
            for( setIdx=0; setIdx<nofSets; setIdx++ ) {
                ctx.save()
                ctx.beginPath()
                ctx.lineJoin    = "round"
                ctx.strokeStyle = theHistory.lineColors[setIdx]
                ctx.fillStyle   = theHistory.fillColor
                ctx.lineWidth   = theHistory.lineWidth
                x = theHistory.model.data( theHistory.model.index(0,0) )
                y = theHistory.model.data( theHistory.model.index(0,setIdx+1) )
                pt = xy2pt(x,y)
                ctx.moveTo( pt.x, pt.y )
                for( rowIdx=1; rowIdx<nofRows; rowIdx++ ) {
                    x = theHistory.model.data( theHistory.model.index(rowIdx,0) )
                    y = theHistory.model.data( theHistory.model.index(rowIdx,setIdx+1) )
                    pt_ = pt
                    pt = xy2pt(x,y)
                    if( theHistory.discrete ) {
                        ctx.lineTo( pt.x, pt_.y )
                        ctx.lineTo( pt.x, pt.y )
                    } else {
                        ctx.lineTo( pt.x, pt.y )
                    }
                }
                ctx.lineTo( width, pt.y )
                ctx.stroke()
                ctx.restore()
            }

            // render y-axis range on right side of canvas
            ctx.save()
            ctx.strokeStyle = "white"
            var fontPxSize = 10
            ctx.font = "" + fontPxSize + "px monospace"
            if( theHistory.showMinLabel && theCanvas.yMinText ) {
                ctx.strokeText( theCanvas.yMinText, width - ctx.measureText(theCanvas.yMinText).width, height-2 )
            }
            if( theHistory.showMaxLabel && theCanvas.yMaxText ) {
                ctx.strokeText( theCanvas.yMaxText, width - ctx.measureText(theCanvas.yMaxText).width, fontPxSize )
            }
            ctx.restore()
        }
    }
}
