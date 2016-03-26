#!/usr/bin/env python
# -*- coding: utf-8 -*-
import common
import xbmcplugin
import sys

# Movie listing


def LIST_MOVIE_ROOT():
    common.addDir(common.getString(30100), 'listmovie', 'LIST_MOVIES_SORTED', 'popularity')
    common.addDir(common.getString(30149), 'listmovie', 'LIST_MOVIES_CATS')
    common.addDir(common.getString(30143), 'listmovie', 'LIST_MOVIES')
    common.addDir(common.getString(30144), 'listmovie', 'LIST_MOVIE_TYPES', 'genres')
    common.addDir(common.getString(30145), 'listmovie', 'LIST_MOVIE_TYPES', 'year')
    common.addDir(common.getString(30146), 'listmovie', 'LIST_MOVIE_TYPES', 'studio')
    common.addDir(common.getString(30158), 'listmovie', 'LIST_MOVIE_TYPES', 'actors')
    common.addDir(common.getString(30147), 'listmovie', 'LIST_MOVIE_TYPES', 'mpaa')
    common.addDir(common.getString(30148), 'listmovie', 'LIST_MOVIE_TYPES', 'director')
    xbmcplugin.endOfDirectory(common.pluginhandle)


def LIST_MOVIES_CATS():
    import movies as moviesDB
    id_ = common.args.url
    if id_:
        asins = moviesDB.lookupMoviedb(id_, rvalue='asins', name='title', table='categories')
        for asin in asins.split(','):
            LIST_MOVIES('asin', asin, search=True)
        common.SetView('movies')
    else:
        for title in moviesDB.lookupMoviedb('', name='asins', table='categories', single=False):
            if title:
                common.addDir(title[0], 'listmovie', 'LIST_MOVIES_CATS', title[0])
        xbmcplugin.endOfDirectory(common.pluginhandle, updateListing=False)


def LIST_MOVIE_TYPES(type=False):
    import movies as moviesDB
    if not type:
        type = common.args.url
    if type:
        mode = 'LIST_MOVIES_FILTERED'
    for item in moviesDB.getMovieTypes(type):
        common.addDir(item, 'listmovie', mode, type)
    xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.pluginhandle, updateListing=False)


def LIST_MOVIES_FILTERED():
    LIST_MOVIES(common.args.url, common.args.name)


def LIST_MOVIES_SORTED():
    LIST_MOVIES(sortaz=False, sortcol=common.args.url)


def LIST_MOVIES(filter='', value=False, sortcol=False, sortaz=True, search=False, cmmode=0):
    import movies as moviesDB
    if 'year' in filter:
        value = value.replace('0 -', '')
    movies = moviesDB.loadMoviedb(filter=filter, value=value, sortcol=sortcol)
    count = 0
    for moviedata in movies:
        count += 1
        ADD_MOVIE_ITEM(moviedata, cmmode=cmmode)
    if not search:
        if sortaz:
            if 'year' not in filter:
                xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
            xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
            xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
            xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_DURATION)
            xbmcplugin.addSortMethod(common.pluginhandle, xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
        common.SetView('movies')
    return count


def ADD_MOVIE_ITEM(moviedata, cmmode=0):
    asin, hd_asin, movietitle, trailer, poster, plot, director, writer, runtime, year, premiered, studio, mpaa, actors, genres, stars, votes, fanart, isprime, isHD, isAdult, popularity, recent, audio = moviedata
    infoLabels = {'Title': movietitle,
                  'Plot': plot,
                  'mediatype': "movie",
                  'Cast': actors.split(',') if actors else [],
                  'Director': director,
                  'Year': year,
                  'Premiered': premiered,
                  'Rating': stars,
                  'Votes': votes,
                  'Genre': genres,
                  'mpaa': mpaa,
                  'Studio': studio,
                  'Duration': int(runtime) * 60,
                  'AudioChannels': audio,
                  'Thumb': poster,
                  'Fanart': fanart,
                  'isHD': isHD,
                  'isAdult': isAdult}
    asin = asin.split(',')[0]
    cm = []
    cm.append((common.getString(30180 + cmmode) % common.getString(30154), 'XBMC.RunPlugin(%s?mode=<common>&sitemode=<toggleWatchlist>&asin=<%s>&remove=<%s>)' % (sys.argv[0], asin, cmmode)))
    cm.append((common.getString(30183), 'Container.Update(%s?mode=<appfeed>&sitemode=<getSimilarities>&asin=<%s>)' % (sys.argv[0], asin)))
    common.addVideo(movietitle, asin, poster, fanart, infoLabels=infoLabels, cm=cm, trailer=trailer, isAdult=isAdult, isHD=isHD)
