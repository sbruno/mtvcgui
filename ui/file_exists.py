# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_exists.ui'
#
# Created: Wed Jun 13 02:46:47 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FileExistsDialog(object):
    def setupUi(self, FileExistsDialog):
        FileExistsDialog.setObjectName(_fromUtf8("FileExistsDialog"))
        FileExistsDialog.resize(367, 92)
        self.buttonBox = QtGui.QDialogButtonBox(FileExistsDialog)
        self.buttonBox.setGeometry(QtCore.QRect(20, 55, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.label = QtGui.QLabel(FileExistsDialog)
        self.label.setGeometry(QtCore.QRect(30, 15, 321, 26))
        self.label.setObjectName(_fromUtf8("label"))

        self.retranslateUi(FileExistsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), FileExistsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), FileExistsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FileExistsDialog)

    def retranslateUi(self, FileExistsDialog):
        FileExistsDialog.setWindowTitle(QtGui.QApplication.translate("FileExistsDialog", "File exists", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileExistsDialog", "Chosen filename exists. Overwrite?", None, QtGui.QApplication.UnicodeUTF8))

