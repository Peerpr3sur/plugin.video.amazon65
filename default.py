#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import resources.lib.common as common
import os
import xbmcaddon
import sys
addon = xbmcaddon.Addon()


def modes():
    if sys.argv[2] == '':
        common.Log('Version: %s' % common.__version__)
        common.Log('Unicode support: %s' % common.os.path.supports_unicode_filenames)
        cm_watchlist = []
        cm_library = [(common.getString(30116), 'XBMC.RunPlugin(%s?mode=<appfeed>&sitemode=<RefreshList>&url=<%s>)' % (sys.argv[0], common.lib))]
        common.addDir('Watchlist',
                      'appfeed',
                      'ListMenu',
                      common.wl,
                      cm=cm_watchlist)
        updatemovie = []
        updatemovie.append((common.getString(30103),
                            'XBMC.RunPlugin(%s?mode=<appfeed>&sitemode=<updateAll>)' % sys.argv[0]))
        updatemovie.append((common.getString(30102),
                            'XBMC.RunPlugin(%s?mode=<movies>&sitemode=<addMoviesdb>&url=<f>)' % sys.argv[0]))
        common.addDir(common.getString(30104),
                      'listmovie',
                      'LIST_MOVIE_ROOT',
                      cm=updatemovie)

        updatetv = []
        updatetv.append((common.getString(30103),
                         'XBMC.RunPlugin(%s?mode=<appfeed>&sitemode=<updateAll>)' % sys.argv[0]))
        updatetv.append((common.getString(30105),
                         'XBMC.RunPlugin(%s?mode=<tv>&sitemode=<addTVdb>&url=<f>)' % sys.argv[0]))
        common.addDir(common.getString(30107),
                      'listtv',
                      'LIST_TV_ROOT', cm=updatetv)

        common.addDir(common.getString(30108),
                      'appfeed',
                      'SEARCH_DB')
        common.addDir(common.getString(30060),
                      'appfeed',
                      'ListMenu',
                      common.lib,
                      cm=cm_library)

        common.xbmcplugin.endOfDirectory(common.pluginhandle)
    else:
        exec 'import resources.lib.%s as sitemodule' % common.args.mode
        exec 'sitemodule.%s()' % common.args.sitemode

if addon.getSetting('save_login') == 'false':
    addon.setSetting('login_name', '')
    addon.setSetting('login_pass', '')
    addon.setSetting('no_cookie', '')
if os.path.isfile(common.COOKIEFILE) and addon.getSetting('no_cookie') == 'true':
    os.remove(common.COOKIEFILE)

modes()
