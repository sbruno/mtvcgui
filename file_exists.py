# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_exists.ui'
#
# Created: Thu Nov 27 03:23:35 2008
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_FileExistsDialog(object):
    def setupUi(self, FileExistsDialog):
        FileExistsDialog.setObjectName("FileExistsDialog")
        FileExistsDialog.resize(367, 92)
        self.buttonBox = QtGui.QDialogButtonBox(FileExistsDialog)
        self.buttonBox.setGeometry(QtCore.QRect(20, 55, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtGui.QLabel(FileExistsDialog)
        self.label.setGeometry(QtCore.QRect(85, 15, 246, 16))
        self.label.setObjectName("label")

        self.retranslateUi(FileExistsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), FileExistsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), FileExistsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FileExistsDialog)

    def retranslateUi(self, FileExistsDialog):
        FileExistsDialog.setWindowTitle(QtGui.QApplication.translate("FileExistsDialog", "File exists", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileExistsDialog", "Chosen filename exists. Overwrite?", None, QtGui.QApplication.UnicodeUTF8))

