#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Santiago Bruno
# License: GPL v3
# Web pages: http://www.santiagobruno.com.ar/programas.html
#            http://code.google.com/p/mtvcgui/

#python imports
import commands
import ConfigParser
import locale
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


def findTranslation(prefix='', tr_dir='i18n'):
    """Function to find a translation file in a directory and install it to an app
    """
    #try with country specific locale (e.g.: es_AR)
    lang = locale.getdefaultlocale()[0]
    if lang:
        tr_path = os.path.join(tr_dir, prefix + lang + '.qm')

        if not os.path.exists(tr_path):
            #try with generic locale (e.g.: es)
            lang = lang.split('_')[0]
            tr_path = os.path.join(tr_dir, prefix + lang + '.qm')
            if not os.path.exists(tr_path):
                #don't translate
                tr_path = ''
    else:
        tr_path = ''

    return tr_path


def getCodecs(cmd):
    output = commands.getoutput(cmd)
    lines = output.split('\n')
    text = ''
    skip = True
    for line in lines:
        if not skip:
            text += '\n' + line
        if 'Available codecs:' in line:
            text += line
            skip = False
    if not text:
        text = output
    return text


def make_filename(filename, channel_text, append_suffix=True):

    def repl_func(match, now):
        year   = now[0]
        month  = now[1]
        day    = now[2]
        hour   = now[3]
        minute = now[4]
        second = now[5]

        text = match.group()

        text = text.replace('%Y', str(year))
        text = text.replace('%y', str(year)[2:])
        text = text.replace('%m', "%.2d" % month)
        text = text.replace('%d', "%.2d" % day)
        text = text.replace('%H', "%.2d" % hour)
        text = text.replace('%M', "%.2d" % minute)
        text = text.replace('%S', "%.2d" % second)

        return text[1:-1]

    new_filename = filename.replace('{channel}', channel_text)
    now    = time.localtime()
    new_filename = re.sub('{[^}]*?}', lambda x: repl_func(x, now), new_filename)

    if append_suffix:
        suffix = 1
        appended_filename = new_filename
        while os.path.exists(appended_filename):
            dot_splitted = new_filename.split('.')

            if len(dot_splitted) > 1:
                name = dot_splitted[:-1]
                extension = [dot_splitted[-1]]
            else:
                name = dot_splitted
                extension = []

            name[-1] = name[-1] + '_' + str(suffix)

            appended_filename = '.'.join(name + extension)
            suffix += 1
        new_filename = appended_filename

    return new_filename

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
        self.time_running = 0
        self.checker_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.checker_timer, QtCore.SIGNAL("timeout()"), self.update_status)

        self.setupUi(self)
        self.setParametersFromConfig()

    def update_status(self):
        if self.mplayer_instance.poll() != 0:
            self.time_running += 1
            self.status_label.setText('Recording... %s seconds' % str(self.time_running))
        else:
            self.record_stop_cleanup()


    def record_stop_cleanup(self):
        self.status_label.setText('Stopped')
        self.checker_timer.stop()
        self.time_running = 0
        post_command = str(self.post_command.text())
        if post_command:
            call(post_command)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)


    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.show()

    def getChannel(self):
        if self.number_rb.isChecked():
            return str(self.channel.value())
        elif self.freq_rb.isChecked():
            return str(self.frequency.value()).replace(",",".")

    def setParametersFromConfig(self):
        config = ConfigParser.ConfigParser()
        config.read("mtvcgui.ini")
        if not config.has_section('mencoder GUI'):
            self.channel.show()
            self.frequency.hide()
            self.number_rb.setChecked(True)
            self.freq_rb.setChecked(False)
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

        if config.has_option('mencoder GUI', 'videocodec'):
            self.videocodec.setCurrentIndex(int(config.get('mencoder GUI', 'videocodec')))

        if config.has_option('mencoder GUI', 'append_suffix'):
            self.append_suffix.setChecked(config.get('mencoder GUI', 'append_suffix') == 'True')


        #lavc options

        if config.has_option('mencoder GUI', 'lavc_audiocodec'):
            self.lavc_audiocodec.setText(config.get('mencoder GUI', 'lavc_audiocodec'))

        if config.has_option('mencoder GUI', 'lavc_audiobitrate'):
            self.lavc_audiobitrate.setText(config.get('mencoder GUI', 'lavc_audiobitrate'))

        if config.has_option('mencoder GUI', 'lavc_videocodec'):
            self.lavc_videocodec.setText(config.get('mencoder GUI', 'lavc_videocodec'))

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

        lavc_audiocodec = str(self.lavc_audiocodec.text())
        lavc_audiobitrate = str(self.lavc_audiobitrate.text())
        lavc_videocodec = str(self.lavc_videocodec.text())
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

        return parameters

    def generateCommand(self, preview=False):
        command = "mencoder tv://"

        parameters = self.getParametersFromGUI()

        channel_type = parameters.get('channel_type', 'number')
        channel = parameters.get('channel')
        frequency = parameters.get('frequency')
        duration = parameters.get('duration')
        driver = parameters.get('driver')
        device = parameters.get('device')
        norm = parameters.get('norm')
        input = parameters.get('input')
        chanlist = parameters.get('chanlist')
        audiocodec = parameters.get('audiocodec')
        videocodec = parameters.get('videocodec')
        append_suffix = parameters.get('append_suffix')
        lavc_audiocodec = parameters.get('lavc_audiocodec')
        lavc_audiobitrate = parameters.get('lavc_audiobitrate')
        lavc_videocodec = parameters.get('lavc_videocodec')
        lavc_videobitrate = parameters.get('lavc_videobitrate')
        tvwidth = parameters.get('tvwidth')
        tvheight = parameters.get('tvheight')
        audiorate = parameters.get('audiorate')
        alsa_audio = parameters.get('alsa_audio')
        adevice = parameters.get('adevice')
        extratvparms = parameters.get('extratvparms')
        scaleheight = parameters.get('scaleheight')
        scalewidth = parameters.get('scalewidth')
        ofps = parameters.get('ofps')
        noskip = parameters.get('noskip')
        quiet = parameters.get('quiet')
        extrafilters = parameters.get('extrafilters')
        extramencoderparms = parameters.get('extramencoderparms')
        outputfile = parameters.get('outputfile')

        channel_text = self.getChannel()

        outputfile = make_filename(outputfile, channel_text, append_suffix=append_suffix)


        if channel_type == 'frequency':
            tvparms = 'freq=' + frequency
        else:
            tvparms = 'channel=' + channel

        tvparms  += ':driver=' + driver
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

        if alsa_audio:
            tvparms += ":alsa"
            if adevice:
                tvparms += ":adevice=" + adevice

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
            return ['mencoder', 'tv://'] + mencoderparms


    def runMencoder(self, accepted=False):
        channel_text = self.getChannel()
        append_suffix = self.append_suffix.isChecked()
        filename = make_filename(str(self.outputfile.text()), channel_text, append_suffix=append_suffix)

        if not accepted and os.path.exists(filename):
            dialog = FileExistsDialog(self)
            dialog.show()
        else:
            self.stopButton.setEnabled(True)
            self.runButton.setEnabled(False)

            pre_command = str(self.pre_command.text())
            if pre_command:
                call(pre_command)

            self.mplayer_instance = Popen(self.generateCommand())
            self.pid = self.mplayer_instance.pid

            if self.pid:
                self.checker_timer.start(1000)
            else:
                self.stopButton.setEnabled(False)
                self.runButton.setEnabled(True)


    def showAvailableAudioCodecs(self):
        dialog = InfoDialog(self)
        text = getCodecs('mencoder -oac help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def showAvailableVideoCodecs(self):
        dialog = InfoDialog(self)
        text = getCodecs('mencoder -ovc help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def stopButtonPressed(self):
        call(['kill', str(self.pid)])
        self.record_stop_cleanup()

    def previewCommand(self):
        self.previewcommand.setText(self.generateCommand(preview=True))

    def saveConfiguration(self):
        parameters = self.getParametersFromGUI(config=True)

        config = ConfigParser.ConfigParser()
        config.read("mtvcgui.ini")
        if not config.has_section('mencoder GUI'):
            config.add_section('mencoder GUI')

        config.set('mencoder GUI', 'channel_type', parameters.get('channel_type', 'number'))
        config.set('mencoder GUI', 'channel', parameters.get('channel'))
        config.set('mencoder GUI', 'frequency', parameters.get('frequency'))
        config.set('mencoder GUI', 'duration', parameters.get('duration'))
        config.set('mencoder GUI', 'driver', parameters.get('driver'))
        config.set('mencoder GUI', 'device', parameters.get('device'))
        config.set('mencoder GUI', 'norm', parameters.get('norm'))
        config.set('mencoder GUI', 'input', parameters.get('input'))
        config.set('mencoder GUI', 'chanlist', parameters.get('chanlist'))
        config.set('mencoder GUI', 'audiocodec', parameters.get('audiocodec'))
        config.set('mencoder GUI', 'videocodec', parameters.get('videocodec'))
        config.set('mencoder GUI', 'append_suffix', parameters.get('append_suffix'))
        config.set('mencoder GUI', 'lavc_audiocodec', parameters.get('lavc_audiocodec'))
        config.set('mencoder GUI', 'lavc_audiobitrate', parameters.get('lavc_audiobitrate'))
        config.set('mencoder GUI', 'lavc_videocodec', parameters.get('lavc_videocodec'))
        config.set('mencoder GUI', 'lavc_videobitrate', parameters.get('lavc_videobitrate'))
        config.set('mencoder GUI', 'tvwidth', parameters.get('tvwidth'))
        config.set('mencoder GUI', 'tvheight', parameters.get('tvheight'))
        config.set('mencoder GUI', 'audiorate', parameters.get('audiorate'))
        config.set('mencoder GUI', 'alsa_audio', parameters.get('alsa_audio'))
        config.set('mencoder GUI', 'adevice', parameters.get('adevice'))
        config.set('mencoder GUI', 'extratvparms', parameters.get('extratvparms'))
        config.set('mencoder GUI', 'scalewidth', parameters.get('scaleheight'))
        config.set('mencoder GUI', 'scaleheight', parameters.get('scalewidth'))
        config.set('mencoder GUI', 'ofps', parameters.get('ofps'))
        config.set('mencoder GUI', 'noskip', parameters.get('noskip'))
        config.set('mencoder GUI', 'quiet', parameters.get('quiet'))
        config.set('mencoder GUI', 'extrafilters', parameters.get('extrafilters'))
        config.set('mencoder GUI', 'extramencoderparms', parameters.get('extramencoderparms'))
        config.set('mencoder GUI', 'pre_command', parameters.get('pre_command'))
        config.set('mencoder GUI', 'post_command', parameters.get('post_command'))
        config.set('mencoder GUI', 'outputfile', parameters.get('outputfile'))

        try:
            config_file = open('mtvcgui.ini', 'w')
            config.write(config_file)
            config_file.close()
        except:
            #mostrar algun error
            pass

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    translation = findTranslation()
    if translation:
        appTranslator = QtCore.QTranslator()
        appTranslator.load(translation)
        app.installTranslator(appTranslator)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
