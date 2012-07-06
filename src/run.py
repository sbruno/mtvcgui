#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
    mtvcgui
    Copyright (C) 2008-2012  Santiago Bruno
    Web pages: http://www.santiagobruno.com.ar/programas.html#mtvcgui
               http://code.google.com/p/mtvcgui/

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
from subprocess import Popen, call, PIPE

#PyQt imports
from PyQt4 import QtCore, QtGui

#UI imports
from ui.about import Ui_AboutDialog
from ui.file_exists import Ui_FileExistsDialog
from ui.info import Ui_InfoDialog
from ui.mtvcgui import Ui_MainWindow

#other imports
import utils

config = ConfigParser.ConfigParser()

NORMS_DICT = {}
INPUTS_DICT = {}

class InfoDialog(QtGui.QDialog, Ui_InfoDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        if parent and parent.translator:
            self.retranslateUi(self)


class AboutDialog(QtGui.QDialog, Ui_AboutDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        if parent and parent.translator:
            self.retranslateUi(self)

class FileExistsDialog(QtGui.QDialog, Ui_FileExistsDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        if parent and parent.translator:
            self.retranslateUi(self)
        
        #how should I communicate with the main window?
        self.parent = parent

    def accept(self):
        self.parent.run_mencoder(accepted=True)
        self.close()

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.translator = None
        self.locale_string = None
        self.mplayer_preview_pid = 0
        self.mplayer_recording_pid = 0
        self.mencoder_pid = 0
        self.tail_pid = 0

        #timer to update state while recording
        self.time_running = 0
        self.checker_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.checker_timer,
            QtCore.SIGNAL("timeout()"), self.update_status)

        #timer to check if the time of a sheduled recorded has been reached
        self.time_waiting = 0
        self.schedule_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.schedule_timer,
            QtCore.SIGNAL("timeout()"), self.check_schedule)

        #timer to check if mencoder has already created the recorded file
        #and preview it
        self.preview_file_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.preview_file_timer,
            QtCore.SIGNAL("timeout()"), self.check_preview_file)

        #timer to check if mplayer preview is still alive
        self.mplayer_preview_timer = QtCore.QTimer()
        QtCore.QObject.connect(self.mplayer_preview_timer,
            QtCore.SIGNAL("timeout()"), self.check_mplayer_preview)


        self.error_dialog = QtGui.QErrorMessage(parent)

        self.setupUi(self)
        
        # I add the icon here because with QT Designer I get a different path
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./ui/icons/mplayer_32x32.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        now = time.localtime()
        self.recording_date.setDate(QtCore.QDate.currentDate())
        self.recording_date.setTime(QtCore.QTime(now[3], now[4], 0))
        
        
        codecs = utils.get_codecs_list('mencoder -oac help')
        if codecs:
            self.audiocodec.clear()
            for codec in codecs:
                self.audiocodec.addItem(codec)
                
        codecs = utils.get_codecs_list('mencoder -ovc help')
        if codecs:
            self.videocodec.clear()
            for codec in codecs:
                self.videocodec.addItem(codec)     

        self.set_params_from_config()
        self.update_device_values()
        
        oldconfig = False
        if config.has_option('mencoder GUI', 'audiocodec'):
            try:
                int(config.get('mencoder GUI', 'audiocodec'))
                oldconfig = True
            except:
                pass
        if config.has_option('mencoder GUI', 'videocodec'):
            try:
                int(config.get('mencoder GUI', 'videocodec'))
                oldconfig = True
            except:
                pass

        self.change_language(self.locale_string)
        
        if oldconfig:
            QtGui.QMessageBox.information(self,
                self.tr("mtvcgui upgrade information"),
                self.tr("You are using a configuration file from an older " \
        "mtvcgui version.\nCurrent version get supported norms, video codecs "\
        "and audio codecs from mplayer and store them as strings in the "\
        "file ~/.mtvgui/mtvcgui.ini instead of integer values as in previous "\
        "versions.\n\nTo avoid this message to appear again select your "\
        "desired norm, audio codec and video codec values next and save "\
        "the configuration."));
        
        
   

    def update_status(self):
        returncode = self.mencoder_instance.poll()
        if returncode is None:
            self.time_running += 1
            self.status_label.setText(self.tr('Recording... %1').arg(utils.secs_to_str(self.time_running)))
        else:
            print "process finished with status code %s" % str(returncode)
            if returncode > 0:
                self.error_dialog.showMessage(self.tr("mencoder execution " \
                    "failed. This program produces output to stdout. Start " \
                    "the program from the command line and check console " \
                    "output for possible causes of this failure."))
            self.record_stop_cleanup()

    def check_preview_file(self):        
        #check that file exists and has some data
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 50000:
            try:
                self.tail_instance = Popen(["tail", "-f", "-c", "+0", self.filename], stdout=PIPE)
                self.mplayer_instance = Popen(["mplayer", "-quiet", "-"], stdin=self.tail_instance.stdout)
                self.mplayer_recording_pid = self.mplayer_instance.pid
                self.tail_pid = self.tail_instance.pid
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % " ".join(cmd))
            self.preview_file_timer.stop()


    def check_mplayer_preview(self):
        if self.mplayer_instance.poll() is not None:
            self.mplayer_preview_pid = 0
            self.mplayer_preview_timer.stop()


    def check_schedule(self):
        current_time = QtCore.QDateTime.currentDateTime()
        recording_time = self.recording_date.dateTime()
        seconds_remaining = current_time.secsTo(recording_time)
        if seconds_remaining <= 0:
            self.append_suffix.setChecked(True)
            self.stopButton.setEnabled(True)
            self.runButton.setEnabled(False)
            self.run_mencoder(accepted=True)
        else:
            self.status_label.setText(self.tr('Waiting %1').arg(utils.secs_to_str(seconds_remaining)))

    def record_stop_cleanup(self):
        self.status_label.setText(self.tr('Stopped'))
        self.checker_timer.stop()
        self.time_running = 0
        if self.mplayer_recording_pid:
            if self.tail_pid:
                call(['kill', str(self.tail_pid)])
                self.tail_pid = 0
            call(['kill', str(self.mplayer_recording_pid)])
            self.mplayer_recording_pid = 0
            
        post_command = str(self.post_command.text())
        if post_command:
            cmds = [c for c in re.split("\s+", post_command) if c]
            try:
                call(cmds)
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % post_command)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)
        self.cancel_sheduleButton.setEnabled(False)
        self.scheduleButton.setEnabled(True)

    def exit_cleanup(self):
        if self.mplayer_recording_pid:
            print "killing mplayer rec"
            call(['kill', str(self.mplayer_recording_pid)])
            if self.tail_pid:
                call(['kill', str(self.tail_pid)])
        if self.mplayer_preview_pid:
            print "killing mplayer prev"
            call(['kill', str(self.mplayer_preview_pid)])
        if self.mencoder_pid:
            call(['kill', str(self.mencoder_pid)])


    def shedule_recording(self):
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(False)
        self.cancel_sheduleButton.setEnabled(True)
        self.scheduleButton.setEnabled(False)
        self.schedule_timer.start(1000)

    def cancel_shedule(self):
        self.status_label.setText(self.tr('Stopped'))
        self.schedule_timer.stop()
        self.cancel_sheduleButton.setEnabled(False)
        self.scheduleButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.show()
        
    def show_save_config_dialog(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, self.tr("Select the configuration file to save"), "", self.tr("mtvcgui configuration Files (*.ini)"))
        if filename:
            config_filename = str(filename)
            self.save_configuration(config_filename)
        
    def show_load_config_dialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select the configuration file to load"), "", self.tr("mtvcgui configuration Files (*.ini)"))
        if filename:
            config_filename = str(filename)
            self.set_params_from_config(config_filename)

    def audio_codec_selected(self, i):
        if self.audiocodec.itemText(i) == 'mp3lame':
            self.lavc_audio_options_box.hide()
            self.lame_options_box.show()
        elif self.audiocodec.itemText(i) == 'lavc':
            self.lame_options_box.hide()
            self.lavc_audio_options_box.show()
        else:
            self.lame_options_box.hide()
            self.lavc_audio_options_box.hide()

    def video_codec_selected(self, i):
        if self.videocodec.itemText(i) == 'lavc':
            self.x264_options_box.hide()
            self.xvid_options_box.hide()
            self.lavc_video_options_box.show()
        elif self.videocodec.itemText(i) == 'xvid':
            self.x264_options_box.hide()
            self.xvid_options_box.show()
            self.lavc_video_options_box.hide()
        elif self.videocodec.itemText(i) == 'x264':
            self.x264_options_box.show()
            self.xvid_options_box.hide()
            self.lavc_video_options_box.hide()
        else:
            self.x264_options_box.hide()
            self.xvid_options_box.hide()
            self.lavc_video_options_box.hide()

    def set_params_from_config(self, config_filename=None):
        global config
        if not config_filename:
            config_filename = os.path.join(os.path.expanduser("~"), '.mtvcgui', 'mtvcgui.ini')
        config.read(config_filename)
        if not config.has_section('mencoder GUI'):
            self.channel.show()
            self.frequency.hide()
            self.number_rb.setChecked(True)
            self.freq_rb.setChecked(False)
            self.audiocodec.setCurrentIndex(0)
            self.videocodec.setCurrentIndex(0)
            self.set_xvid_cbr(False)
            self.set_x264_cbr(False)
            return None

        #main tab
        if config.has_option('mencoder GUI', 'language'):
            lang = config.get('mencoder GUI', 'language')
            self.locale_string = lang if lang else None
            
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
            self.frequency.setValue(float(config.get('mencoder GUI',
                                                     'frequency')))

        if config.has_option('mencoder GUI', 'duration'):
            self.duration.setTime(QtCore.QTime().fromString(
                config.get('mencoder GUI', 'duration'))
                )

        if config.has_option('mencoder GUI', 'driver'):
            self.driver.setCurrentIndex(int(config.get('mencoder GUI',
                                                       'driver')))

        if config.has_option('mencoder GUI', 'device'):
            self.device.setText(config.get('mencoder GUI', 'device'))
            
        self.update_norm_index_from_config()
        
        self.update_input_index_from_config()

        if config.has_option('mencoder GUI', 'chanlist'):
            self.chanlist.setCurrentIndex(int(config.get('mencoder GUI',
                                                         'chanlist')))

        if config.has_option('mencoder GUI', 'audiocodec'):
            index = self.audiocodec.findText(config.get('mencoder GUI',
                                                        'audiocodec'))
            self.audiocodec.setCurrentIndex(index)
            
            
        if config.has_option('mencoder GUI', 'videocodec'):
            index = self.videocodec.findText(config.get('mencoder GUI',
                                                        'videocodec'))
            self.videocodec.setCurrentIndex(index)

        if config.has_option('mencoder GUI', 'append_suffix'):
            self.append_suffix.setChecked(
                config.get('mencoder GUI', 'append_suffix') == 'True'
                )


        #lame options
        
        if config.has_option('mencoder GUI', 'lame_audiobitrate'):
            self.lame_audiobitrate.setText(config.get('mencoder GUI', 'lame_audiobitrate'))
            
        if config.has_option('mencoder GUI', 'lame_extra_opts'):
            self.lame_extra_opts.setText(config.get('mencoder GUI', 'lame_extra_opts'))
                
                
        #lavc audio options

        if config.has_option('mencoder GUI', 'lavc_audiocodec'):
            self.lavc_audiocodec.setCurrentIndex(int(config.get('mencoder GUI', 'lavc_audiocodec')))

        if config.has_option('mencoder GUI', 'lavc_audiobitrate'):
            self.lavc_audiobitrate.setText(config.get('mencoder GUI', 'lavc_audiobitrate'))

        if config.has_option('mencoder GUI', 'lavc_audio_extra_opts'):
            self.lavc_audio_extra_opts.setText(config.get('mencoder GUI', 'lavc_audio_extra_opts'))

            
        #lavc video options
        
        if config.has_option('mencoder GUI', 'lavc_videocodec'):
            self.lavc_videocodec.setCurrentIndex(int(config.get('mencoder GUI', 'lavc_videocodec')))

        if config.has_option('mencoder GUI', 'lavc_videobitrate'):
            self.lavc_videobitrate.setText(config.get('mencoder GUI', 'lavc_videobitrate'))
            
        if config.has_option('mencoder GUI', 'lavc_video_extra_opts'):
            self.lavc_video_extra_opts.setText(config.get('mencoder GUI', 'lavc_video_extra_opts'))

            
        #xvid options

        if config.has_option('mencoder GUI', 'xvid_cbr'):
            self.xvid_cbr.setChecked(
                config.get('mencoder GUI', 'xvid_cbr') == 'True'
                )
                
        if config.has_option('mencoder GUI', 'xvid_bitrate'):
            self.xvid_bitrate.setText(config.get('mencoder GUI', 'xvid_bitrate'))
            
        if config.has_option('mencoder GUI', 'xvid_extra_opts'):
            self.xvid_extra_opts.setText(config.get('mencoder GUI', 'xvid_extra_opts'))
            
        if config.has_option('mencoder GUI', 'xvid_fixed_quant'):
            self.xvid_fixed_quant.setText(config.get('mencoder GUI', 'xvid_fixed_quant'))

        if config.has_option('mencoder GUI', 'xvid_me_quality'):
            self.xvid_me_quality.setText(config.get('mencoder GUI', 'xvid_me_quality'))
            
        if config.has_option('mencoder GUI', 'xvid_cartoon'):
            self.xvid_cartoon.setChecked(
                config.get('mencoder GUI', 'xvid_cartoon') == 'True'
                )
                
        if config.has_option('mencoder GUI', 'xvid_interlacing'):
            self.xvid_interlacing.setChecked(
                config.get('mencoder GUI', 'xvid_interlacing') == 'True'
                )
                
        self.set_xvid_cbr(self.xvid_cbr.isChecked())
                
        #x264 options
        
        x264_dropdown_value = 'crf'
        if config.has_option('mencoder GUI', 'x264_dropdown_value'):
            x264_dropdown_value = config.get('mencoder GUI', 'x264_dropdown_value')
            index = self.x264_dropdown.findText(x264_dropdown_value)
            self.x264_dropdown.setCurrentIndex(index)
        
        self.update_crf_qp(x264_dropdown_value)

        if config.has_option('mencoder GUI', 'x264_cbr'):
            self.x264_cbr.setChecked(
                config.get('mencoder GUI', 'x264_cbr') == 'True'
                )
        
        if config.has_option('mencoder GUI', 'x264_bitrate'):
            self.x264_bitrate.setText(config.get('mencoder GUI', 'x264_bitrate'))
            
        if config.has_option('mencoder GUI', 'x264_qp'):
            self.x264_qp.setText(config.get('mencoder GUI', 'x264_qp'))
            
        if config.has_option('mencoder GUI', 'x264_crf'):
            self.x264_crf.setText(config.get('mencoder GUI', 'x264_crf'))
            
        if config.has_option('mencoder GUI', 'x264_extra_opts'):
            self.x264_extra_opts.setText(config.get('mencoder GUI', 'x264_extra_opts'))
                
        if config.has_option('mencoder GUI', 'outputfile'):
            self.outputfile.setText(config.get('mencoder GUI', 'outputfile'))
            
        self.set_x264_cbr(self.x264_cbr.isChecked())
            
            
        #tv parms tab

        if config.has_option('mencoder GUI', 'tvwidth'):
            self.tvwidth.setText(config.get('mencoder GUI', 'tvwidth'))

        if config.has_option('mencoder GUI', 'tvheight'):
            self.tvheight.setText(config.get('mencoder GUI', 'tvheight'))

        if config.has_option('mencoder GUI', 'audiorate'):
            self.audiorate.setText(config.get('mencoder GUI', 'audiorate'))

        if config.has_option('mencoder GUI', 'extratvparms'):
            self.extratvparms.setText(config.get('mencoder GUI', 'extratvparms'))
            
        if config.has_option('mencoder GUI', 'extramplayerparms'):
            self.extramplayerparms.setText(config.get('mencoder GUI', 'extramplayerparms'))

        if config.has_option('mencoder GUI', 'alsa_audio'):
            self.alsa_audio.setChecked(config.get('mencoder GUI', 'alsa_audio') == 'True')

        if config.has_option('mencoder GUI', 'adevice'):
            self.adevice.setText(config.get('mencoder GUI', 'adevice'))

        if config.has_option('mencoder GUI', 'brightness'):
            self.brightnessSlider.setSliderPosition(int(config.get('mencoder GUI', 'brightness')))

        if config.has_option('mencoder GUI', 'contrast'):
            self.contrastSlider.setSliderPosition(int(config.get('mencoder GUI', 'contrast')))

        if config.has_option('mencoder GUI', 'hue'):
            self.hueSlider.setSliderPosition(int(config.get('mencoder GUI', 'hue')))

        if config.has_option('mencoder GUI', 'saturation'):
            self.saturationSlider.setSliderPosition(int(config.get('mencoder GUI', 'saturation')))



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
            self.extramencoderparms.setText(config.get('mencoder GUI',
                                                       'extramencoderparms'))


        #advanced tab
        if config.has_option('mencoder GUI', 'pre_command'):
            self.pre_command.setText(config.get('mencoder GUI', 'pre_command'))

        if config.has_option('mencoder GUI', 'post_command'):
            self.post_command.setText(config.get('mencoder GUI', 'post_command'))

        if config.has_option('mencoder GUI', 'play_while_recording'):
            self.play_while_recording.setChecked(config.get('mencoder GUI',
                'play_while_recording') == 'True')

        if config.has_option('mencoder GUI', 'setenvvars'):
            self.setenvvars.setChecked(config.get('mencoder GUI', 'setenvvars') == 'True')
            
        if config.has_option('mencoder GUI', 'envvars'):
            self.envvars.setPlainText(config.get('mencoder GUI', 'envvars'))


    def update_norm_index_from_config(self):
        try:
            if config.has_option('mencoder GUI', 'norm'):
                norm_name = None
                try:
                    norm_int = int(config.get('mencoder GUI', 'norm'))
                except:
                    norm_int = -1
                    norm_name = config.get('mencoder GUI', 'norm')
                    if norm_name:
                        for i in NORMS_DICT:
                            if NORMS_DICT[i] == norm_name:
                                norm_int = i
                                break
                if norm_int > -1 and not norm_name:
                    norm_name = str(norm_int)
                    self.norm.addItem(norm_name)
                index = self.norm.findText(norm_name)
                self.norm.setCurrentIndex(index)
                self.setFocus()
        except:
            raise

    def update_input_index_from_config(self):
        try:
            if config.has_option('mencoder GUI', 'input'):
                input_name = None
                try:
                    input_int = int(config.get('mencoder GUI', 'input'))
                except:
                    input_int = -1
                    input_name = config.get('mencoder GUI', 'input')
                    if input_name:
                        for i in INPUTS_DICT:
                            if INPUTS_DICT[i] == input_name:
                                input_int = i
                                break
                if input_int > -1 and not input_name:
                    input_name = str(input_int)
                    self.input.addItem(input_name)
                index = self.input.findText(input_name)
                self.input.setCurrentIndex(index)
                self.setFocus()
        except:
            raise
                
    def get_params_from_gui(self, config=False):
        """ Returns a dictionary with the values of the application parameters
            from the gui components. If config is set to true some values
            will be modified so they can be properly saved in the configuration
            file.
        """

        parameters = {}
        
        if self.locale_string is None and config:
            self.locale_string = ""
        parameters['language'] = self.locale_string

        parameters['channel_type'] = self.number_rb.isChecked() and \
            'number' or 'frequency'
        parameters['channel'] = str(self.channel.value())
        parameters['frequency'] = str(self.frequency.value()).replace(",",".")

        if self.duration.time().hour() or self.duration.time().minute() or \
            self.duration.time().second():
            parameters['duration'] = "%.2d:%.2d:%.2d" % (
                                        self.duration.time().hour(),
                                        self.duration.time().minute(),
                                        self.duration.time().second()
                                      )
        else:
            parameters['duration'] = ''

        if config:
            parameters['driver'] = self.driver.currentIndex()
        else:
            parameters['driver'] = str(self.driver.currentText())

        parameters['device'] = str(self.device.text())
        
        norm = self.norm.currentText()
        parameters['norm'] = str(norm)
        
        norm_int = parameters['norm']
        for key, val in NORMS_DICT.items():
            if val == parameters['norm']:
                norm_int = str(key)
                break
        parameters['norm_int'] = norm_int
        
        
        input = self.input.currentText()
        parameters['input'] = str(input)
        
        input_int = parameters['input']
        for key, val in INPUTS_DICT.items():
            if val == parameters['input']:
                input_int = str(key)
                break
        parameters['input_int'] = input_int

        if config:
            parameters['chanlist'] = self.chanlist.currentIndex()
        else:
            parameters['chanlist'] = str(self.chanlist.currentText())

        parameters['audiocodec'] = str(self.audiocodec.currentText())
        parameters['videocodec'] = str(self.videocodec.currentText())

        parameters['append_suffix'] = self.append_suffix.isChecked()

        parameters['lame_audiobitrate'] = str(self.lame_audiobitrate.text())
        parameters['lame_extra_opts'] = str(self.lame_extra_opts.text())

        if config:
            parameters['lavc_audiocodec'] = self.lavc_audiocodec.currentIndex()
        else:
            parameters['lavc_audiocodec'] = \
                str(self.lavc_audiocodec.currentText())

            
        parameters['lavc_audiobitrate'] = str(self.lavc_audiobitrate.text())
        parameters['lavc_audio_extra_opts'] = \
            str(self.lavc_audio_extra_opts.text())

        if config:
            parameters['lavc_videocodec'] = self.lavc_videocodec.currentIndex()
        else:
            parameters['lavc_videocodec'] = \
                str(self.lavc_videocodec.currentText())

        parameters['lavc_videobitrate'] = str(self.lavc_videobitrate.text())
        parameters['lavc_video_extra_opts'] = \
            str(self.lavc_video_extra_opts.text())        
        
        parameters['xvid_cbr'] = self.xvid_cbr.isChecked()
        parameters['xvid_bitrate'] = str(self.xvid_bitrate.text())
        parameters['xvid_extra_opts'] = str(self.xvid_extra_opts.text())
        parameters['xvid_fixed_quant'] = str(self.xvid_fixed_quant.text())
        parameters['xvid_me_quality'] = str(self.xvid_me_quality.text())
        parameters['xvid_cartoon'] = self.xvid_cartoon.isChecked()
        parameters['xvid_interlacing'] = self.xvid_interlacing.isChecked()
        
        parameters['x264_cbr'] = self.x264_cbr.isChecked()
        parameters['x264_bitrate'] = str(self.x264_bitrate.text())
        parameters['x264_dropdown_value'] = str(self.x264_dropdown.currentText())
        parameters['x264_qp'] = str(self.x264_qp.text())
        parameters['x264_crf'] = str(self.x264_crf.text())
        parameters['x264_extra_opts'] = str(self.x264_extra_opts.text())
        
        parameters['outputfile'] = str(self.outputfile.text())

        parameters['tvwidth'] = str(self.tvwidth.text())
        parameters['tvheight'] = str(self.tvheight.text())
        parameters['audiorate'] = str(self.audiorate.text())
        parameters['alsa_audio'] = self.alsa_audio.isChecked()
        parameters['adevice'] = str(self.adevice.text())
        parameters['extratvparms'] = str(self.extratvparms.text())
        parameters['extramplayerparms'] = str(self.extramplayerparms.text())

        parameters['brightness'] = str(self.brightnessSlider.sliderPosition())
        parameters['contrast'] = str(self.contrastSlider.sliderPosition())
        parameters['hue'] = str(self.hueSlider.sliderPosition())
        parameters['saturation'] = str(self.saturationSlider.sliderPosition())

        parameters['noskip'] = self.noskip.isChecked()
        parameters['quiet'] = self.quiet.isChecked()

        parameters['scaleheight'] = str(self.scaleheight.text())
        parameters['scalewidth'] = str(self.scalewidth.text())
        parameters['ofps'] = str(self.ofps.text())
        parameters['extrafilters'] = str(self.extrafilters.text())
        parameters['extramencoderparms'] = str(self.extramencoderparms.text())

        parameters['pre_command'] = str(self.pre_command.text())
        parameters['post_command'] = str(self.post_command.text())
        parameters['play_while_recording'] = \
            self.play_while_recording.isChecked()

        parameters['setenvvars'] = self.setenvvars.isChecked()
        if config:
            parameters['envvars'] = str(self.envvars.toPlainText())
        else:
            envvars = {}
            for lines in str(self.envvars.toPlainText()).split('\n'):
                keyval = lines.split('=', 1)
                if len(keyval) == 2:
                    key = keyval[0].strip()
                    val = keyval[1].strip()
                    envvars[key] = val
            parameters['envvars'] = envvars
        
        if parameters['channel_type'] == 'number':
            parameters['channel_text'] = str(self.channel.value())
        elif parameters['channel_type'] == 'frequency':
            parameters['channel_text'] = \
                str(self.frequency.value()).replace(",",".")

        return parameters



    def preview_with_mplayer(self):
        if not self.mplayer_preview_pid:
            parameters = self.get_params_from_gui()
            cmd = utils.generate_mplayer_command(parameters)
            print "Excecuting %s" % " ".join(cmd)
            env = os.environ.copy()
            if parameters.get('setenvvars'):
                for key, val in parameters.get('envvars').items():
                    env[key] = val
            try:
                self.mplayer_instance = Popen(cmd, stdin=PIPE, env=env)
                self.mplayer_preview_pid = self.mplayer_instance.pid
                self.mplayer_preview_timer.start(1000)
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" %
                                              (" ".join(cmd),))



    def run_mencoder(self, accepted=False):
        if self.mplayer_preview_pid:
            call(['kill', str(self.mplayer_preview_pid)])
            self.mplayer_preview_pid = 0

        parameters = self.get_params_from_gui()

        self.schedule_timer.stop()
        channel_text = parameters.get('channel_text')
        append_suffix = self.append_suffix.isChecked()
        play_while_recording = self.play_while_recording.isChecked()
        filename = utils.make_filename(str(self.outputfile.text()),
                                       channel_text,
                                       append_suffix=append_suffix)

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
                    self.error_dialog.showMessage("excecution of %s failed" %
                                                  (pre_command,))

            cmd = utils.generate_command(parameters)
            env = os.environ.copy()
            if parameters.get('setenvvars'):
                for key, val in parameters.get('envvars').items():
                    env[key] = val
            try:
                self.mencoder_instance = Popen(cmd, env=env)
                self.mencoder_pid = self.mencoder_instance.pid
            except OSError:
                self.error_dialog.showMessage("excecution of %s failed" % " ".join(cmd))

            if self.mencoder_pid:
                self.status_label.setText(self.tr('Recording... %1').arg(
                    utils.secs_to_str(self.time_running)
                    ))
                self.checker_timer.start(1000)
                self.scheduleButton.setEnabled(False)
                self.cancel_sheduleButton.setEnabled(False)
                if play_while_recording:
                    self.preview_file_timer.start(2000)
            else:
                self.stopButton.setEnabled(False)
                self.runButton.setEnabled(True)


    def show_available_audio_codecs(self):
        dialog = InfoDialog(self)
        text = "If for some reason the dropdown list with the supported codecs is not correct\n" \
               "the following is the list of supported codecs. You may type any of them in the\n" \
               "text field\n\n"
        text += utils.get_codecs('mencoder -oac help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def show_available_video_codecs(self):
        dialog = InfoDialog(self)
        text = "If for some reason the dropdown list with the supported codecs is not correct\n" \
               "the following is the list of supported codecs. You may type any of them in the\n" \
               "text field\n\n"
        text += utils.get_codecs('mencoder -ovc help')
        dialog.plainTextEdit.setPlainText(text)
        dialog.show()

    def stop_button_pressed(self):
        if self.mencoder_pid:
            call(['kill', str(self.mencoder_pid)])
            self.mencoder_pid = 0
        self.record_stop_cleanup()

    def channel_changed(self, channel):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_channel %s\n' %
                                                  (str(channel),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def frequency_changed(self, freq):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_freq %s\n' %
                                                  (str(freq),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def brightness_changed(self, brightness):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_brightness %s\n' %
                                                  (str(brightness),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def contrast_changed(self, contrast):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_contrast %s\n' %
                                                  (str(contrast),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def hue_changed(self, hue):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_hue %s\n' %
                                                  (str(hue),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def saturation_changed(self, saturation):
        if self.mplayer_preview_pid:
            try:
                self.mplayer_instance.stdin.write('tv_set_saturation %s\n' %
                                                  (str(saturation),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")

    def norm_changed(self, norm):
        if self.mplayer_preview_pid:
            norm = NORMS_DICT.get(norm, 'NTSC')
            try:
                self.mplayer_instance.stdin.write('tv_set_norm %s\n' %
                                                  (str(norm),))
            except:
                self.error_dialog.showMessage("communication with mplayer failed")
                
                
    def update_device_values(self):
        global config, NORMS_DICT, INPUTS_DICT
        parameters = self.get_params_from_gui()
        preview_command = \
            utils.generate_mplayer_command(parameters,
                                           extra_params=['-vo', 'null',
                                                         '-ao', 'null',
                                                         '-frames', '0'],
                                           as_string=True)
        dev_info = utils.get_device_information(preview_command)
        norms = dev_info['norms']
        inputs = dev_info['inputs']
        
        self.norm.clear()
        
        if norms:
           for norm_id, norm_value in norms:
                self.norm.addItem(norm_value)
                NORMS_DICT[int(norm_id)] = norm_value
                
        self.update_norm_index_from_config()
        
        self.input.clear()
        
        if inputs:
           for input_id, input_value in inputs:
                self.input.addItem(input_value)
                INPUTS_DICT[int(input_id)] = input_value
                
        self.update_input_index_from_config()

    def preview_command(self):
        appTranslator = QtCore.QTranslator()
        appTranslator.load("")
        app.installTranslator(appTranslator)
        self.retranslateUi(self)
        parameters = self.get_params_from_gui()
        self.previewcommand.setText(utils.generate_command(parameters,
                                                           preview=True))

    def save_configuration(self, config_filename=None):
        parameters = self.get_params_from_gui(config=True)
        utils.save_configuration(parameters, config_filename=config_filename)

    def set_xvid_cbr(self, is_cbr):
        if is_cbr:
            self.xvid_bitrate.show()
            self.xvid_bitrate_label.show()
            self.xvid_fixed_quant.hide()
            self.xvid_fixed_quant_label.hide()
        else:
            self.xvid_bitrate.hide()
            self.xvid_bitrate_label.hide()
            self.xvid_fixed_quant.show()
            self.xvid_fixed_quant_label.show()
            
    def set_x264_cbr(self, is_cbr):
        if is_cbr:
            self.x264_bitrate.show()
            self.x264_bitrate_label.show()
            self.x264_dropdown.hide()
            self.x264_crf.hide()
            self.x264_qp.hide()
        else:
            self.x264_bitrate.hide()
            self.x264_bitrate_label.hide()
            self.x264_dropdown.show()
            value = str(self.x264_dropdown.currentText())
            self.update_crf_qp(value)

            
    def update_crf_qp(self, value):
        if value == 'crf':
            self.x264_crf.show()
            self.x264_qp.hide()
        else:
            self.x264_crf.hide()
            self.x264_qp.show()

        
    def change_language(self, locale_string=None):
        self.locale_string = locale_string
        if self.translator:
            app.removeTranslator(self.translator)
        translation = utils.find_translation(locale_string=locale_string)
        appTranslator = QtCore.QTranslator()
        appTranslator.load(translation)
        app.installTranslator(appTranslator)
        self.translator = appTranslator
        self.retranslateUi(self)
        
    def changeToEnglish(self):
        self.locale_string = "en"
        self.change_language(self.locale_string)
        
    def changeToSpanish(self):
        self.locale_string = "es"
        self.change_language(self.locale_string)
        
    def changeToSpanish_Argentina(self):
        self.locale_string = "es_AR"
        self.change_language(self.locale_string)

    def changeToItalian(self):
        self.locale_string = "it"
        self.change_language(self.locale_string)
        
    def changeToGerman(self):
        self.locale_string = "de"
        self.change_language(self.locale_string)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    status = app.exec_()
    win.exit_cleanup()
    sys.exit(status)
