#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Santiago Bruno
# License: GPL v3
# Web pages: http://www.santiagobruno.com.ar/programas.html
#            http://code.google.com/p/mtvcgui/

#python imports
import ConfigParser
import os
import sys
from subprocess import Popen

#PyQt imports
from PyQt4 import QtCore, QtGui

#UI imports
from about import Ui_AboutDialog
from file_exists import Ui_FileExistsDialog
from mtvcgui import Ui_MainWindow



class AboutDialog(QtGui.QDialog, Ui_AboutDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)

class FileExistsDialog(QtGui.QDialog, Ui_FileExistsDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        
        #how should I communicate with the main window?
        self.parent = parent

    def accept(self):
        self.parent.runMencoder(accepted=True)
        self.close()

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.setParametersFromConfig()

    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.show()

    def setParametersFromConfig(self):
        config = ConfigParser.ConfigParser()
        config.read("mtvcgui.ini")
        if not config.has_section('mencoder GUI'):
            return None

        #main tab
        if config.has_option('mencoder GUI', 'channel'):
            self.channel.setValue(int(config.get('mencoder GUI', 'channel')))

        if config.has_option('mencoder GUI', 'duration'):
            self.duration.setTime(QtCore.QTime().fromString(config.get('mencoder GUI', 'duration')))

        if config.has_option('mencoder GUI', 'driver'):
            self.driver.setCurrentIndex(int(config.get('mencoder GUI', 'driver')))

        if config.has_option('mencoder GUI', 'device'):
            self.device.setText(config.get('mencoder GUI', 'device'))

        if config.has_option('mencoder GUI', 'norm'):
            self.norm.setValue(int(config.get('mencoder GUI', 'norm')))

        if config.has_option('mencoder GUI', 'input'):
            self.input.setValue(int(config.get('mencoder GUI', 'input')))

        if config.has_option('mencoder GUI', 'chanlist'):
            self.chanlist.setCurrentIndex(int(config.get('mencoder GUI', 'chanlist')))

        if config.has_option('mencoder GUI', 'audiocodec'):
            self.audiocodec.setCurrentIndex(int(config.get('mencoder GUI', 'audiocodec')))

        if config.has_option('mencoder GUI', 'videocodec'):
            self.videocodec.setCurrentIndex(int(config.get('mencoder GUI', 'videocodec')))


        #lavc options

        if config.has_option('mencoder GUI', 'lavc_audiocodec'):
            self.lavc_audiocodec.setText(config.get('mencoder GUI', 'lavc_audiocodec'))

        if config.has_option('mencoder GUI', 'lavc_audiobitrate'):
            self.lavc_audiobitrate.setText(config.get('mencoder GUI', 'lavc_audiobitrate'))

        if config.has_option('mencoder GUI', 'lavc_videocodec'):
            self.lavc_videocodec.setText(config.get('mencoder GUI', 'lavc_videocodec'))

        if config.has_option('mencoder GUI', 'lavc_videobitrate'):
            self.lavc_videobitrate.setText(config.get('mencoder GUI', 'lavc_videobitrate'))

        #tv parms tab

        if config.has_option('mencoder GUI', 'tvwidth'):
            self.tvwidth.setText(config.get('mencoder GUI', 'tvwidth'))

        if config.has_option('mencoder GUI', 'tvheight'):
            self.tvheight.setText(config.get('mencoder GUI', 'tvheight'))

        if config.has_option('mencoder GUI', 'audiorate'):
            self.audiorate.setText(config.get('mencoder GUI', 'audiorate'))

        if config.has_option('mencoder GUI', 'extratvparms'):
            self.extratvparms.setText(config.get('mencoder GUI', 'extratvparms'))


        #mencoder parms tab

        if config.has_option('mencoder GUI', 'scalewidth'):
            self.scalewidth.setText(config.get('mencoder GUI', 'scalewidth'))

        if config.has_option('mencoder GUI', 'scaleheight'):
            self.scaleheight.setText(config.get('mencoder GUI', 'scaleheight'))

        if config.has_option('mencoder GUI', 'ofps'):
            self.ofps.setText(config.get('mencoder GUI', 'ofps'))

        if config.has_option('mencoder GUI', 'noskip'):
            self.noskip.setChecked(config.get('mencoder GUI', 'noskip') == 'True')

        if config.has_option('mencoder GUI', 'quiet'):
            self.quiet.setChecked(config.get('mencoder GUI', 'quiet') == 'True')

        if config.has_option('mencoder GUI', 'extrafilters'):
            self.extrafilters.setText(config.get('mencoder GUI', 'extrafilters'))

        if config.has_option('mencoder GUI', 'extramencoderparms'):
            self.extramencoderparms.setText(config.get('mencoder GUI', 'extramencoderparms'))



        if config.has_option('mencoder GUI', 'outputfile'):
            self.outputfile.setText(config.get('mencoder GUI', 'outputfile'))


    def getParametersFromGUI(self, config=False):
        channel = str(self.channel.value())

        if self.duration.time().hour() or self.duration.time().minute() or self.duration.time().second():
            duration = "%.2d:%.2d:%.2d" % ( self.duration.time().hour(),
                                            self.duration.time().minute(),
                                            self.duration.time().second()
                                          )
        else:
            duration = ''

        if config:
            driver = self.driver.currentIndex()
        else:
            driver = str(self.driver.currentText())
        device = str(self.device.text())
        norm = str(self.norm.value())
        input = str(self.input.value())

        if config:
            chanlist = self.chanlist.currentIndex()
        else:
            chanlist = str(self.chanlist.currentText())

        if config:
            audiocodec = self.audiocodec.currentIndex()
        else:
            audiocodec = str(self.audiocodec.currentText())

        if config:
            videocodec = self.videocodec.currentIndex()
        else:
            videocodec = str(self.videocodec.currentText())

        lavc_audiocodec = str(self.lavc_audiocodec.text())
        lavc_audiobitrate = str(self.lavc_audiobitrate.text())
        lavc_videocodec = str(self.lavc_videocodec.text())
        lavc_videobitrate = str(self.lavc_videobitrate.text())

        tvwidth = str(self.tvwidth.text())
        tvheight = str(self.tvheight.text())
        audiorate = str(self.audiorate.text())
        extratvparms = str(self.extratvparms.text())

        quiet = self.quiet.isChecked()
        noskip = self.noskip.isChecked()

        scalewidth = str(self.scalewidth.text())
        scaleheight = str(self.scaleheight.text())
        ofps = str(self.ofps.text())
        extrafilters = str(self.extrafilters.text())
        extramencoderparms = str(self.extramencoderparms.text())

        outputfile = str(self.outputfile.text())

        return (channel,
                duration,
                driver,
                device,
                norm,
                input,
                chanlist,
                audiocodec,
                videocodec,
                lavc_audiocodec,
                lavc_audiobitrate,
                lavc_videocodec,
                lavc_videobitrate,
                tvwidth,
                tvheight,
                audiorate,
                extratvparms,
                scaleheight,
                scalewidth,
                ofps,
                noskip,
                quiet,
                extrafilters,
                extramencoderparms,
                outputfile)


    def generateCommand(self, preview=False):
        command = "mencoder tv://"

        (channel,
        duration,
        driver,
        device,
        norm,
        input,
        chanlist,
        audiocodec,
        videocodec,
        lavc_audiocodec,
        lavc_audiobitrate,
        lavc_videocodec,
        lavc_videobitrate,
        tvwidth,
        tvheight,
        audiorate,
        extratvparms,
        scaleheight,
        scalewidth,
        ofps,
        noskip,
        quiet,
        extrafilters,
        extramencoderparms,
        outputfile) = self.getParametersFromGUI()

        command += channel

        tvparms  = 'driver=' + driver
        tvparms += ':device=' + device
        if driver == 'v4l2':
            tvparms += ':normid=' + norm
        else:
            tvparms += ':norm=' + norm
        tvparms += ':input=' + input
        tvparms += ':chanlist=' + chanlist
        
        if tvwidth and tvheight:
            tvparms += ':width=' + tvwidth
            tvparms += ':height=' + tvheight
        if audiorate:
            tvparms += ':audiorate=' + audiorate
        
        if extratvparms:
            tvparms += ':' + extratvparms

        mencoderparms = ['-tv']

        mencoderparms.append(tvparms)

        if audiocodec == 'none':
            mencoderparms.append('-nosound')
        else:
            if preview:
                mencoderparms.append('-oac ' + audiocodec)
            else:
                mencoderparms += ['-oac', audiocodec]

        if preview:
            mencoderparms.append('-ovc ' + videocodec)
        else:
            mencoderparms += ['-ovc', videocodec]

        if duration:
            if preview:
                mencoderparms.append('-endpos ' + duration)
            else:
                mencoderparms += ['-endpos', duration]

        if ofps:
            if preview:
                mencoderparms.append('-ofps ' + ofps)
            else:
                mencoderparms += ['-ofps', ofps]

        if noskip:
            mencoderparms.append('-noskip')

        if quiet:
            mencoderparms.append('-quiet')


        if extrafilters or (scalewidth and scaleheight):
            filters = []
            if extrafilters:
                filters.append(extrafilters)
            if scaleheight:
                filters.append("scale=%s:%s" % (scalewidth, scaleheight) )

            filters = ','.join(filters)

            if preview:
                mencoderparms.append('-vf ' + filters)
            else:
                mencoderparms += ['-vf', filters]



        if lavc_audiocodec or lavc_audiobitrate or lavc_videobitrate or lavc_videocodec:
            lavcopts = []
            if lavc_audiocodec:
                lavcopts.append("acodec=" + lavc_audiocodec)
            if lavc_audiobitrate:
                lavcopts.append("abitrate=" + lavc_audiobitrate)
            if lavc_videocodec:
                lavcopts.append("vcodec=" + lavc_videocodec)
            if lavc_videobitrate:
                lavcopts.append("vbitrate=" + lavc_videobitrate)

            lavcopts = ':'.join(lavcopts)

            if preview:
                mencoderparms.append('-lavcopts ' + lavcopts)
            else:
                mencoderparms += ['-lavcopts', lavcopts]



        if extramencoderparms:
            if preview:
                mencoderparms.append(extramencoderparms)
            else:
                for extraparm in extramencoderparms.split(' '):
                    mencoderparms.append(extraparm)

        if preview:
            mencoderparms.append('-o ' + outputfile)
        else:
            mencoderparms += ['-o', outputfile]

        for parm in mencoderparms:
            command += ' ' + parm

        if preview:
            return command
        else:
            return ['mencoder', 'tv://' + str(self.channel.value())] + mencoderparms


    def runMencoder(self, accepted=False):
        if not accepted and os.path.exists(str(self.outputfile.text())):
            dialog = FileExistsDialog(self)
            dialog.show()
        else:
            self.stopButton.setEnabled(True)
            self.runButton.setEnabled(False)
            self.pid = Popen(self.generateCommand()).pid

    def stopButtonPressed(self):
        Popen(['kill', str(self.pid)])
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)

    def previewCommand(self):
        self.previewcommand.setText(self.generateCommand(preview=True))

    def saveConfiguration(self):

        (channel,
        duration,
        driver,
        device,
        norm,
        input,
        chanlist,
        audiocodec,
        videocodec,
        lavc_audiocodec,
        lavc_audiobitrate,
        lavc_videocodec,
        lavc_videobitrate,
        tvwidth,
        tvheight,
        audiorate,
        extratvparms,
        scaleheight,
        scalewidth,
        ofps,
        noskip,
        quiet,
        extrafilters,
        extramencoderparms,
        outputfile) = self.getParametersFromGUI(config=True)

        config = ConfigParser.ConfigParser()
        config.read("mtvcgui.ini")
        if not config.has_section('mencoder GUI'):
            config.add_section('mencoder GUI')
        
        config.set('mencoder GUI', 'channel', channel)
        config.set('mencoder GUI', 'duration', duration)
        config.set('mencoder GUI', 'driver', driver)
        config.set('mencoder GUI', 'device', device)
        config.set('mencoder GUI', 'norm', norm)
        config.set('mencoder GUI', 'input', input)
        config.set('mencoder GUI', 'chanlist', chanlist)
        config.set('mencoder GUI', 'audiocodec', audiocodec)
        config.set('mencoder GUI', 'videocodec', videocodec)
        config.set('mencoder GUI', 'lavc_audiocodec', lavc_audiocodec)
        config.set('mencoder GUI', 'lavc_audiobitrate', lavc_audiobitrate)
        config.set('mencoder GUI', 'lavc_videocodec', lavc_videocodec)
        config.set('mencoder GUI', 'lavc_videobitrate', lavc_videobitrate)
        config.set('mencoder GUI', 'tvwidth', tvwidth)
        config.set('mencoder GUI', 'tvheight', tvheight)
        config.set('mencoder GUI', 'audiorate', audiorate)
        config.set('mencoder GUI', 'extratvparms', extratvparms)
        config.set('mencoder GUI', 'scalewidth', scalewidth)
        config.set('mencoder GUI', 'scaleheight', scaleheight)
        config.set('mencoder GUI', 'ofps', ofps)
        config.set('mencoder GUI', 'noskip', noskip)
        config.set('mencoder GUI', 'quiet', quiet)
        config.set('mencoder GUI', 'extrafilters', extrafilters)
        config.set('mencoder GUI', 'extramencoderparms', extramencoderparms)
        config.set('mencoder GUI', 'outputfile', outputfile)

        try:
            config_file = open('mtvcgui.ini', 'w')
            config.write(config_file)
            config_file.close()
        except:
            #mostrar algun error
            pass

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
