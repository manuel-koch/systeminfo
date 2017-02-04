set -e
BASE_DIR=$(dirname ${0})

IN=${BASE_DIR}/resources.qrc
OUT=${BASE_DIR}/../systeminfo/ui/resources.py
echo "Building Resources..."
echo "from ${IN}"
echo "to   ${OUT}"
pyrcc5-3.5 -o "$OUT" "$IN" && echo Done

IN=${BASE_DIR}/utilities-system-monitor-icon.png
OUT=${BASE_DIR}/utilities-system-monitor-icon.icns
echo "Building Iconset..."
echo "from ${IN}"
echo "to   ${OUT}"
sips -s format icns "$IN" --out "$OUT"
