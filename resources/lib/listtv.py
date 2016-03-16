#!/usr/bin/env python
# -*- coding: utf-8 -*-
import common
import xbmclibrary

pluginhandle = common.pluginhandle
xbmc = common.xbmc
xbmcplugin = common.xbmcplugin
urllib = common.urllib
sys = common.sys
xbmcgui = common.xbmcgui
showfanart = common.addon.getSetting("useshowfanart")
###################### Television

def LIST_TV_ROOT():
    common.addDir(common.getString(30100),'listtv','LIST_TVSHOWS_SORTED','popularity')
    common.addDir(common.getString(30110),'listtv','LIST_TVSEASON_SORTED','recent')
    common.addDir(common.getString(30149),'listtv','LIST_TVSHOWS_CATS')
    common.addDir(common.getString(30160),'listtv','LIST_TVSHOWS')
    common.addDir(common.getString(30144),'listtv','LIST_TVSHOWS_TYPES','genres' )
    common.addDir(common.getString(30158),'listtv','LIST_TVSHOWS_TYPES','actors')
    common.addDir(common.getString(30145),'listtv','LIST_TVSHOWS_TYPES','year' )
    common.addDir(common.getString(30161),'listtv','LIST_TVSHOWS_TYPES','network')
    common.addDir(common.getString(30162),'listtv','LIST_TVSHOWS_TYPES','mpaa' )
    xbmcplugin.endOfDirectory(pluginhandle)
    
def LIST_TVSHOWS_CATS():
    import tv as tvDB
    id = common.args.url
    if id:
        asins = tvDB.lookupTVdb(id, rvalue='asins', name='title', tbl='categories')
        epidb = tvDB.lookupTVdb('', name='asin', rvalue='asin, seasonasin', tbl='episodes', single=False)
        if not asins: return
        for asin in asins.split(','):
            seasonasin = None
            for epidata in epidb:
                if asin in str(epidata):
                    seasonasin = epidata[1]
                    break
            if not seasonasin: seasonasin = asin
            for seasondata in tvDB.loadTVSeasonsdb(seasonasin=seasonasin).fetchall():
                ADD_SEASON_ITEM(seasondata, disptitle=True)
        common.SetView('tvshows', 'seasonview')
        del epidb
    else:
        for title in tvDB.lookupTVdb('', name='asins', tbl='categories', single=False):
            if title: common.addDir(title[0],'listtv','LIST_TVSHOWS_CATS',title[0])
        xbmcplugin.endOfDirectory(pluginhandle,updateListing=False)   
        
def LIST_TVSHOWS_TYPES(type=False):
    import tv as tvDB
    if not type:
        type = common.args.url
    if type:
        mode = 'LIST_TVSHOWS_FILTERED'
        items = tvDB.getShowTypes(type)
    for item in items:
        common.addDir(item,'listtv',mode,type)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)          
    xbmcplugin.endOfDirectory(pluginhandle,updateListing=False)   

def LIST_TVSHOWS_FILTERED():
    LIST_TVSHOWS(common.args.url, common.args.name)

def LIST_TVSHOWS_SORTED():
    LIST_TVSHOWS(sortaz = False, sortcol = common.args.url)
    
def LIST_TVSHOWS(filter='',value=False,sortcol=False,sortaz=True,search=False,cmmode=0,export=False):
    import tv as tvDB
    if 'year' in filter: value = value.replace('0 -','')
    shows = tvDB.loadTVShowdb(filter=filter,value=value,sortcol=sortcol)
    count = 0
    for showdata in shows:
        count += 1
        ADD_SHOW_ITEM(showdata,cmmode=cmmode,export=export)
    if not search:
        if sortaz:
            if not 'year' in filter: xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
        common.SetView('tvshows', 'showview')
    return count

