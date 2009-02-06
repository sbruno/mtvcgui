#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    mtvcgui
    Copyright (C) 2008  Santiago Bruno
    Web pages: http://www.santiagobruno.com.ar/programas.html#mtvcgui
               http://code.google.com/p/mtvcgui/
               http://github.com/sbruno/mtvcgui/

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


#python imports
import ConfigParser
import os
import re
import sys
import time
from subprocess import Popen, call

#PyQt imports
from PyQt4 import QtCore, QtGui

#UI imports
from ui.about import Ui_AboutDialog
from ui.file_exists import Ui_FileExistsDialog
from ui.info import Ui_InfoDialog
from ui.mtvcgui import Ui_MainWindow

#other imports
import utils


class InfoDialog(QtGui.QDialog, Ui_InfoDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


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

        self.mplayer_pid = 0
        self.mencoder_pid = 0

        #timer to update state while recording
        self.time_running = 0
        self.checker_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.checker_timer, QtCore.SIGNAL("timeout()"), self.update_status)

        #timer to check if the time of a sheduled recorded has been reached
        self.time_waiting = 0
        self.schedule_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.schedule_timer, QtCore.SIGNAL("timeout()"), self.check_schedule)

        #timer to check if mencoder has already created the recorded file and preview it
        self.preview_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.preview_timer, QtCore.SIGNAL("timeout()"), self.check_preview)

        self.error_dialog = QtGui.QErrorMessage(parent)

        self.setupUi(self)
        
        # I add the icon here because with QT Designer I get a different path
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./ui/icons/mplayer_32x32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        now = time.localtime()
        self.recording_date.setDate(QtCore.QDate.currentDate())
        self.recording_date.setTime(QtCore.QTime(now[3], now[4], 0))
        self.setParametersFromConfig()

    def update_status(self):
        if self.mencoder_instance.poll() is None:
            self.time_running += 1
            self.status_label.setText(self.tr('Recording... %1').arg(utils.secs_to_str(self.time_running)))
        else:
            self.record_stop_cleanup()

    def check_preview(self):
        if os.path.exists(self.filename):
            cmd = ['mplayer','-quiet', self.filename]
            try:
                self.mplayer_instance = Popen(cmd)
                self.mplayer_pid = self.mplayer_instance.pid
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % " ".join(cmd))
            self.preview_timer.stop()

    def check_schedule(self):
        current_time = QtCore.QDateTime.currentDateTime()
        recording_time = self.recording_date.dateTime()
        seconds_remaining = current_time.secsTo(recording_time)
        if seconds_remaining <= 0:
            self.append_suffix.setChecked(True)
            self.stopButton.setEnabled(True)
            self.runButton.setEnabled(False)
            self.runMencoder(accepted=True)
        else:
            self.status_label.setText(self.tr('Waiting %1').arg(utils.secs_to_str(seconds_remaining)))

    def record_stop_cleanup(self):
        self.status_label.setText(self.tr('Stopped'))
        self.checker_timer.stop()
        self.time_running = 0
        if self.mplayer_pid:
            call(['kill', str(self.mplayer_pid)])
            self.mplayer_pid = 0
        post_command = str(self.post_command.text())
        if post_command:
            cmds = [c for c in re.split("\s+", post_command) if c]
            try:
                call(cmds)
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % post_command)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)
        self.cancelScheduleButton.setEnabled(False)
        self.scheduleButton.setEnabled(True)

    def scheduleRecording(self):
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(False)
        self.cancelScheduleButton.setEnabled(True)
        self.scheduleButton.setEnabled(False)
        self.schedule_timer.start(1000)

    def cancelSchedule(self):
        self.status_label.setText(self.tr('Stopped'))
        self.schedule_timer.stop()
        self.cancelScheduleButton.setEnabled(False)
        self.scheduleButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)

    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.show()

    def audioCodecSelected(self,i):
        LAME = 3
        LAVC = 4
        if i == LAME:
            self.lavc_audio_options_box.hide()
            self.lame_options_box.show()
        elif i == LAVC:
            self.lame_options_box.hide()
            self.lavc_audio_options_box.show()
        else:
            self.lame_options_box.hide()
            self.lavc_audio_options_box.hide()

    def videoCodecSelected(self,i):
        LAVC = 2
        if i == LAVC:
            self.lavc_video_options_box.show()
        else:
            self.lavc_video_options_box.hide()

    def setParametersFromConfig(self):
        config = ConfigParser.ConfigParser()
        config_filename = os.path.join(os.path.expanduser("~"), '.mtvcgui', 'mtvcgui.ini')
        config.read(config_filename)
        if not config.has_section('mencoder GUI'):
            self.channel.show()
            self.frequency.hide()
            self.number_rb.setChecked(True)
            self.freq_rb.setChecked(False)
            self.audiocodec.setCurrentIndex(3) #default to mp3lame
            self.videocodec.setCurrentIndex(2) #default to lavc
            return None

        #main tab
        if config.has_option('mencoder GUI', 'channel_type'):
            channel_type = config.get('mencoder GUI', 'channel_type')
            if channel_type == 'frequency':
                self.channel.hide()
                self.frequency.show()
                self.number_rb.setChecked(False)
                self.freq_rb.setChecked(True)
            elif channel_type == 'number':
                self.channel.show()
                self.frequency.hide()
                self.number_rb.setChecked(True)
                self.freq_rb.setChecked(False)
        else:
            self.channel.show()
            self.frequency.hide()
            self.number_rb.setChecked(True)
            self.freq_rb.setChecked(False)

        if config.has_option('mencoder GUI', 'channel'):
            self.channel.setValue(int(config.get('mencoder GUI', 'channel')))

        if config.has_option('mencoder GUI', 'frequency'):
            self.frequency.setValue(float(config.get('mencoder GUI', 'frequency')))

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
        else:
            self.audiocodec.setCurrentIndex(3) #default to mp3lame

        if config.has_option('mencoder GUI', 'videocodec'):
            self.videocodec.setCurrentIndex(int(config.get('mencoder GUI', 'videocodec')))
        else:
            self.videocodec.setCurrentIndex(2) #default to lavc

        if config.has_option('mencoder GUI', 'append_suffix'):
            self.append_suffix.setChecked(config.get('mencoder GUI', 'append_suffix') == 'True')


        #lavc options

        if config.has_option('mencoder GUI', 'lavc_audiocodec'):
            self.lavc_audiocodec.setCurrentIndex(int(config.get('mencoder GUI', 'lavc_audiocodec')))

        if config.has_option('mencoder GUI', 'lavc_audiobitrate'):
            self.lavc_audiobitrate.setText(config.get('mencoder GUI', 'lavc_audiobitrate'))

        if config.has_option('mencoder GUI', 'lame_audiobitrate'):
            self.lame_audiobitrate.setText(config.get('mencoder GUI', 'lame_audiobitrate'))


        if config.has_option('mencoder GUI', 'lavc_videocodec'):
            self.lavc_videocodec.setCurrentIndex(int(config.get('mencoder GUI', 'lavc_videocodec')))

        if config.has_option('mencoder GUI', 'lavc_videobitrate'):
            self.lavc_videobitrate.setText(config.get('mencoder GUI', 'lavc_videobitrate'))


        if config.has_option('mencoder GUI', 'outputfile'):
            self.outputfile.setText(config.get('mencoder GUI', 'outputfile'))



        #tv parms tab

        if config.has_option('mencoder GUI', 'tvwidth'):
            self.tvwidth.setText(config.get('mencoder GUI', 'tvwidth'))

        if config.has_option('mencoder GUI', 'tvheight'):
            self.tvheight.setText(config.get('mencoder GUI', 'tvheight'))

        if config.has_option('mencoder GUI', 'audiorate'):
            self.audiorate.setText(config.get('mencoder GUI', 'audiorate'))

        if config.has_option('mencoder GUI', 'extratvparms'):
            self.extratvparms.setText(config.get('mencoder GUI', 'extratvparms'))

        if config.has_option('mencoder GUI', 'alsa_audio'):
            self.alsa_audio.setChecked(config.get('mencoder GUI', 'alsa_audio') == 'True')

        if config.has_option('mencoder GUI', 'adevice'):
            self.adevice.setText(config.get('mencoder GUI', 'adevice'))


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


        #advanced tab
        if config.has_option('mencoder GUI', 'pre_command'):
            self.pre_command.setText(config.get('mencoder GUI', 'pre_command'))

        if config.has_option('mencoder GUI', 'post_command'):
            self.post_command.setText(config.get('mencoder GUI', 'post_command'))

        if config.has_option('mencoder GUI', 'play_while_recording'):
            self.play_while_recording.setChecked(config.get('mencoder GUI', 'play_while_recording') == 'True')


    def getParametersFromGUI(self, config=False):
        channel = str(self.channel.value())
        frequency = str(self.frequency.value()).replace(",",".")
        channel_type = self.number_rb.isChecked() and 'number' or 'frequency'

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

        append_suffix = self.append_suffix.isChecked()

        if config:
            lavc_audiocodec = self.lavc_audiocodec.currentIndex()
        else:
            lavc_audiocodec = str(self.lavc_audiocodec.currentText())

        lavc_audiobitrate = str(self.lavc_audiobitrate.text())
        lame_audiobitrate = str(self.lame_audiobitrate.text())

        if config:
            lavc_videocodec = self.lavc_videocodec.currentIndex()
        else:
            lavc_videocodec = str(self.lavc_videocodec.currentText())


        lavc_videobitrate = str(self.lavc_videobitrate.text())

        outputfile = str(self.outputfile.text())

        tvwidth = str(self.tvwidth.text())
        tvheight = str(self.tvheight.text())
        audiorate = str(self.audiorate.text())
        alsa_audio = self.alsa_audio.isChecked()
        adevice = str(self.adevice.text())
        extratvparms = str(self.extratvparms.text())

        quiet = self.quiet.isChecked()
        noskip = self.noskip.isChecked()

        scalewidth = str(self.scalewidth.text())
        scaleheight = str(self.scaleheight.text())
        ofps = str(self.ofps.text())
        extrafilters = str(self.extrafilters.text())
        extramencoderparms = str(self.extramencoderparms.text())

        pre_command = str(self.pre_command.text())
        post_command = str(self.post_command.text())
        play_while_recording = self.play_while_recording.isChecked()

        parameters = {}
        parameters['channel_type'] = channel_type
        parameters['channel'] = channel
        parameters['frequency'] = frequency
        parameters['duration'] = duration
        parameters['driver'] = driver
        parameters['device'] = device
        parameters['norm'] = norm
        parameters['input'] = input
        parameters['chanlist'] = chanlist
        parameters['audiocodec'] = audiocodec
        parameters['videocodec'] = videocodec
        parameters['append_suffix'] = append_suffix
        parameters['lavc_audiocodec'] = lavc_audiocodec
        parameters['lavc_audiobitrate'] = lavc_audiobitrate
        parameters['lame_audiobitrate'] = lame_audiobitrate
        parameters['lavc_videocodec'] = lavc_videocodec
        parameters['lavc_videobitrate'] = lavc_videobitrate
        parameters['outputfile'] = outputfile

        parameters['tvwidth'] = tvwidth
        parameters['tvheight'] = tvheight
        parameters['audiorate'] = audiorate
        parameters['alsa_audio'] = alsa_audio
        parameters['adevice'] = adevice
        parameters['extratvparms'] = extratvparms

        parameters['scaleheight'] = scaleheight
        parameters['scalewidth'] = scalewidth
        parameters['ofps'] = ofps
        parameters['noskip'] = noskip
        parameters['quiet'] = quiet
        parameters['extrafilters'] = extrafilters
        parameters['extramencoderparms'] = extramencoderparms

        parameters['pre_command'] = pre_command
        parameters['post_command'] = post_command
        parameters['play_while_recording'] = play_while_recording

        if channel_type == 'number':
            parameters['channel_text'] = str(self.channel.value())
        elif channel_type == 'frequency':
            parameters['channel_text'] = str(self.frequency.value()).replace(",",".")

        return parameters



    def previewWithMplayer(self):
        parameters = self.getParametersFromGUI()
        cmd = utils.generateMplayerCommand(parameters)
        try:
            self.mplayer_instance = Popen(cmd)
            self.mplayer_pid = self.mplayer_instance.pid
        except OSError:
            self.error_dialog.showMessage("excecution of %s failed" % " ".join(cmd))



    def runMencoder(self, accepted=False):
        if self.mplayer_pid:
            call(['kill', str(self.mplayer_pid)])
            self.mplayer_pid = 0

        parameters = self.getParametersFromGUI()

        self.schedule_timer.stop()
        channel_text = parameters.get('channel_text')
        append_suffix = self.append_suffix.isChecked()
        play_while_recording = self.play_while_recording.isChecked()
        filename = utils.make_filename(str(self.outputfile.text()), channel_text, append_suffix=append_suffix)

        self.filename = filename

        if not accepted and os.path.exists(filename):
            dialog = FileExistsDialog(self)
            dialog.show()
        else:
            self.stopButton.setEnabled(True)
            self.runButton.setEnabled(False)

            pre_command = str(self.pre_command.text())
            if pre_command:
                cmds = [c for c in re.split("\s+", pre_command) if c]
                try:
                    call(cmds)
                except OSError:
                    self.error_dialog.showMessage("excecution of %s failed" % pre_command)

            cmd = utils.generateCommand(parameters)
            try:
                self.mencoder_instance = Popen(cmd)
                self.mencoder_pid = self.mencoder_instance.pid
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % " ".join(cmd))

            if self.mencoder_pid:
                self.status_label.setText(self.tr('Recording... %1').arg(utils.secs_to_str(self.time_running)))
                self.checker_timer.start(1000)
                self.scheduleButton.setEnabled(False)
                self.cancelScheduleButton.setEnabled(False)
                if play_while_recording:
                    self.preview_timer.start(1000)
            else:
                self.stopButton.setEnabled(False)
                self.runButton.setEnabled(True)


    def showAvailableAudioCodecs(self):
        dialog = InfoDialog(self)
        text = utils.getCodecs('mencoder -oac help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def showAvailableVideoCodecs(self):
        dialog = InfoDialog(self)
        text = utils.getCodecs('mencoder -ovc help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def stopButtonPressed(self):
        if self.mencoder_pid:
            call(['kill', str(self.mencoder_pid)])
            self.mencoder_pid = 0
        self.record_stop_cleanup()

    def previewCommand(self):
        parameters = self.getParametersFromGUI()
        self.previewcommand.setText(utils.generateCommand(parameters, preview=True))

    def saveConfiguration(self):
        parameters = self.getParametersFromGUI(config=True)
        utils.saveConfiguration(parameters)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    translation = utils.findTranslation()
    if translation:
        appTranslator = QtCore.QTranslator()
        appTranslator.load(translation)
        app.installTranslator(appTranslator)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
