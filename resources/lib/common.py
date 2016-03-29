#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pyDes
import uuid
import cookielib
import mechanize
import sys
import urllib
import urllib2
import urlparse
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import base64
import shutil
import binascii
import hmac
import time
import hashlib
import json

addon = xbmcaddon.Addon()
__plugin__ = addon.getAddonInfo('name')
__authors__ = addon.getAddonInfo('author')
__credits__ = ""
__version__ = addon.getAddonInfo('version')
__addonid__ = addon.getAddonInfo('id')
profilpath = xbmc.translatePath('special://profile/').decode('utf-8')
pluginpath = addon.getAddonInfo('path').decode('utf-8')
pldatapath = xbmc.translatePath('special://profile/addon_data/' + __addonid__).decode('utf-8')
homepath = xbmc.translatePath('special://home').decode('utf-8')
dbplugin = 'script.module.amazon.database'
dbpath = os.path.join(homepath, 'addons', dbplugin, 'lib')
pluginhandle = int(sys.argv[1])
tmdb = base64.b64decode('YjM0NDkwYzA1NmYwZGQ5ZTNlYzlhZjIxNjdhNzMxZjQ=')
tvdb = base64.b64decode('MUQ2MkYyRjkwMDMwQzQ0NA==')
COOKIEFILE = os.path.join(pldatapath, 'cookies.lwp')
def_fanart = os.path.join(pluginpath, 'fanart.jpg')
na = 'not available'

selectLanguage = addon.getSetting("selectLanguage")
siteVersion = int(addon.getSetting("siteVersion"))
siteVersionsList = ["com", "co.uk", "de", "jp"]
apiMain = ["atv-ps", "atv-ps-eu", "atv-ps-eu"][siteVersion]
marketplaceId = ["ATVPDKIKX0DER", "A1F83G8C2ARO7P", "A1PA6795UKMFR9", "A1VC38T7YXB528"][siteVersion]
siteVersion = siteVersionsList[siteVersion]


# not workin yet
# BASE_URL = "https://www.amazon." + siteVersion
# ATV_URL = 'https://atv-ps-eu.amazon.com'


BASE_URL = 'https://www.amazon.de'
ATV_URL = 'https://atv-eu.amazon.com'

# ATV_URL = 'https://atv-ext-eu.amazon.com'
DEVICETYPE_ID = "A1MPSLFC7L5AFK"
FIRMWARE = "fmw:15-app:1.1.23"
UserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2566.0 Safari/537.36'
movielib = '/gp/video/%s/movie/'
tvlib = '/gp/video/%s/tv/'
lib = 'video-library'
wl = 'watchlist'
verbLog = addon.getSetting('logging') == 'true'
Dialog = xbmcgui.Dialog()


class _Info:

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)


def log(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8", 'ignore')
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8", 'ignore'),
             level=xbmc.LOGDEBUG)


def prettyprint(string):
    log(json.dumps(string,
                   sort_keys=True,
                   indent=4,
                   separators=(',', ': ')))


def getURL(url, host=BASE_URL.split('//')[1], useCookie=False, silent=False, headers=None):
    cj = cookielib.LWPCookieJar()
    if useCookie:
        if isinstance(useCookie, bool):
            cj = mechanizeLogin()
        else:
            cj = useCookie
        if isinstance(cj, bool):
            return False
    dispurl = re.sub('(?i)%s|%s|&token=\w+' % (tvdb, tmdb), '', url).strip()
    if not silent:
        Log('getURL: ' + dispurl)
    if not headers:
        headers = [('User-Agent', UserAgent), ('Host', host)]
    try:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), urllib2.HTTPRedirectHandler)
        opener.addheaders = headers
        usock = opener.open(url)
        response = usock.read()
        usock.close()
    except urllib2.URLError, e:
        Log('Error reason: %s' % e, xbmc.LOGERROR)
        return False
    return response


def getATVURL(url):
    try:
        opener = urllib2.build_opener()
        Log('ATVURL --> url = ' + url)
        hmac_key = binascii.unhexlify('f5b0a28b415e443810130a4bcb86e50d800508cc')
        sig = hmac.new(hmac_key, url, hashlib.sha1)
        androidsig = base64.encodestring(sig.digest()).replace('\n', '')
        opener.addheaders = [('x-android-sign', androidsig)]
        usock = opener.open(url)
        response = usock.read()
        usock.close()
    except urllib2.URLError, e:
        Log('Error reason: %s' % e, xbmc.LOGERROR)
        return False
    else:
        return response


def WriteLog(data, fn='', mode='a'):
    if not verbLog:
        return
    if fn:
        fn = '-' + fn
    fn = __plugin__ + fn + '.log'
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    data = time.strftime('[%d.%m/%H:%M:%S] ', time.localtime()) + data.__str__()
    path = os.path.join(homepath, fn)
    with open(path, mode) as file:
        file.write(data)
        file.write('\n')