def ADD_SHOW_ITEM(showdata,mode='listtv',submode='LIST_TV_SEASONS',cmmode=0,onlyinfo=False,export=False):
    asin,seriestitle,plot,network,mpaa,genres,actors,premiered,year,stars,votes,seasontotal,episodetotal,audio,isHD,isprime,empty,empty,empty,poster,banner,fanart = showdata
    infoLabels={'Title': seriestitle,'TVShowTitle':seriestitle}
    if plot:
        infoLabels['Plot'] = plot
    if mpaa:
        infoLabels['MPAA'] = mpaa
    if actors:
        infoLabels['Cast'] = actors.split(',')
    if year:
        infoLabels['Year'] = year
    if premiered:
        infoLabels['Premiered'] = premiered
    if stars:
        infoLabels['Rating'] = stars           
    if votes:
        infoLabels['Votes'] = votes  
    if genres:
        infoLabels['Genre'] = genres 
    if episodetotal:
        infoLabels['Episode'] = episodetotal
    if seasontotal:
        infoLabels['TotalSeasons'] = seasontotal
    if network:
        infoLabels['Studio'] = network
    if audio:
        infoLabels['AudioChannels'] = audio
    if mode == 'listtv':
        submode = 'LIST_TV_SEASONS'
    if poster is None:
        poster=''
    infoLabels['Thumb'] = poster
    infoLabels['Fanart'] = fanart
    infoLabels['Asins'] = asin
    asin = asin.split(',')[0]
    if export:
        xbmclibrary.EXPORT_SHOW(asin)
        return
    cm = []
    cm.append((common.getString(30180+cmmode) % common.getString(30166), 'XBMC.RunPlugin(%s?mode=<common>&sitemode=<toogleWatchlist>&asin=<%s>&remove=<%s>)' % (sys.argv[0], asin, cmmode)))
    cm.append((common.getString(30185) % common.getString(30166), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<EXPORT_SHOW>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30183), 'Container.Update(%s?mode=<appfeed>&sitemode=<getSimilarities>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30186), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<UpdateLibrary>)' % sys.argv[0]))
    cm.append((common.getString(30155) % common.getString(30166), 'XBMC.RunPlugin(%s?mode=<tv>&sitemode=<delfromTVdb>&asins=<%s>&table=<shows>&title=<%s>)' % ( sys.argv[0], urllib.quote_plus(infoLabels['Asins']), urllib.quote_plus(seriestitle))))
    if onlyinfo:
        return infoLabels
    else:
        common.addDir(seriestitle,mode,submode,infoLabels['Asins'],poster,fanart,infoLabels,isHD=isHD,cm=cm)
   
def LIST_TV_SEASONS(seasons=False):
    seriesasin = common.args.url
    import tv as tvDB
    for asin in seriesasin.split(','):
        seasons = tvDB.loadTVSeasonsdb(seriesasin=asin).fetchall()
        for seasondata in seasons:
            ADD_SEASON_ITEM(seasondata)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    common.SetView('tvshows', 'seasonview')

def LIST_TVSEASON_SORTED(seasons=False, cmmode=0):
    import tv as tvDB
    if not seasons:
        seasons = tvDB.loadTVSeasonsdb(sortcol=common.args.url).fetchall()
    for seasondata in seasons:
        ADD_SEASON_ITEM(seasondata, disptitle=True, cmmode=cmmode)
    common.SetView('tvshows', 'seasonview')
        
def ADD_SEASON_ITEM(seasondata, mode='listtv', submode='LIST_EPISODES_DB', disptitle=False, cmmode=0, onlyinfo=False, export=False):
    asin,seriesASIN,season,seriestitle,plot,actors,network,mpaa,genres,premiered,year,stars,votes,episodetotal,audio,empty,empty,isHD,isprime,empty,poster,banner,fanart = seasondata
    infoLabels={'Title': seriestitle,'TVShowTitle':seriestitle}
    if plot:
        infoLabels['Plot'] = plot
    if mpaa:
        infoLabels['MPAA'] = mpaa
    if actors:
        infoLabels['Cast'] = actors.split(',')
    if year:
        infoLabels['Year'] = year
    if premiered:
        infoLabels['Premiered'] = premiered
    if stars:
        infoLabels['Rating'] = stars           
    if votes:
        infoLabels['Votes'] = votes  
    if genres:
        infoLabels['Genre'] = genres 
    if episodetotal:
        infoLabels['Episode'] = episodetotal
    if season:
        infoLabels['Season'] = season
    if network:
        infoLabels['Studio'] = network
    if audio:
        infoLabels['AudioChannels'] = audio
    displayname = ''
    if disptitle: displayname = seriestitle + ' - '
    if season != 0 and len(str(season)) < 3: displayname += common.getString(30167, True) + ' ' + str(season)
    elif len(str(season)) > 2: displayname += common.getString(30168, True) + str(season)
    else: displayname += common.getString(30169, True)
    if showfanart == 'true': 
        fanart, cover = getFanart(seriesASIN)
    infoLabels['TotalSeasons'] = 1
    infoLabels['Thumb'] = poster
    infoLabels['Fanart'] = fanart
    infoLabels['Asins'] = asin
    asin = asin.split(',')[0]
    if export:
        xbmclibrary.EXPORT_SEASON(asin)
        return
    cm = []
    cm.append((common.getString(30180+cmmode) % common.getString(30167), 'XBMC.RunPlugin(%s?mode=<common>&sitemode=<toogleWatchlist>&asin=<%s>&remove=<%s>)' % (sys.argv[0], asin, cmmode)))
    cm.append((common.getString(30185) % common.getString(30167), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<EXPORT_SEASON>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30183), 'Container.Update(%s?mode=<appfeed>&sitemode=<getSimilarities>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30186), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<UpdateLibrary>)' % sys.argv[0]))
    cm.append((common.getString(30155) % common.getString(30167), 'XBMC.RunPlugin(%s?mode=<tv>&sitemode=<delfromTVdb>&asins=<%s>&table=<seasons>&title=<%s>)' % ( sys.argv[0], urllib.quote_plus(infoLabels['Asins']), urllib.quote_plus(displayname))))
    if onlyinfo:
        return infoLabels
    else:
        common.addDir(displayname,mode,submode,infoLabels['Asins'],poster,fanart,infoLabels,isHD=isHD,cm=cm)

