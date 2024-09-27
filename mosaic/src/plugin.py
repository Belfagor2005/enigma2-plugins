#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mosaic by AliAbdul
# new screens (4/9 switchable) recalculated for hd/fhd by mrvica
# recoded from lululla 20240919 reference channel shot and add console

# from . import _
from Components.ActionMap import NumberActionMap
from Components.config import config, ConfigSubsection, ConfigInteger
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.VideoWindow import VideoWindow
from enigma import (
    eServiceCenter,
    eTimer,
    getDesktop,
    loadJPG,
    ePicLoad,
    eServiceReference,
)
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import BouquetSelector
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from time import sleep
from os.path import exists as file_exists
import re
import sys

from .Console import Console as MyConsole


try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch


PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    from urllib.parse import quote
    from urllib.parse import unquote
else:
    from urllib import quote
    from urllib import unquote


global firstscrennshot
firstscrennshot = True

grab_binary = "/usr/bin/grab"
grab_errorlog = "/tmp/mosaic.log"

config_limits = (3, 30)
config.plugins.Mosaic = ConfigSubsection()
config.plugins.Mosaic.countdown = ConfigInteger(default=5, limits=config_limits)
config.plugins.Mosaic.howmanyscreens = ConfigInteger(default=9)

plugin_name = "Mosaic"
plugin_description = "Mosaic 9/4 Screens"
plugin_icon = 'icon.png'


def isFHD():
    screenwidth = getDesktop(0).size()
    if screenwidth.width() >= 1920:
        FHD = True
        return FHD


def getScale():
    return AVSwitch().getFramebufferScale()


