# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'info.ui'
#
# Created: Sun Nov 30 01:34:49 2008
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog):
        InfoDialog.setObjectName("InfoDialog")
        InfoDialog.resize(562, 310)
        self.plainTextEdit = QtGui.QPlainTextEdit(InfoDialog)
        self.plainTextEdit.setGeometry(QtCore.QRect(-5, 0, 591, 316))
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setObjectName("plainTextEdit")

        self.retranslateUi(InfoDialog)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)

    def retranslateUi(self, InfoDialog):
        InfoDialog.setWindowTitle(QtGui.QApplication.translate("InfoDialog", "Info", None, QtGui.QApplication.UnicodeUTF8))