def Log(msg, level=xbmc.LOGNOTICE):
    if level == xbmc.LOGDEBUG and verbLog:
        level = xbmc.LOGNOTICE
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    WriteLog(msg)
    xbmc.log('[%s] %s' % (__plugin__, msg.__str__()), level)


def addDir(name, mode, sitemode, url='', thumb='', fanart='', infoLabels=False, totalItems=0, cm=False, page=1, options=''):
    u = '%s?url=<%s>&mode=<%s>&sitemode=<%s>&name=<%s>&page=<%s>&opt=<%s>' % (sys.argv[0], urllib.quote_plus(url), mode, sitemode, urllib.quote_plus(name), urllib.quote_plus(str(page)), options)
    if not fanart or fanart == na:
        fanart = def_fanart
    else:
        u += '&fanart=<%s>' % urllib.quote_plus(fanart)
    if not thumb:
        thumb = def_fanart
    else:
        u += '&thumb=<%s>' % urllib.quote_plus(thumb)
    item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumb)
    item.setArt({'fanart': fanart,
                 'poster': thumb})
    item.setProperty('IsPlayable', 'false')
    try:
        item.setProperty('TotalSeasons', str(infoLabels['TotalSeasons']))
    except Exception:
        pass
    if infoLabels:
        item.setInfo(type='Video', infoLabels=infoLabels)
    if cm:
        item.addContextMenuItems(cm, replaceItems=False)
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=item, isFolder=True, totalItems=totalItems)


def addVideo(name, asin, poster=False, fanart=False, infoLabels=False, totalItems=0, cm=None, trailer=False, isAdult=False, isHD=False):
    if not infoLabels:
        infoLabels = {"Title": name}
    u = '%s?asin=<%s>&mode=<play>&name=<%s>&sitemode=<PLAYVIDEO>&adult=<%s>' % (sys.argv[0], asin, urllib.quote_plus(name), str(isAdult))
    liz = xbmcgui.ListItem(name, thumbnailImage=poster if poster else "")
    if not fanart or fanart == na:
        fanart = def_fanart
    liz.setProperty('fanart_image', fanart)
    liz.setProperty('IsPlayable', 'true')
    if isHD:
        liz.addStreamInfo('video', {'width': 1920, 'height': 1080})
    else:
        liz.addStreamInfo('video', {'width': 720, 'height': 480})
    if infoLabels['AudioChannels']:
        liz.addStreamInfo('audio', {'codec': 'ac3', 'channels': int(infoLabels['AudioChannels'])})
    if trailer:
        infoLabels['Trailer'] = u + '&trailer=<1>&selbitrate=<0>'
    u += '&trailer=<0>&selbitrate=<0>'
    if 'Poster' in infoLabels:
        liz.setArt({'tvshow.poster': infoLabels['Poster']})
    else:
        liz.setArt({'poster': poster})
    liz.setInfo(type='Video', infoLabels=infoLabels)
    if cm:
        liz.addContextMenuItems(cm, replaceItems=False)
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=False, totalItems=totalItems)


def addText(name):
    item = xbmcgui.ListItem(name)
    item.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=sys.argv[0], listitem=item)


def toggleWatchlist(asin=False, action='add'):
    cookie = mechanizeLogin()
    token = getToken(asin, cookie)
    params = {"ASIN": asin,
              "dataType": "json",
              "token": token,
              "action": action}
    url = BASE_URL + '/gp/video/watchlist/ajax/addRemove.html?' + urllib.urlencode(params)
    data = json.loads(getURL(url, useCookie=cookie))
    if data['success'] == 1:
        Log(asin + ' ' + data['status'])
        if data['AsinStatus'] == 0:
            xbmc.executebuiltin('Container.Refresh')
    else:
        Log(data['status'] + ': ' + data['reason'])


def getToken(asin, cookie):
    url = BASE_URL + '/gp/aw/video/detail/' + asin
    data = getURL(url, useCookie=cookie)
    token = re.compile('token[^"]*"([^"]*)"').findall(data)[0]
    return urllib.quote_plus(token)


def gen_id():
    guid = addon.getSetting("GenDeviceID")
    if not guid or len(guid) != 56:
        guid = hmac.new(UserAgent, uuid.uuid4().bytes, hashlib.sha224).hexdigest()
        addon.setSetting("GenDeviceID", guid)
    return guid


def mechanizeLogin():
    cj = cookielib.LWPCookieJar()
    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE, ignore_discard=True, ignore_expires=True)
        return cj
    Log('Login')
    for i in xrange(0, 3):
        succeeded = dologin()
        if succeeded:
            return True
        Log('Login Retry: %s' % i)
        xbmc.sleep(1000)
    Dialog.ok('Login Error', 'Failed to Login')
    return False


