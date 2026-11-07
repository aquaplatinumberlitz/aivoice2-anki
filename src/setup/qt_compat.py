"""Qt 6 binding selection; the runtime/backend itself has no Qt dependency."""
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    Signal=QtCore.Signal
    QT_BINDING='PySide6'
except ImportError:
    from PyQt6 import QtCore, QtGui, QtWidgets
    Signal=QtCore.pyqtSignal
    QT_BINDING='PyQt6'

Qt=QtCore.Qt
