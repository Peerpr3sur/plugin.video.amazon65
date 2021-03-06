#!/usr/bin/env python
# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
import common
import listtv
import listmovie
import xbmcgui
import json
import xbmc
import urllib

pluginhandle = common.pluginhandle

# Modes
# ===============================================================================
# 'catalog/GetCategoryList'
# 'catalog/Browse'
# 'catalog/Search'
# 'catalog/GetSearchSuggestions'
# 'catalog/GetASINDetails'
# 'catalog/GetSimilarities'
#
# 'catalog/GetStreamingUrls'
# 'catalog/GetStreamingTrailerUrls'
# 'catalog/GetContentUrls'
#
# 'library/GetLibrary'
# 'library/Purchase'
# 'library/GetRecentPurchases'
#
# 'link/LinkDevice'
# 'link/UnlinkDevice'
# 'link/RegisterClient'
# 'licensing/Release'
#
# 'usage/UpdateStream'
# 'usage/ReportLogEvent'
# 'usage/ReportEvent'
# 'usage/GetServerConfig'
# ===============================================================================

PARAMETERS = {"firmware": common.FIRMWARE,
              "deviceTypeID": common.DEVICETYPE_ID,
              "deviceID": common.gen_id(),
              "format": "json"}
PARAMETERS = '?' + urllib.urlencode(PARAMETERS)


def BUILD_BASE_API(MODE, HOST=common.ATV_URL + '/cdp/'):
    return HOST + MODE + PARAMETERS


def getList(ContentType=False, start=0, isPrime=True, NumberOfResults=False, OrderBy='MostPopular', version=2, AsinList=False, catalog='Browse', asin=False):
    BROWSE_PARAMS = '&StartIndex=' + str(start)
    if NumberOfResults:
        BROWSE_PARAMS += '&NumberOfResults=' + str(NumberOfResults)
    if ContentType:
        BROWSE_PARAMS += '&ContentType=' + ContentType
        BROWSE_PARAMS += '&OrderBy=' + OrderBy
    BROWSE_PARAMS += '&IncludeAll=T'
    if isPrime:
        BROWSE_PARAMS += '&OfferGroups=B0043YVHMY'
    if ContentType == 'TVEpisode':
        BROWSE_PARAMS += '&Detailed=T'
        BROWSE_PARAMS += '&AID=T'
        BROWSE_PARAMS += '&tag=1'
        BROWSE_PARAMS += '&IncludeBlackList=T'
    if AsinList:
        BROWSE_PARAMS += '&SeasonASIN=' + AsinList
    if asin:
        BROWSE_PARAMS += '&asin=' + asin
    BROWSE_PARAMS += '&version=' + str(version)
    url = BUILD_BASE_API('catalog/%s' % catalog) + BROWSE_PARAMS
    return json.loads(common.getATVURL(url))


def ASIN_LOOKUP(ASINLIST):
    params = {"asinList": ASINLIST,
              "NumberOfResults": len(ASINLIST.split(',')) - 1,
              "IncludeAll": "T",
              "playbackInformationRequired": "true",
              "version": 2}
    url = BUILD_BASE_API('catalog/GetASINDetails') + "&" + urllib.urlencode(params)
    return json.loads(common.getATVURL(url))


def URL_LOOKUP(url):
    return json.loads(common.getATVURL(url + PARAMETERS.replace('?', '&')))


def SEARCH_DB(searchString=False):
    if not searchString:
        keyboard = xbmc.Keyboard('')
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            searchString = keyboard.getText()
            if searchString != '':
                common.addText('          ----=== ' + common.getString(30104) + ' ===----')
                if not listmovie.LIST_MOVIES('movietitle', searchString, search=True):
                    common.addText(common.getString(30202))
                common.addText('          ----=== ' + common.getString(30107) + ' ===----')
                if not listtv.LIST_TVSHOWS('seriestitle', searchString, search=True):
                    common.addText(common.getString(30202))
                common.SetView('tvshows')


def getSimilarities():
    import tv
    data = getList(NumberOfResults=250, catalog='GetSimilarities', asin=common.args.asin)
    for title in data['message']['body']['titles']:
        asin = title['titleId']
        if not listmovie.LIST_MOVIES('asin', asin, search=True):
            for seasondata in tv.lookupTVdb(asin, tbl='seasons', single=False):
                if seasondata:
                    listtv.ADD_SEASON_ITEM(seasondata, disptitle=True)
    common.SetView('tvshows')


def ListMenu():
    list_ = common.args.url
    common.addDir(common.getString(30104), 'appfeed', 'ListCont', common.movielib % list_)
    common.addDir(common.getString(30107), 'appfeed', 'ListCont', common.tvlib % list_)
    common.xbmcplugin.endOfDirectory(common.pluginhandle)


def ListCont():
    import tv
    mov = False
    showonly = False
    rvalue = 'distinct *'
    url = common.args.url
    if 'movie' in url:
        mov = True
    if common.addon.getSetting('disptvshow') == 'true':
        showonly = True
        rvalue = 'seriesasin'
    asins = common.SCRAP_ASINS(url)
    if not asins:
        common.SetView('movies')
        return

    asinlist = []
    for value in asins:
        ret = 0
        if mov:
            ret = listmovie.LIST_MOVIES('asin', value, search=True, cmmode=1)
        if ret == 0 and not mov:
            for seasondata in tv.lookupTVdb(value, tbl='seasons', rvalue=rvalue, single=False):
                if not seasondata:
                    continue
                if showonly:
                    ret = 0
                    value = seasondata[0]
                    for asin in tv.lookupTVdb(value, tbl='shows', rvalue='asin').split(','):
                        if asin in asinlist:
                            ret = 1
                else:
                    ret = 1
                    listtv.ADD_SEASON_ITEM(seasondata, disptitle=True, cmmode=1)
        if ret == 0 and not mov:
            listtv.LIST_TVSHOWS('asin', value, search=True, cmmode=1)
        asinlist.append(value)
    if mov:
        common.SetView('movies')
    else:
        common.SetView('tvshows')