def LIST_EPISODES_DB(owned=False, url=False):
    if not url:
        seriestitle = common.args.url
    import tv as tvDB
    for asin in seriestitle.split(','):
        episodes = tvDB.loadTVEpisodesdb(asin)
        for episodedata in episodes:
            ADD_EPISODE_ITEM(episodedata)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    common.SetView('episodes', 'episodeview')
        
def ADD_EPISODE_ITEM(episodedata, onlyinfo=False, export=False):
    asin,seasonASIN,seriesASIN,seriestitle,season,episode,poster,mpaa,actors,genres,episodetitle,network,stars,votes,fanart,plot,airdate,year,runtime,isHD,isprime,isAdult,audio = episodedata
    infoLabels={'Title': episodetitle,'TVShowTitle':seriestitle,
                'Episode': episode,'Season':season}
    if plot:
        infoLabels['Plot'] = plot
    if airdate:
        infoLabels['Premiered'] = airdate 
    if year:
        infoLabels['Year'] = year
    if runtime:
        infoLabels['Duration'] = int(runtime)*60
    if mpaa:
        infoLabels['MPAA'] = mpaa
    if actors:
        infoLabels['Cast'] = actors.split(',')
    if stars:
        infoLabels['Rating'] = stars           
    if votes:
        infoLabels['Votes'] = votes  
    if genres:
        infoLabels['Genre'] = genres 
    if network:
        infoLabels['Studio'] = network
    if audio:
        infoLabels['AudioChannels'] = audio

    displayname = str(episode) + ' - ' + episodetitle 
    displayname = displayname.replace('"','')
    tvfanart, tvposter = getFanart(seriesASIN)
    if showfanart == 'true': 
        fanart = tvfanart
    infoLabels['Fanart'] = fanart
    infoLabels['Thumb'] = poster
    infoLabels['Poster'] = tvposter
    infoLabels['Title'] = displayname
    infoLabels['isHD'] = isHD
    infoLabels['isAdult'] = isAdult
    infoLabels['seriesASIN'] = seriesASIN
    asin = asin.split(',')[0]
    if export:
        xbmclibrary.EXPORT_EPISODE(asin)
        return
    cm = []
    cm.append((common.getString(30185) % common.getString(30173), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<EXPORT_EPISODE>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30183), 'Container.Update(%s?mode=<appfeed>&sitemode=<getSimilarities>&asin=<%s>)' % (sys.argv[0], asin)))
    cm.append((common.getString(30186), 'XBMC.RunPlugin(%s?mode=<xbmclibrary>&sitemode=<UpdateLibrary>)' % sys.argv[0]))
    if onlyinfo:
        return infoLabels
    else:
        common.addVideo(displayname,asin,poster,fanart,infoLabels=infoLabels,isAdult=isAdult,isHD=isHD,cm=cm)
        
def getFanart(asin):
    import tv
    fanart, poster = tv.lookupTVdb(asin, rvalue='fanart, poster', tbl='shows')
    if not fanart or fanart == common.na:
        fanart = poster
    return fanart, poster