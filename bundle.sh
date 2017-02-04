res/build_resources.sh

# Somehow PyInstaller is unable to find PyQt5 stuff automatically.
# We give it some hints here...
PYQT5_DIR=$(python3.5 -c "import os ; import PyQt5 ; print(os.path.dirname(PyQt5.__file__))")
export QT5DIR=/opt/local/libexec/qt5
export PATH=${QT5DIR}:${PYQT5_DIR}:${PATH}
echo PYQT5_DIR=${PYQT5_DIR}
echo QT5DIR=${QT5DIR}
pyinstaller-3.5 --log-level=DEBUG --onefile --windowed --clean --paths $(dirname $0) $(dirname $0)/systeminfo.spec