REGEX = re.compile(
    r'[\(\[].*?[\)\]]|'                    # Parentesi tonde o quadre
    r':?\s?odc\.\d+|'                      # odc. con o senza numero prima
    r'\d+\s?:?\s?odc\.\d+|'                # numero con odc.
    r'[:!]|'                               # due punti o punto esclamativo
    r'\s-\s.*|'                            # trattino con testo successivo
    r',|'                                  # virgola
    r'/.*|'                                # tutto dopo uno slash
    r'\|\s?\d+\+|'                         # | seguito da numero e +
    r'\d+\+|'                              # numero seguito da +
    r'\s\*\d{4}\Z|'                        # * seguito da un anno a 4 cifre
    r'[\(\[\|].*?[\)\]\|]|'                # Parentesi tonde, quadre o pipe
    r'(?:\"[\.|\,]?\s.*|\"|'               # Testo tra virgolette
    r'\.\s.+)|'                            # Punto seguito da testo
    r'Премьера\.\s|'                       # Specifico per il russo
    r'[хмтдХМТД]/[фс]\s|'                  # Pattern per il russo con /ф o /с
    r'\s[сС](?:езон|ерия|-н|-я)\s.*|'      # Stagione o episodio in russo
    r'\s\d{1,3}\s[чсЧС]\.?\s.*|'           # numero di parte/episodio in russo
    r'\.\s\d{1,3}\s[чсЧС]\.?\s.*|'         # numero di parte/episodio in russo con punto
    r'\s[чсЧС]\.?\s\d{1,3}.*|'             # Parte/Episodio in russo
    r'\d{1,3}-(?:я|й)\s?с-н.*',            # Finale con numero e suffisso russo
    re.DOTALL)


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace('"', '').replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '').replace('.', '').replace(' | ', '')
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '')
        eventName = eventName.replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '')
        eventName = eventName.replace('(0+)', '').replace('0+', '').replace('+', '')
        eventName = eventName.replace('episode', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def remove_accents(string):
    import unicodedata
    if PY3 is False:
        if type(string) is not unicode:
            string = unicode(string, encoding='utf-8')
    string = unicodedata.normalize('NFD', string)
    string = re.sub(r'[\u0300-\u036f]', '', string)
    return string


def dataenc(data):
    if PY3:
        data = data.decode("utf-8")
    else:
        data = data.encode("utf-8")
    return data


def convtext(text=''):
    try:
        if text != '' or text is not None or text != 'None':
            print('original text: ', text)
            text = text.lower()
            text = remove_accents(text)
            text = cutName(text)
            text = getCleanTitle(text)
            text = text.replace(' ', '')
            text = text.strip(' -').strip(' ')
            text = quote(text, safe="")
        else:
            text = text
        return unquote(text)
    except Exception as e:
        print('convtext error: ', e)
        pass
    return unquote(text)


class Mosaic(Screen):
    PLAY = 0
    PAUSE = 1

    global windowWidth, windowHeight

    desktop = getDesktop(0)
    size = desktop.size()
    width = size.width()
    height = size.height()

    if isFHD():
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            windowWidth = width / 4 + 102
            windowHeight = height / 4 + 30
            positions = []
            x = 45
            y = 45
            for i in range(1, 10):
                positions.append([x, y])
                x += windowWidth
                x += ((width - 81) - (windowWidth * 3)) / 2
                if (i == 3) or (i == 6):
                    y = y + windowHeight + 45
                    x = 45
        else:
            windowWidth = width / 2 - 75    # 885
            windowHeight = height / 2 - 68   # 473
            positions = []
            x = 45
            y = 45
            for i in range(1, 5):
                positions.append([x, y])
                x += windowWidth
                x += ((width - 90) - (windowWidth * 2))
                if (i == 2):
                    y = y + windowHeight + 45
                    x = 45
    else:
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            windowWidth = width / 4 + 68
            windowHeight = height / 4 + 20
            positions = []
            x = 30
            y = 30
            for i in range(1, 10):
                positions.append([x, y])
                x += windowWidth
                x += ((width - 54) - (windowWidth * 3)) / 2
                if (i == 3) or (i == 6):
                    y = y + windowHeight + 30
                    x = 30
        else:
            windowWidth = width / 2 - 50    # 590
            windowHeight = height / 2 - 45  # 315
            positions = []
            x = 30
            y = 30
            for i in range(1, 5):
                positions.append([x, y])
                x += windowWidth
                x += ((width - 60) - (windowWidth * 2))
                if (i == 2):
                    y = y + windowHeight + 30
                    x = 30

    if isFHD:
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            skin = ""
            skin += """<screen position="0,0" size="%d,%d" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >""" % (width, height)
            skin += """<eLabel font="Regular;27" backgroundColor="#ffffff" foregroundColor="#0000ff00" borderWidth="1" zPosition="4" borderColor="#0000ff00" position="927,1035" size="40,40" text=">" />"""
            skin += """<eLabel font="Regular;27" backgroundColor="#ffffff" foregroundColor="#00ffa000" borderWidth="1" zPosition="4" borderColor="#00ffa000" position="971,1035" size="40,40" text="||" />"""
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[4][0] - 3, positions[4][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[5][0] - 3, positions[5][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[6][0] - 3, positions[6][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[7][0] - 3, positions[7][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[8][0] - 3, positions[8][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="channel1" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[0][0], positions[0][1] - 33, windowWidth - 6)
            skin += """<widget name="channel2" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[1][0], positions[1][1] - 33, windowWidth - 6)
            skin += """<widget name="channel3" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[2][0], positions[2][1] - 33, windowWidth - 6)
            skin += """<widget name="channel4" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[3][0], positions[3][1] - 33, windowWidth - 6)
            skin += """<widget name="channel5" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[4][0], positions[4][1] - 33, windowWidth - 6)
            skin += """<widget name="channel6" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[5][0], positions[5][1] - 33, windowWidth - 6)
            skin += """<widget name="channel7" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[6][0], positions[6][1] - 33, windowWidth - 6)
            skin += """<widget name="channel8" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[7][0], positions[7][1] - 33, windowWidth - 6)
            skin += """<widget name="channel9" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[8][0], positions[8][1] - 33, windowWidth - 6)
            skin += """<widget name="window1" scale="1" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window2" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window3" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window4" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window5" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[4][0] - 3, positions[4][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window6" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[5][0] - 3, positions[5][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window7" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[6][0] - 3, positions[6][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window8" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[7][0] - 3, positions[7][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window9" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[8][0] - 3, positions[8][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video1" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video2" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video3" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video4" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video5" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[4][0] - 3, positions[4][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video6" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[5][0] - 3, positions[5][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video7" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[6][0] - 3, positions[6][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video8" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[7][0] - 3, positions[7][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video9" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[8][0] - 3, positions[8][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="event1" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth)
            skin += """<widget name="event2" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth)
            skin += """<widget name="event3" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth)
            skin += """<widget name="event4" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth)
            skin += """<widget name="event5" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[4][0] - 3, positions[4][1] - 2, windowWidth)
            skin += """<widget name="event6" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[5][0] - 3, positions[5][1] - 2, windowWidth)
            skin += """<widget name="event7" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[6][0] - 3, positions[6][1] - 2, windowWidth)
            skin += """<widget name="event8" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[7][0] - 3, positions[7][1] - 2, windowWidth)
            skin += """<widget name="event9" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[8][0] - 3, positions[8][1] - 2, windowWidth)
            skin += """<widget name="countdown" position="45,%d" size="200,30" font="Regular;27" zPosition="4" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (height - 45)  # , windowWidth)
            skin += """<eLabel backgroundColor="#001d283c" cornerRadius="30" position="765,1032" zPosition="2" size="390,45" />"""
            skin += """<widget name="button" position="1014,1035" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mosaic/blue.png" zPosition="3" alphatest="on" />"""
            skin += """<widget name="count" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
            </screen>""" % (positions[2][0], height - 45, windowWidth)
        else:
            skin = ""
            skin += """<screen position="0,0" size="%d,%d" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >""" % (width, height)
            skin += """<eLabel font="Regular;27" backgroundColor="#ffffff" foregroundColor="#0000ff00" borderWidth="1" zPosition="4" borderColor="#0000ff00" position="927,1035" size="40,40" text=">" />"""
            skin += """<eLabel font="Regular;27" backgroundColor="#ffffff" foregroundColor="#00ffa000" borderWidth="1" zPosition="4" borderColor="#00ffa000" position="971,1035" size="40,40" text="||" />"""
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="channel1" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[0][0], positions[0][1] - 33, windowWidth - 6)
            skin += """<widget name="channel2" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[1][0], positions[1][1] - 33, windowWidth - 6)
            skin += """<widget name="channel3" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[2][0], positions[2][1] - 33, windowWidth - 6)
            skin += """<widget name="channel4" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[3][0], positions[3][1] - 33, windowWidth - 6)
            skin += """<widget name="window1" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window2" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window3" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="window4" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video1" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video2" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video3" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="video4" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth, windowHeight)
            skin += """<widget name="event1" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[0][0] - 3, positions[0][1] - 2, windowWidth)
            skin += """<widget name="event2" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[1][0] - 3, positions[1][1] - 2, windowWidth)
            skin += """<widget name="event3" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[2][0] - 3, positions[2][1] - 2, windowWidth)
            skin += """<widget name="event4" position="%d,%d" size="%d,30" zPosition="3" font="Regular;26" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[3][0] - 3, positions[3][1] - 2, windowWidth)
            skin += """<widget name="countdown" position="45,%d" size="200,30" font="Regular;27" zPosition="4" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (height - 45)  # , windowWidth)
            skin += """<eLabel backgroundColor="#001d283c" cornerRadius="30" position="765,1032" zPosition="2" size="390,45" />"""
            skin += """<widget name="button" position="1014,1035" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mosaic/blue.png" zPosition="3" alphatest="on" />"""
            skin += """<widget name="count" position="%d,%d" size="%d,30" font="Regular;27" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
            </screen>""" % (positions[2][0], height - 45, windowWidth + 945)

    else:
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            skin = ""
            skin += """<screen position="0,0" size="%d,%d" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >""" % (width, height)
            skin += """<eLabel font="Regular;22" backgroundColor="#ffffff" foregroundColor="#0000ff00" borderWidth="1" zPosition="4" borderColor="#0000ff00" position="610,678" size="40,40" text="&gt;" />"""
            skin += """<eLabel font="Regular;22" backgroundColor="#ffffff" foregroundColor="#00ffa000" borderWidth="1" zPosition="4" borderColor="#00ffa000" position="647,678" size="40,40" text="||" />"""
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="channel1" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[0][0], positions[0][1] - 22, windowWidth - 4)
            skin += """<widget name="channel2" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[1][0], positions[1][1] - 22, windowWidth - 4)
            skin += """<widget name="channel3" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[2][0], positions[2][1] - 22, windowWidth - 4)
            skin += """<widget name="channel4" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[3][0], positions[3][1] - 22, windowWidth - 4)
            skin += """<widget name="channel5" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[4][0], positions[4][1] - 22, windowWidth - 4)
            skin += """<widget name="channel6" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[5][0], positions[5][1] - 22, windowWidth - 4)
            skin += """<widget name="channel7" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[6][0], positions[6][1] - 22, windowWidth - 4)
            skin += """<widget name="channel8" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[7][0], positions[7][1] - 22, windowWidth - 4)
            skin += """<widget name="channel9" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[8][0], positions[8][1] - 22, windowWidth - 4)
            skin += """<widget name="window1" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window2" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window3" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window4" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window5" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window6" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window7" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window8" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window9" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video1" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video2" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video3" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video4" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video5" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video6" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video7" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video8" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video9" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="event1" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth)
            skin += """<widget name="event2" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth)
            skin += """<widget name="event3" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth)
            skin += """<widget name="event4" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth)
            skin += """<widget name="event5" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth)
            skin += """<widget name="event6" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth)
            skin += """<widget name="event7" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth)
            skin += """<widget name="event8" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth)
            skin += """<widget name="event9" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth)
            skin += """<widget name="countdown" position="30,%d" size="200,20" font="Regular;18" zPosition="4" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (height - 30)  # , windowWidth)
            skin += """<eLabel backgroundColor="#001d283c" cornerRadius="30" position="457,675" zPosition="2" size="390,45" />"""
            skin += """<widget name="button" position="690,678" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mosaic/blue.png" zPosition="3" alphatest="on" />"""
            skin += """<widget name="count" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
            </screen>""" % (positions[2][0], height - 30, windowWidth)
        else:
            skin = ""
            skin += """<screen position="0,0" size="%d,%d" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >""" % (width, height)
            skin += """<eLabel font="Regular;22" backgroundColor="#ffffff" foregroundColor="#0000ff00" borderWidth="1" zPosition="4" borderColor="#0000ff00" position="610,678" size="40,40" text="&gt;" />"""
            skin += """<eLabel font="Regular;22" backgroundColor="#ffffff" foregroundColor="#00ffa000" borderWidth="1" zPosition="4" borderColor="#00ffa000" position="647,678" size="40,40" text="||" />"""
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="channel1" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[0][0], positions[0][1] - 22, windowWidth - 4)
            skin += """<widget name="channel2" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[1][0], positions[1][1] - 22, windowWidth - 4)
            skin += """<widget name="channel3" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[2][0], positions[2][1] - 22, windowWidth - 4)
            skin += """<widget name="channel4" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[3][0], positions[3][1] - 22, windowWidth - 4)
            skin += """<widget name="window1" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window2" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window3" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="window4" scale="stretch" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video1" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video2" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video3" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="video4" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
            skin += """<widget name="event1" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth)
            skin += """<widget name="event2" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth)
            skin += """<widget name="event3" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth)
            skin += """<widget name="event4" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth)
            skin += """<widget name="countdown" position="30,%d" size="200,20" font="Regular;18" zPosition="4" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (height - 30)  # , windowWidth)
            skin += """<eLabel backgroundColor="#001d283c" cornerRadius="30" position="457,675" zPosition="2" size="390,45" />"""
            skin += """<widget name="button" position="690,678" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/mosaic/blue.png" zPosition="3" alphatest="on" />"""
            skin += """<widget name="count" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
            </screen>""" % (positions[2][0], height - 30, windowWidth + 630)

    def __init__(self, session, services):
        Screen.__init__(self, session)
        self.skin = Mosaic.skin
        print('self.skin=\n', self.skin)
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.consoleCmd = ""
        self.Console = MyConsole()
        self.serviceHandler = eServiceCenter.getInstance()
        self.ref_list = services
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            self.window_refs = [None, None, None, None, None, None, None, None, None]
        else:
            self.window_refs = [None, None, None, None]

        self.countdown = config.plugins.Mosaic.countdown.value
        self.howmanyscreens = config.plugins.Mosaic.howmanyscreens.value

        global firstscrennshot
        firstscrennshot = True

        self.idd = 0
        self.current_refidx = 0
        self.current_window = 1
        self.working = False
        self.state = self.PLAY

        self.windowWidth = windowWidth
        self.windowHeight = windowHeight

        # self["playState"] = Pixmap()
        if config.plugins.Mosaic.howmanyscreens.value == 9:
            for i in range(1, 10):
                self["window" + str(i)] = Pixmap()
                self["video" + str(i)] = VideoWindow(decoder=0, fb_width=int(self.windowWidth), fb_height=int(self.windowHeight))
                # self["video" + str(i)] = VideoWindow(decoder=0, fb_width=self.width, fb_height=self.height)
                self["video" + str(i)].hide()
                self["channel" + str(i)] = Label("")
                self["event" + str(i)] = Label("")
                self["event" + str(i)].hide()
        else:
            for i in range(1, 5):
                self["window" + str(i)] = Pixmap()
                # self["video" + str(i)] = VideoWindow(decoder=0, fb_width=self.width, fb_height=self.height)
                self["video" + str(i)] = VideoWindow(decoder=0, fb_width=int(self.windowWidth), fb_height=int(self.windowHeight))
                self["video" + str(i)].hide()
                self["channel" + str(i)] = Label("")
                self["event" + str(i)] = Label("")
                self["event" + str(i)].hide()
        self["video1"].decoder = 0
        self["video1"].show()
        self["countdown"] = Label()
        self.updateCountdownLabel()
        self["count"] = Label()
        self["button"] = Pixmap()
        # if config.plugins.Mosaic.howmanyscreens.value == 9:
        self["actions"] = NumberActionMap(["MosaicActions"],
                                          {"ok": self.exit,
                                           "cancel": self.closeWithOldService,
                                           "green": self.play,
                                           "yellow": self.pause,
                                           "blue": self.toggleScreens,
                                           "channelup": self.countdownPlus,
                                           "channeldown": self.countdownMinus,
                                           "displayHelp": self.showHelp,
                                           "1": self.numberPressed,
                                           "2": self.numberPressed,
                                           "3": self.numberPressed,
                                           "4": self.numberPressed,
                                           "5": self.numberPressed,
                                           "6": self.numberPressed,
                                           "7": self.numberPressed,
                                           "8": self.numberPressed,
                                           "9": self.numberPressed}, prio=-1)

        self.PicLoad = ePicLoad()
        self.updateTimer = eTimer()
        if file_exists('/var/lib/dpkg/status'):
            self.updateTimer_conn = self.updateTimer.timeout.connect(self.updateCountdown)
        else:
            self.updateTimer.callback.append(self.updateCountdown)

        self.checkTimer = eTimer()
        if file_exists('/var/lib/dpkg/status'):
            self.checkTimer_conn = self.checkTimer.timeout.connect(self.checkGrab)
        else:
            self.checkTimer.callback.append(self.checkGrab)
        self.checkTimer.start(500, True)

    def isStandardMosaic(self):
        return self.__class__.__name__ == "Mosaic"

    def toggleScreens(self):
        try:
            self.checkTimer.stop()
            self.updateTimer.stop()
            howmanyscreens = config.plugins.Mosaic.howmanyscreens.value
            if howmanyscreens == 9:
                howmanyscreens = 4
                self.session.open(MessageBox, "switching to %d Screens\nrestart e2 and launch Mosaic again" % howmanyscreens, MessageBox.TYPE_INFO, timeout=5)
            elif howmanyscreens == 4:
                howmanyscreens = 9
                self.session.open(MessageBox, "switching to %d Screens\nrestart e2 and launch Mosaic again" % howmanyscreens, MessageBox.TYPE_INFO, timeout=5)
            config.plugins.Mosaic.howmanyscreens.value = howmanyscreens
            config.plugins.Mosaic.howmanyscreens.save()
        except:
            pass

    def showHelp(self):
        self.session.open(MessageBox, '%s' % 'CH+/CH- : countdown to next screen in secs (3-30)\nGreen : play Mosaic\nYellow : pause Mosaic\nBlue : toggle 9/4 screens\n1-9(4) : switch to screen 1-9(4) and leave\nOK : switch to current screen and leave\nExit : leave to previously service\nHelp : this help', MessageBox.TYPE_INFO, close_on_any_key=True)

    def checkGrab(self):
        # Start the first service in the bouquet and show the service-name
        try:
            '''
            # if self.current_refidx > (len(self.ref_list) - 1):
                # self.current_refidx = 0
            '''
            # Play next ref
            ref = self.ref_list[self.current_refidx]
            # ref = self.ref_list[0]  # ref = self.ref_list[self.current_refidx]  # have a crash ?? why?
            self.window_refs[0] = ref
            info = self.serviceHandler.info(ref)
            name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
            event_name = self.getEventName(info, ref)

            # first name screen
            self.name_name_grab = (convtext(name))
            print('name self.name_name_grab=', self.name_name_grab)

            self["channel1"].setText(name)
            self["event1"].setText(event_name)
            self.session.nav.playService(ref)
            self["count"].setText("Channel: " + "1 / " + str(len(self.ref_list)))
            # self["playState"].instance.setPixmap(playingIcon)
            # Start updating the video-screenshots
            self.updateTimer.start(1, True)
        except Exception as e:
            print('error checkGrab:', e)

    def name_grab(self):
        # make show the service-name for next screen
        ref = self.ref_list[self.current_refidx]
        info = self.serviceHandler.info(ref)
        name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
        self.name_name_grab = (convtext(name))
        # self["playState"].instance.setPixmap(playingIcon)
        return self.name_name_grab

    def exit(self, callback=None):
        self.deleteConsoleCallbacks()
        self.close()

    def deleteConsoleCallbacks(self):
        if self.consoleCmd in self.Console.appContainers:
            try:
                del self.Console.appContainers[self.consoleCmd].dataAvail[:]
            except Exception as e:
                print('error del self.Console.appContainers[self.consoleCmd].dataAvail[:]', e)
            try:
                del self.Console.appContainers[self.consoleCmd].appClosed[:]
            except Exception as e:
                print('error del self.Console.appContainers[self.consoleCmd].appClosed[:]', e)
            try:
                del self.Console.appContainers[self.consoleCmd]
            except Exception as e:
                print('error del self.Console.appContainers[self.consoleCmd]', e)
            try:
                del self.Console.extra_args[self.consoleCmd]
            except Exception as e:
                print('error del self.Console.extra_args[self.consoleCmd]', e)
            try:
                del self.Console.callbacks[self.consoleCmd]
            except Exception as e:
                print('error del self.Console.callbacks[self.consoleCmd]', e)

    def closeWithOldService(self):
        try:
            self.session.nav.playService(self.oldService)
            self.deleteConsoleCallbacks()
            self.deletefilescreen()
            self.close()
        except:
            pass

    def deletefilescreen(self:)
        self.directory = '/tmp'
        pattern = re.compile(r'^[0-9]+.*')
        for filename in os.listdir(self.directory):
            if pattern.match(filename):
                file_path = os.path.join(self.directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print("Rimosso:", file_path)


    def numberPressed(self, number):
        try:
            ref = self.window_refs[number - 1]
            if ref is not None:
                self.session.nav.playService(ref)
                self.deleteConsoleCallbacks()
                self.close()
        except:
            pass

    def play(self):
        try:
            if self.working is False and self.state == self.PAUSE:
                self.state = self.PLAY
                self.updateTimer.start(1000, 1)
        except:
            pass

    def pause(self):
        try:
            if self.working is False and self.state == self.PLAY:
                self.state = self.PAUSE
                self.updateTimer.stop()
        except:
            pass

    def countdownPlus(self):
        try:
            self.changeCountdown(1)
        except:
            pass

    def countdownMinus(self):
        try:
            self.changeCountdown(-1)
        except:
            pass

    def changeCountdown(self, direction):
        try:
            if self.working is False:
                configNow = config.plugins.Mosaic.countdown.value
                configNow += direction
                if configNow < config_limits[0]:
                    configNow = config_limits[0]
                elif configNow > config_limits[1]:
                    configNow = config_limits[1]
                config.plugins.Mosaic.countdown.value = configNow
                config.plugins.Mosaic.countdown.save()
                self.updateCountdownLabel()
        except:
            pass

    def createSummary(self):
        return Mosaic

    def getCurrentServiceReference(self):
        print('Ritorna il riferimento al servizio attualmente in riproduzione.')
        import NavigationInstance
        playingref = None
        if NavigationInstance.instance:
            playingref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        return playingref

    def makeNextScreenshot(self):
        try:
            global firstscrennshot
            self.namepic = ''
            print('1 firstscrennshot * =', firstscrennshot)
            if firstscrennshot:
                self.idd = 0
                firstscrennshot = False
                self.namepic = str(self.idd) + self.name_name_grab  # self.name_grab()
            else:
                self.idd += 1
                self.namepic = str(self.idd) + self.name_next_grab
            print('self.name_grab() =', self.name_grab())

            # Hide all screen window
            self.hide()

            print('Ottieni il riferimento del canale attualmente in riproduzione')
            current_service_ref = self.getCurrentServiceReference()
            # print('1 current_service_ref=', current_service_ref)
            # Verifica se c'è un servizio in riproduzione
            if current_service_ref:
                # print('2 current_service_ref=', current_service_ref)
                #
                service_ref = current_service_ref.toString()
                print('service_ref')
                """Fa uno screenshot del canale specificato."""

                # Imposta il canale specifico
                service = eServiceReference(service_ref)
                self.session.nav.playService(service)
                # print('Aspetta un secondo per permettere il cambio canale')
            sleep(2)
            print('Pic Name=', self.namepic)
            print('Make screenshot')
            print('Width screen -r %d self.windowWidth=', self.windowWidth)
            self.consoleCmd = "%s -v -q -r %d -p /tmp/%s.png" % (grab_binary, self.windowWidth, self.namepic)
            # self.consoleCmd = "%s -v -q -r %d -j 100 /tmp/%s.jpg" % (grab_binary, self.windowWidth, self.namepic)
            self.Console.ePopen(self.consoleCmd, self.showNextScreenshot)
        except:
            pass

    def showNextScreenshot(self, result, retval, extra_args):
        try:
            if retval == 0:
                self.picx = extra_args  # return from console name file. ;)
                self["window" + str(self.current_window)].instance.setPixmap(loadJPG(self.picx))
                # # self["window" + str(self.current_window)].instance.setPixmap(pic)
                # # self["window" + str(self.current_window)].instance.setPixmap(pic)

                # Show all screen window
                self.show()

                # Hide current video-window and show the running event-name
                # self["video" + str(self.current_window)].hide()
                # # self["event" + str(self.current_window)].show()

                # Get next ref
                self.current_refidx += 1
                if self.current_refidx > (len(self.ref_list) - 1):
                    self.current_refidx = 0

                # # Play next ref
                ref = self.ref_list[self.current_refidx]
                info = self.serviceHandler.info(ref)
                name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
                event_name = self.getEventName(info, ref)
                self.session.nav.playService(ref)

                # Hide current video-window and show the running event-name
                self["video" + str(self.current_window)].hide()

                # Get next window index
                self.current_window += 1
                if config.plugins.Mosaic.howmanyscreens.value == 9:
                    if self.current_window > 9:
                        self.current_window = 1
                else:
                    if self.current_window > 4:
                        # Get next window index
                        self.current_window = 1

                # Save the ref
                self.window_refs[self.current_window - 1] = ref

                # Save the event-name and hide the label
                self["event" + str(self.current_window)].hide()
                self["event" + str(self.current_window)].setText(event_name)

                # Show the new video-window
                self["video" + str(self.current_window)].show()
                self["video" + str(self.current_window)].decoder = 0

                # Show the servicename
                self["channel" + str(self.current_window)].setText(name)
                self["count"].setText("Channel: " + str(self.current_refidx + 1) + " / " + str(len(self.ref_list)))

                # name for next pic
                self.name_next_grab = (convtext(name))
                print('showNextScreenshot name_next_grab=', self.name_next_grab)

                # Restart timer
                self.working = False
                self.updateTimer.start(1, True)
            else:
                print(("[Mosaic] retval: %d result: %s" % (retval, result)))
                try:
                    with open("/tmp/mosaic.log", "a") as f:
                        f.write("retval: %d\nresult: %s" % (retval, result))
                except:
                    pass
                self.session.openWithCallback(self.exit, MessageBox, "Error while creating screenshot", MessageBox.TYPE_ERROR, timeout=3)
        except Exception as e:
            print('error:', e)
            pass

    def updateCountdown(self, callback=None):
        try:
            self.countdown -= 1
            self.updateCountdownLabel()
            if self.countdown == 0:
                self.countdown = config.plugins.Mosaic.countdown.value
                self.working = True
                self.makeNextScreenshot()
            else:
                self.updateTimer.start(1000, True)
        except:
            pass

    def updateCountdownLabel(self):
        try:
            self["countdown"].setText("%s %s / %s" % ("Countdown:", str(self.countdown), str(config.plugins.Mosaic.countdown.value)))
        except:
            pass

    def getEventName(self, info, ref):
        try:
            event = info.getEvent(ref)
            if event is not None:
                eventName = event.getEventName()
                if eventName is None:
                    eventName = ""
            else:
                eventName = ""
            return eventName
        except:
            pass


Session = None
Servicelist = None
BouquetSelectorScreen = None
# log


def trace_error():
    try:
        import sys
        import traceback
        # Stampa la traccia dell'errore su stdout
        traceback.print_exc(file=sys.stdout)
        # Scrive la traccia dell'errore su un file di log
        with open("/tmp/mosaic.log", "a") as log_file:
            traceback.print_exc(file=log_file)
    except Exception as e:
        # Gestisce qualsiasi eccezione che potrebbe verificarsi durante la registrazione dell'errore
        print("Failed to log the error:", e, file=sys.stderr)


def getBouquetServices(bouquet):
    try:
        services = []
        Servicelist = eServiceCenter.getInstance().list(bouquet)
        if Servicelist is not None:
            while True:
                service = Servicelist.getNext()
                if not service.valid():
                    break
                if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
                    continue
                services.append(service)
        return services
    except:
        pass


def closeBouquetSelectorScreen(ret=None):
    if BouquetSelectorScreen is not None:
        BouquetSelectorScreen.close()


def openMosaic(bouquet):
    if bouquet is not None:
        services = getBouquetServices(bouquet)
        if len(services):
            Session.openWithCallback(closeBouquetSelectorScreen, Mosaic, services)


def main(session, servicelist, **kwargs):
    global Session
    Session = session
    global Servicelist
    Servicelist = servicelist
    global BouquetSelectorScreen

    bouquets = Servicelist.getBouquetList()
    if bouquets is not None:
        if len(bouquets) == 1:
            openMosaic(bouquets[0][1])
        elif len(bouquets) > 1:
            BouquetSelectorScreen = Session.open(BouquetSelector, bouquets, openMosaic, enableWrapAround=True)


def Plugins(**kwargs):
    return PluginDescriptor(name="Mosaic 9/4 Screens", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
