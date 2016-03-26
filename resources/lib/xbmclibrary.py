#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui

Dialog = xbmcgui.Dialog()


def UpdateLibrary():
    xbmc.executebuiltin('UpdateLibrary(video)')

