#!/usr/bin/env python
# -*- coding: utf-8 -*-
import common
import random
import xbmc
import xbmcplugin
import xbmcgui
import re
import json
import codecs
from BeautifulSoup import BeautifulSoup
import urllib

addon = common.addon
Dialog = xbmcgui.Dialog()
pluginhandle = common.pluginhandle

verbLog = addon.getSetting('logging') == 'true'


def IStreamPlayback(url, asin, trailer):
    values = getFlashVars(url)
    if not values:
        return
    vMT = 'Trailer' if trailer == '1' else 'Feature'
    data = getUrldata(mode='catalog/GetPlaybackResources',
                      values=values,
                      extra=True,
                      vMT=vMT,
                      opt='&titleDecorationScheme=primary-content')
    title, plot, mpd, subs = getStreams(*data, retmpd=True)
    licURL = getUrldata(mode='catalog/GetPlaybackResources',
                        values=values,
                        extra=True,
                        vMT=vMT,
                        dRes='Widevine2License',
                        retURL=True)
    common.Log(mpd)
    listitem = xbmcgui.ListItem(path=mpd)

    if trailer == '1':
        if title:
            listitem.setInfo('video', {'Title': title + ' (Trailer)'})
        if plot:
            listitem.setInfo('video', {'Plot': plot})
    listitem.setSubtitles(subs)
    listitem.setProperty('inputstream.mpd.license_type', 'com.widevine.alpha')
    listitem.setProperty('inputstream.mpd.license_key', licURL)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=listitem)


def parseSubs(data):
    subs = []
    if addon.getSetting('subtitles') == 'false':
        return subs
    for sub in data:
        lang = sub['displayName'].split('(')[0].strip()
        common.Log('Convert %s Subtitle' % lang)
        file = xbmc.translatePath('special://temp/%s.srt' % lang).decode('utf-8')
        srt = codecs.open(file, 'w', encoding='utf-8')
        soup = BeautifulSoup(common.getURL(sub['url']))
        enc = soup.originalEncoding
        num = 0
        for caption in soup.findAll('tt:p'):
            num += 1
            subtext = caption.renderContents().decode(enc).replace('<tt:br>', '\n').replace('</tt:br>', '')
            srt.write(u'%s\n%s --> %s\n%s\n\n' % (num, caption['begin'], caption['end'], subtext))
        srt.close()
        subs.append(file)
    return subs


def PLAYVIDEO():
    amazonUrl = common.BASE_URL + "/dp/" + common.args.asin
    trailer = common.args.trailer
    xbmc.Player().stop()
    IStreamPlayback(amazonUrl, common.args.asin, trailer)


def getStreams(suc, data, retmpd=False):
    if not suc:
        return ''
    subUrls = parseSubs(data['subtitleUrls'])
    title = plot = False
    common.prettyprint(data)
    if "catalogMetadata" in data:
        title = data['catalogMetadata']['catalog']['title']
        plot = data['catalogMetadata']['catalog']['synopsis']

    for cdn in data['audioVideoUrls']['avCdnUrlSets']:
        for urlset in cdn['avUrlInfoList']:
            if retmpd:
                return title, plot, urlset['url'], subUrls
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
    data = getUrldata(mode='catalog/GetPlaybackResources',
                      values=values,
                      extra=True)
    fr = getStreams(*data)
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


def getUrldata(mode, values, devicetypeid=False, opt='', extra=False, useCookie=False, retURL=False, vMT='Feature', dRes='AudioVideoUrls%2CCatalogMetadata%2CSubtitleUrls'):
    if not devicetypeid:
        devicetypeid = values['deviceTypeID']
    url = common.ATV_URL + '/cdp/' + mode + "?"
    params = {"asin": values['asin'],
              "consumptionType": "Streaming",
              "deviceID": values['deviceID'],
              "deviceTypeID": devicetypeid,
              "firmware": 1,
              "version": 1,
              "format": "json",
              "marketplaceID": values['marketplace'],
              # "operatingSystemName": "Windows",
              # "operatingSystemVersion": "10.0",
              "customerID": values['customer'],
              "token": values['token']}
    url += urllib.urlencode(params)
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
        if "error" in jsondata:
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