def RefreshList():
    import tv
    import movies
    list_ = common.args.url
    mvlist = []
    tvlist = []
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(common.__plugin__, common.getString(30117))

    for asin in common.SCRAP_ASINS(common.movielib % list_):
        if not movies.lookupMoviedb(asin):
            mvlist.append(asin)

    for asin in common.SCRAP_ASINS(common.tvlib % list_):
        if not tv.lookupTVdb(asin, tbl='seasons'):
            tvlist.append(asin)

    if mvlist:
        movies.updateLibrary(mvlist)
    if tvlist:
        tv.addTVdb(False, tvlist)
    pDialog.close()

    if mvlist:
        movies.updateFanart()
    if tvlist:
        tv.updateFanart()


def getTVDBImages(title, imdb=None, tvdb_id=None, seasons=False):
    posterurl = fanarturl = None
    splitter = [' - ', ': ', ', ']
    langcodes = ['de', 'en']
    TVDB_URL = 'http://www.thetvdb.com/banners/'
    while not tvdb_id:
        tv = urllib.quote_plus(title)
        result = common.getURL('http://www.thetvdb.com/api/GetSeries.php?seriesname=%s&language=de' % (tv), silent=True)
        soup = BeautifulSoup(result)
        tvdb_id = soup.find('seriesid')
        if tvdb_id:
            tvdb_id = tvdb_id.string
        else:
            oldtitle = title
            for splitchar in splitter:
                if title.count(splitchar):
                    title = title.split(splitchar)[0]
                    break
            if title == oldtitle:
                break
    if not tvdb_id:
        return None, None, None
    if seasons:
        soup = BeautifulSoup(common.getURL('http://www.thetvdb.com/api/%s/series/%s/banners.xml' % (common.tvdb, tvdb_id), silent=True))
        seasons = {}
        for lang in langcodes:
            for datalang in soup.findAll('language'):
                if datalang.string == lang:
                    data = datalang.parent
                    if data.bannertype.string == 'fanart' and not fanarturl:
                        fanarturl = TVDB_URL + data.bannerpath.string
                    if data.bannertype.string == 'poster' and not posterurl:
                        posterurl = TVDB_URL + data.bannerpath.string
                    if data.bannertype.string == data.bannertype2.string == 'season':
                        snr = data.season.string
                        if snr not in seasons:
                            seasons[snr] = TVDB_URL + data.bannerpath.string
        return seasons, posterurl, fanarturl
    else:
        for lang in langcodes:
            result = common.getURL('http://www.thetvdb.com/api/%s/series/%s/%s.xml' % (common.tvdb, tvdb_id, lang), silent=True)
            soup = BeautifulSoup(result)
            fanart = soup.find('fanart')
            poster = soup.find('poster')
            if fanart and not fanarturl:
                fanarturl = TVDB_URL + fanart.string
            if poster and not posterurl:
                posterurl = TVDB_URL + poster.string
            if posterurl and fanarturl:
                return tvdb_id, posterurl, fanarturl
        return tvdb_id, posterurl, fanarturl


def getTMDBImages(title, imdb=None, content='movie', year=None):
    fanart = movie_id = None
    splitter = [' - ', ': ', ', ']
    TMDB_URL = 'http://image.tmdb.org/t/p/original'
    yearorg = year

    while not movie_id:
        str_year = '&year=' + str(year) if year else ""
        movie = urllib.quote_plus(title)
        result = common.getURL('http://api.themoviedb.org/3/search/%s?api_key=%s&language=de&query=%s%s' % (content, common.tmdb, movie, str_year), silent=True)
        if not result:
            common.Log('Fanart: Pause 5 sec...')
            xbmc.sleep(5000)
            continue
        data = json.loads(result)
        if data['total_results'] > 0:
            result = data['results'][0]
            if result['backdrop_path']:
                fanart = TMDB_URL + result['backdrop_path']
            movie_id = result['id']
        elif year:
            year = 0
        else:
            year = yearorg
            oldtitle = title
            for splitchar in splitter:
                if title.count(splitchar):
                    title = title.split(splitchar)[0]
                    break
            if title == oldtitle:
                break
    if content == 'movie' and movie_id and not fanart:
        fanart = common.na
    return fanart


def updateAll():
    if common.updateRunning():
        return
    import movies
    import tv
    from datetime import datetime
    common.addon.setSetting('update_running', datetime.today().strftime('%Y-%m-%d %H:%M'))
    common.Log('Starting DBUpdate')
    Notif = xbmcgui.Dialog().notification
    Notif(common.__plugin__, common.getString(30106), sound=False)
    tv.addTVdb(False)
    movies.addMoviesdb(False)
    NewAsins = common.getCategories()
    movies.setNewest(NewAsins)
    movies.updateFanart()
    tv.setNewest(NewAsins)
    tv.updateFanart()
    common.addon.setSetting('last_update', datetime.today().strftime('%Y-%m-%d'))
    common.addon.setSetting('update_running', 'false')
    Notif(common.__plugin__, common.getString(30126), sound=False)
    common.Log('DBUpdate finished')