def dologin():
    email = addon.getSetting('login_name')
    password = decode(addon.getSetting('login_pass'))
    changed = False

    if addon.getSetting('save_login') == 'false' or email == '' or password == '':
        keyboard = xbmc.Keyboard(addon.getSetting('login_name'), getString(30002))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            email = keyboard.getText()
            password = setLoginPW()
            if password:
                changed = True
    if password:
        if os.path.isfile(COOKIEFILE):
            os.remove(COOKIEFILE)
        cj = cookielib.LWPCookieJar()
        br = mechanize.Browser()
        br.set_handle_robots(False)
        br.set_cookiejar(cj)
        # br.set_debug_http(True)
        # br.set_debug_responses(True)
        br.addheaders = [('User-agent', UserAgent)]
        br.open(BASE_URL + "/gp/aw/si.html")
        br.select_form(name="signIn")
        br["email"] = email
        br["password"] = password
        logged_in = br.submit()
        error_str = "message error"
        if error_str in logged_in.read():
            Dialog.ok(getString(30200), getString(30201))
            return False
        else:
            if addon.getSetting('save_login') == 'true' and changed:
                addon.setSetting('login_name', email)
                addon.setSetting('login_pass', encode(password))
            if addon.getSetting('no_cookie') != 'true':
                cj.save(COOKIEFILE, ignore_discard=True, ignore_expires=True)
            gen_id()
            return cj
    return True


def setLoginPW():
    keyboard = xbmc.Keyboard('', getString(30003), True)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        password = keyboard.getText()
        return password
    return False


def encode(data):
    k = pyDes.triple_des((str(uuid.getnode()) * 2)[0:24],
                         pyDes.CBC,
                         "\0\0\0\0\0\0\0\0",
                         padmode=pyDes.PAD_PKCS5)
    return base64.b64encode(k.encrypt(data))


def decode(data):
    if not data:
        return ''
    k = pyDes.triple_des((str(uuid.getnode()) * 2)[0:24],
                         pyDes.CBC,
                         "\0\0\0\0\0\0\0\0",
                         padmode=pyDes.PAD_PKCS5)
    return k.decrypt(base64.b64decode(data))


def cleanData(data):
    if isinstance(data, (str, unicode)):
        if data.replace('-', '').strip() == '':
            data = ''
        data = data.replace(u'\u00A0', ' ').replace(u'\u2013', '-')
        data = data.strip()
        if data == '':
            data = None
    return data


def GET_ASINS(content):
    asins = ''
    hd_key = False
    prime_key = False
    channels = 1
    if "titleId" in content:
        asins += content['titleId']
        titleId = content['titleId']
    for format_ in content['formats']:
        hasprime = False
        for offer in format_['offers']:
            if offer['offerType'] == 'SUBSCRIPTION':
                hasprime = True
                prime_key = True
            elif "asin" in offer:
                newasin = offer['asin']
                if format_['videoFormatType'] == 'HD':
                    if (newasin == titleId) and hasprime:
                        hd_key = True
                if newasin not in asins:
                    asins += ',' + newasin
        if 'STEREO' in format_['audioFormatTypes']:
            channels = 2
        if 'AC_3_5_1' in format_['audioFormatTypes']:
            channels = 6
    return asins, hd_key, prime_key, channels


def SCRAP_ASINS(url):
    asins = []
    url = BASE_URL + url + '?ie=UTF8&sortBy=DATE_ADDED_DESC'
    content = getURL(url, useCookie=True)
    if content:
        asins += re.compile('data-asin="(.+?)"', re.DOTALL).findall(content)
        return asins
    return []


def getString(string_id, enc=False):
    if enc:
        return addon.getLocalizedString(string_id).encode('utf-8')
    return addon.getLocalizedString(string_id)


def remLoginData():
    if os.path.isfile(COOKIEFILE):
        os.remove(COOKIEFILE)
    addon.setSetting('login_name', '')
    addon.setSetting('login_pass', '')


def checkCase(title):
    if title.isupper():
        title = title.title().replace('[Ov]', '[OV]').replace('Bc', 'BC')
    return title.replace('[dt./OV]', '')


