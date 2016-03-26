#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import common
import random
import xbmc
import xbmcplugin
import xbmcgui
import re
import json

addon = common.addon
Dialog = xbmcgui.Dialog()
pluginhandle = common.pluginhandle

verbLog = addon.getSetting('logging') == 'true'


def IStreamPlayback(url, asin, trailer):
    values = getFlashVars(url)
    if not values:
        return
    vMT = 'Trailer' if trailer == '1' else 'Feature'
    title, plot, mpd = getStreams(*getUrldata('catalog/GetPlaybackResources', values, extra=True, vMT=vMT, opt='&titleDecorationScheme=primary-content'), retmpd=True)
    licURL = getUrldata('catalog/GetPlaybackResources', values, extra=True, vMT=vMT, dRes='Widevine2License', retURL=True)
    common.Log(mpd)
    listitem = xbmcgui.ListItem(path=mpd)

    if trailer == '1':
        if title:
            listitem.setInfo('video', {'Title': title + ' (Trailer)'})
        if plot:
            listitem.setInfo('video', {'Plot': plot})
    listitem.setProperty('inputstream.mpd.license_type', 'com.widevine.alpha')
    listitem.setProperty('inputstream.mpd.license_key', licURL)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=listitem)


def PLAYVIDEO():
    amazonUrl = common.BASE_URL + "/dp/" + common.args.asin
    trailer = common.args.trailer
    xbmc.Player().stop()
    IStreamPlayback(amazonUrl, common.args.asin, trailer)


def check_output(*popenargs, **kwargs):
    p = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, *popenargs, **kwargs)
    out, err = p.communicate()
    retcode = p.poll()
    if retcode != 0:
        c = kwargs.get("args")
        if c is None:
            c = popenargs[0]
            e = subprocess.CalledProcessError(retcode, c)
            e.output = str(out) + str(err)
            common.Log(e, xbmc.LOGERROR)
    return out.strip()


def getStreams(suc, data, retmpd=False):
    if not suc:
        return ''

    title = plot = False
    common.prettyprint(data)
    if "catalogMetadata" in data:
        title = data['catalogMetadata']['catalog']['title']
        plot = data['catalogMetadata']['catalog']['synopsis']

    for cdn in data['audioVideoUrls']['avCdnUrlSets']:
        for urlset in cdn['avUrlInfoList']:
            if retmpd:
                return title, plot, urlset['url']
            data = common.getURL(urlset['url'])
            fps_string = re.compile('frameRate="([^"]*)').findall(data)[0]
            fr = round(eval(fps_string + '.0'), 3)
            return str(fr).replace('.0', '')
    return ''


def getPlaybackInfo(url):
    if addon.getSetting("framerate") == 'false':
        return ''
    Dialog.notification(xbmc.getLocalizedString(20186), '', xbmcgui.NOTIFICATION_INFO, 60000, False)
    values = getFlashVars(url)
    if not values:
        return ''
    fr = getStreams(*getUrldata('catalog/GetPlaybackResources', values, extra=True))
    Dialog.notification(xbmc.getLocalizedString(20186), '', xbmcgui.NOTIFICATION_INFO, 10, False)
    return fr


def getFlashVars(url):
    cookie = common.mechanizeLogin()
    showpage = common.getURL(url, useCookie=cookie)
    if not showpage:
        Dialog.notification(common.__plugin__, Error('CDP.InvalidRequest'), xbmcgui.NOTIFICATION_ERROR)
        return False
    values = {}
    search = {'sessionID': "ue_sid='(.*?)'",
              'marketplace': "ue_mid='(.*?)'",
              'customer': '"customerID":"(.*?)"'}
    if 'var config' in showpage:
        flashVars = re.compile('var config = (.*?);', re.DOTALL).findall(showpage)
        flashVars = json.loads(unicode(flashVars[0], errors='ignore'))
        values = flashVars['player']['fl_config']['initParams']
    else:
        for key, pattern in search.items():
            result = re.compile(pattern, re.DOTALL).findall(showpage)
            if result:
                values[key] = result[0]

    for key in values.keys():
        if key not in values:
            Dialog.notification(common.getString(30200), common.getString(30210), xbmcgui.NOTIFICATION_ERROR)
            return False

    values['deviceTypeID'] = 'AOAGZA014O5RE'
    values['asin'] = common.args.asin
    values['userAgent'] = common.UserAgent
    values['deviceID'] = common.gen_id()
    rand = 'onWebToken_' + str(random.randint(0, 484))
    pltoken = common.getURL(common.BASE_URL + "/gp/video/streaming/player-token.json?callback=" + rand, useCookie=cookie)
    try:
        values['token'] = re.compile('"([^"]*).*"([^"]*)"').findall(pltoken)[0][1]
    except:
        Dialog.notification(common.getString(30200), common.getString(30201), xbmcgui.NOTIFICATION_ERROR)
        return False
    return values


def getUrldata(mode, values, format='json', devicetypeid=False, version=1, firmware='1', opt='', extra=False, useCookie=False, retURL=False, vMT='Feature', dRes='AudioVideoUrls%2CCatalogMetadata'):
    if not devicetypeid:
        devicetypeid = values['deviceTypeID']
    url = common.ATV_URL + '/cdp/' + mode
    url += '?asin=' + values['asin']
    url += '&deviceTypeID=' + devicetypeid
    url += '&firmware=' + firmware
    url += '&customerID=' + values['customer']
    url += '&deviceID=' + values['deviceID']
    url += '&marketplaceID=' + values['marketplace']
    url += '&token=' + values['token']
    url += '&format=' + format
    url += '&version=' + str(version)
    url += opt
    if extra:
        url += '&resourceUsage=ImmediateConsumption&consumptionType=Streaming&deviceDrmOverride=CENC&deviceStreamingTechnologyOverride=DASH&deviceProtocolOverride=Http&audioTrackId=all'
        url += '&videoMaterialType=' + vMT
        url += '&desiredResources=' + dRes
    if retURL:
        return url
    data = common.getURL(url, common.ATV_URL.split('//')[1], useCookie=useCookie)
    if data:
        jsondata = json.loads(data)
        del data
        if "error" not in jsondata:
            return False, Error(jsondata['error'])
        return True, jsondata
    return False, 'HTTP Fehler'


def Error(data):
    code = data['errorCode']
    common.Log('%s (%s) ' % (data['message'], code), xbmc.LOGERROR)
    if 'CDP.InvalidRequest' in code:
        return common.getString(30204)
    elif 'CDP.Playback.NoAvailableStreams' in code:
        return common.getString(30205)
    elif 'CDP.Playback.NotOwned' in code:
        return common.getString(30206)
    elif 'CDP.Authorization.InvalidGeoIP' in code:
        return common.getString(30207)
    elif 'CDP.Playback.TemporarilyUnavailable' in code:
        return common.getString(30208)
    else:
        return '%s (%s) ' % (data['message'], code)
