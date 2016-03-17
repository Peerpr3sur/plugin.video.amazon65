#!/usr/bin/env python
# -*- coding: utf-8 -*-
import common
import movies as moviesDB
import tv as tvDB
import listtv
import listmovie

pluginhandle = common.pluginhandle
xbmc = common.xbmc
xbmcplugin = common.xbmcplugin
urllib = common.urllib
sys = common.sys
xbmcgui = common.xbmcgui
os = common.os
Dialog = xbmcgui.Dialog()

if (common.addon.getSetting('enablelibraryfolder') == 'true'):
    MOVIE_PATH = os.path.join(xbmc.translatePath(common.addon.getSetting('customlibraryfolder')),'Movies').decode('utf-8')
    TV_SHOWS_PATH = os.path.join(xbmc.translatePath(common.addon.getSetting('customlibraryfolder')),'TV').decode('utf-8')
else:
    MOVIE_PATH = os.path.join(common.pldatapath,'Movies')
    TV_SHOWS_PATH = os.path.join(common.pldatapath,'TV')

def UpdateLibrary():
    xbmc.executebuiltin('UpdateLibrary(video)')

def SaveFile(filename, data, dir=False):
    if dir:
        filename = common.cleanName(filename)
        filename = os.path.join(dir, filename)
    filename = common.cleanName(filename, file=False)
    file = open(filename, 'w')
    file.write(data)
    file.close()


def streamDetails(Info, language='ger', hasSubtitles=False):
    skip_keys = ('ishd', 'isadult', 'audiochannels', 'genre', 'cast', 'duration', 'trailer', 'asins')
    fileinfo  = '<runtime>%s</runtime>' % Info['Duration']
    if Info.has_key('Genre'):
        for genre in Info['Genre'].split('/'):
            fileinfo += '<genre>%s</genre>' % genre.strip()
    if Info.has_key('Cast'):
        for actor in Info['Cast']:
            fileinfo += '<actor>'
            fileinfo += '<name>%s</name>' % actor.strip()
            fileinfo += '</actor>'
    for key, value in Info.items():
        lkey = key.lower()
        if lkey == 'premiered' and Info.has_key('TVShowTitle'):
            fileinfo += '<aired>%s</aired>' % value
        elif lkey == 'fanart':
            fileinfo += '<%s><thumb>%s</thumb></%s>' % (lkey, value, lkey)
        elif lkey not in skip_keys:
            fileinfo += '<%s>%s</%s>' % (lkey, value, lkey)
    fileinfo += '<fileinfo>'
    fileinfo += '<streamdetails>'
    fileinfo += '<audio>'
    fileinfo += '<channels>%s</channels>' % Info['AudioChannels']
    fileinfo += '<codec>aac</codec>'
    fileinfo += '</audio>'
    fileinfo += '<video>'
    fileinfo += '<codec>h264</codec>'
    fileinfo += '<durationinseconds>%s</durationinseconds>' % Info['Duration']
    if Info['isHD'] == True:
        fileinfo += '<height>720</height>'
        fileinfo += '<width>1280</width>'
    else:
        fileinfo += '<height>480</height>'
        fileinfo += '<width>720</width>'
    fileinfo += '<language>%s</language>' % language
    fileinfo += '<scantype>Progressive</scantype>'
    fileinfo += '</video>'
    if hasSubtitles == True:
        fileinfo += '<subtitle>'
        fileinfo += '<language>ger</language>'
        fileinfo += '</subtitle>'
    fileinfo += '</streamdetails>'
    fileinfo += '</fileinfo>'
    return fileinfo