def getCategories():
    params = {"firmware": FIRMWARE,
              "deviceTypeID": DEVICETYPE_ID,
              "deviceID": addon.getSetting("GenDeviceID"),
              "format": "json",
              "OfferGroups": "B0043YVHMY",
              "IncludeAll": "T",
              "version": 2}
    response = getURL(ATV_URL + '/cdp/catalog/GetCategoryList?' + urllib.urlencode(params))
    data = json.loads(response)
    asins = {}
    for maincat in data['message']['body']['categories']:
        mainCatId = maincat.get('id')
        if mainCatId not in ['movies', 'tv_shows']:
            continue
        asins.update({mainCatId: {}})
        for cat in maincat['categories'][0]['categories']:
            subPageType = cat.get('subPageType')
            subCatId = cat.get('id')
            if subPageType in ['PrimeMovieRecentlyAdded', 'PrimeTVRecentlyAdded']:
                asins[mainCatId].update({subPageType: urlparse.parse_qs(cat['query'])['ASINList'][0].split(',')})
            elif 'prime_editors_picks' in subCatId:
                for picks in cat['categories']:
                    query = picks.get('query').upper()
                    title = picks.get('title')
                    if title and ('ASINLIST' in query):
                        querylist = urlparse.parse_qs(query)
                        alkey = None
                        for key in querylist.keys():
                            if 'ASINLIST' in key:
                                alkey = key
                        asins[mainCatId].update({title: urlparse.parse_qs(query)[alkey][0]})
    return asins


def SetView(content):
    xbmcplugin.setContent(pluginhandle, content)
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=False)


def compasin(list_, searchstring):
    ret = False
    for array in list_:
        if searchstring.lower() in array[0].lower():
            array[1] = 1
            ret = True
    return ret, list_


def waitforDB(database):
    if database == 'tv':
        import tv
        c = tv.tvDB.cursor()
        tbl = 'shows'
    else:
        import movies
        c = movies.MovieDB.cursor()
        tbl = 'movies'
    error = True
    while error:
        error = False
        try:
            c.execute('select distinct * from ' + tbl).fetchone()
        except Exception:
            error = True
            xbmc.sleep(1000)
            Log('Database locked')
    c.close()


def getTypes(items, col):
    types = []
    lowlist = []
    for data in items:
        data = data[0]
        if isinstance(data, str):
            if 'Rated' in data:
                item = data.split('for')[0]
                if item and item not in types and item != 'Inc.' and item != 'LLC.':
                    types.append(item)
            else:
                if 'genres' in col:
                    data = data.split('/')
                else:
                    data = re.split(r'[,;/]', data)
                for item in data:
                    item = item.strip()
                    if item and item.lower() not in lowlist and item != 'Inc.' and item != 'LLC.':
                        types.append(item)
                        lowlist.append(item.lower())
        elif data != 0:
            if data is not None:
                strdata = str(data)[0:-1] + '0 -'
                if strdata not in types:
                    types.append(strdata)
    return types


def updateRunning():
    from datetime import datetime, timedelta
    update = addon.getSetting('update_running')
    if update != 'false':
        starttime = datetime(*(time.strptime(update, '%Y-%m-%d %H:%M')[0:6]))
        if (starttime + timedelta(hours=6)) <= datetime.today():
            addon.setSetting('update_running', 'false')
            Log('DB Cancel update - duration > 6 hours')
        else:
            Log('DB Update already running', xbmc.LOGDEBUG)
            return True
    return False


def copyDB(ask=False):
    if ask:
        if not Dialog.yesno(getString(30193), getString(30194)):
            shutil.copystat(org_tvDBfile, tvDBfile)
            shutil.copystat(org_MovieDBfile, MovieDBfile)
            return
    import tv
    import movies
    tv.tvDB.close()
    movies.MovieDB.close()
    shutil.copy2(org_tvDBfile, tvDBfile)
    shutil.copy2(org_MovieDBfile, MovieDBfile)

org_tvDBfile = os.path.join(dbpath, 'tv.db')
org_MovieDBfile = os.path.join(dbpath, 'movies.db')
if addon.getSetting('customdbfolder') == 'true':
    dbpath = xbmc.translatePath(addon.getSetting('dbfolder')).decode('utf-8')
tvDBfile = os.path.join(dbpath, 'tv.db')
MovieDBfile = os.path.join(dbpath, 'movies.db')

if addon.getSetting('customdbfolder') == 'true':
    if os.path.isfile(org_tvDBfile) and os.path.isfile(org_MovieDBfile):
        if not os.path.isdir(dbpath):
            os.makedirs(dbpath)
        if not os.path.isfile(tvDBfile) or not os.path.isfile(MovieDBfile):
            copyDB()
        org_fileacc = int(os.path.getmtime(org_tvDBfile) + os.path.getmtime(org_MovieDBfile))
        cur_fileacc = int(os.path.getmtime(tvDBfile) + os.path.getmtime(MovieDBfile))
        if org_fileacc > cur_fileacc:
            copyDB(True)

urlargs = urllib.unquote_plus(sys.argv[2][1:].replace('&', ', ')).replace('<', '"').replace('>', '"')
Log('Args: %s' % urlargs)
exec "args = _Info(%s)" % urlargs
