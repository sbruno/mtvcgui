# -*- coding: utf-8 -*-

# Author: Santiago Bruno
# License: GPL v3
# Web pages: http://www.santiagobruno.com.ar/programas.html
#            http://code.google.com/p/mtvcgui/

import locale
import os
import commands
import re
import time
import ConfigParser

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

def secs_to_str(seconds):
    secs = seconds % 60
    mins_left = seconds / 60
    mins = mins_left % 60
    hours = mins_left / 60

    return "%.2d:%.2d:%.2d" % (hours, mins, secs)


def saveConfiguration(parameters):

    config = ConfigParser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), '.mtvcgui')
    config_filename = os.path.join(config_dir, 'mtvcgui.ini')
    config.read(config_filename)

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
    config.set('mencoder GUI', 'lame_audiobitrate', parameters.get('lame_audiobitrate'))
    config.set('mencoder GUI', 'lavc_videocodec', parameters.get('lavc_videocodec'))
    config.set('mencoder GUI', 'lavc_videobitrate', parameters.get('lavc_videobitrate'))
    config.set('mencoder GUI', 'outputfile', parameters.get('outputfile'))

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
    config.set('mencoder GUI', 'play_while_recording', parameters.get('play_while_recording'))

    if not os.path.exists(config_dir):
        try:
            os.mkdir(config_dir)
        except:
            print "Error trying to create %s" % (config_dir, )


    try:
        config_file = open(config_filename, 'w')
        config.write(config_file)
        config_file.close()
    except:
        print "Error trying to save configuration to %s" % (config_filename, )


def generateCommand(parameters, preview=False):
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
    lame_audiobitrate = parameters.get('lame_audiobitrate')
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

    channel_text = parameters.get('channel_text')

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
        mencoderparms += ['-oac', audiocodec]

    mencoderparms += ['-ovc', videocodec]

    if duration:
        mencoderparms += ['-endpos', duration]

    if ofps:
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

        mencoderparms += ['-lavcopts', lavcopts]

    if lame_audiobitrate:
        mencoderparms += ['-lameopts', 'cbr:br=' + lame_audiobitrate]


    if extramencoderparms:
        for extraparm in extramencoderparms.split(' '):
            mencoderparms.append(extraparm)

    mencoderparms += ['-o', outputfile]

    command = ['mencoder', 'tv://'] + mencoderparms

    if preview:
        return " ".join(command)
    else:
        return command


def generateMplayerCommand(parameters):

    channel_type = parameters.get('channel_type', 'number')
    channel = parameters.get('channel')
    frequency = parameters.get('frequency')
    driver = parameters.get('driver')
    device = parameters.get('device')
    norm = parameters.get('norm')
    input = parameters.get('input')
    chanlist = parameters.get('chanlist')
    tvwidth = parameters.get('tvwidth')
    tvheight = parameters.get('tvheight')
    extratvparms = parameters.get('extratvparms')
    audiorate = parameters.get('audiorate')
    alsa_audio = parameters.get('alsa_audio')
    adevice = parameters.get('adevice')
    scaleheight = parameters.get('scaleheight')
    scalewidth = parameters.get('scalewidth')
    ofps = parameters.get('ofps')
    extrafilters = parameters.get('extrafilters')


    channel_text = parameters.get('channel_text')

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

    if ofps:
        mencoderparms += ['-fps', ofps]

    mencoderparms.append('-quiet')

    if extrafilters or (scalewidth and scaleheight):
        filters = []
        if extrafilters:
            filters.append(extrafilters)
        if scaleheight:
            filters.append("scale=%s:%s" % (scalewidth, scaleheight) )

        filters = ','.join(filters)

        mencoderparms += ['-vf', filters]


    return ['mplayer', 'tv://'] + mencoderparms
