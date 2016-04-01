import xbmc
import xbmcaddon

import_suc = False
while not import_suc:
    import_suc = True
    try:
        from datetime import datetime, timedelta
        datetime.today()
        datetime.strptime('1970-01-01', '%Y-%m-%d')
        timedelta()
    except Exception:
        import_suc = False
        xbmc.sleep(2000)

if __name__ == '__main__':
    xbmc.log('AmazonDB: Service Start')
    addon = xbmcaddon.Addon()
    addon.setSetting('update_running', 'false')
    freq = addon.getSetting('auto_update')
    addon_id = addon.getAddonInfo('id')
    idleupdate = 300
    startidle = 0
    monitor = xbmc.Monitor()

    if (not freq == '') and (not freq == '0'):
        while not monitor.abortRequested():
            today = datetime.today()
            freq = addon.getSetting('auto_update')
            last = addon.getSetting('last_update')
            time = addon.getSetting('update_time')
            update = addon.getSetting('update_running')
            if last == '':
                last = '1970-01-01'
            if time == '':
                time = '00:00'
            if freq == '0':
                break
            dt = last + ' ' + time
            dtlast = datetime.strptime(dt, '%Y-%m-%d %H:%M')
            freqdays = [0, 1, 2, 5, 7][int(freq)]
            lastidle = xbmc.getGlobalIdleTime()
            if xbmc.Player().isPlaying():
                startidle = lastidle
            if lastidle < startidle:
                startidle = 0
            idletime = lastidle - startidle
            if addon.getSetting('wait_idle') != 'true':
                idletime = idleupdate

            if dtlast + timedelta(days=freqdays) <= today and idletime >= idleupdate:
                if update == 'false':
                    xbmc.log('AmazonDB: Starting DBUpdate (%s / %s)' % (dtlast, today))
                    xbmc.executebuiltin('XBMC.RunPlugin(plugin://%s/?mode=<appfeed>&sitemode=<updateAll>)' % addon_id)
                    if monitor.waitForAbort(10):
                        break
                else:
                    starttime = datetime.strptime(update, '%Y-%m-%d %H:%M')
                    if (starttime + timedelta(hours=6)) <= today:
                        addon.setSetting('update_running', 'false')
                        xbmc.log('AmazonDB: Cancel update - duration > 6 hours')
                    else:
                        xbmc.log('AmazonDB: Update already running', xbmc.LOGDEBUG)
            if monitor.waitForAbort(5):
                break
    xbmc.log('AmazonDB: Service End')
