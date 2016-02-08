# -*- coding: utf-8 -*-
import os, sys, datetime, signal, subprocess
from time import sleep
from re import findall
from copy import copy
from operator import itemgetter

epg = SharedCodeService.epg
const = SharedCodeService.constants
api = SharedCodeService.api

ART = 'fanart.jpg'
ICON = 'icon.png'
NAME = L('NAME')


def Start():
    Plugin.AddPrefixHandler("/video/weebtv",MainMenu,NAME,ICON,ART)
    Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")
    Plugin.AddViewGroup('Details', viewMode='InfoList', mediaType='items')
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = "List"
    DirectoryObject.thumb = R(ICON)
    #Thread.Create(Scanner)
    #Thread.Lock('dict')
    if Prefs['username'] and Prefs['password']:
        Dict['loggedIn'] = api.Login(Prefs['username'],Prefs['password'])
    Dict['channels'] = {}
    
   
#@handler('/video/weebtv', 'WeebTV')
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(LiveChannels,page=1,action='live'),title=L("MENU_LIVE_CHANNELS")))
    if Dict['fav']:    
        oc.add(DirectoryObject(key=Callback(LiveChannels,page=1,action='fav'),title=L("MENU_FAVOURITE_CHANNELS"),thumb=R('favorites.png')))
    #oc.add(DirectoryObject(key=Callback(ManageRecordings),title=L("MENU_MANAGE_RECORDINGS"),thumb=R('record.png')))
    if Dict['loggedIn']:
        oc.add(DirectoryObject(key=Callback(MyAccount),title=L("MENU_MY_ACCOUNT")))
    oc.add(PrefsObject(title=L("SETTINGS")))
    return oc
    
    
@route('/video/weebtv/channels')    
def LiveChannels(page,action):
    oc = ObjectContainer()
    oc.no_cache = True
    dChannels = api.GetChannelsFromApi()
    Dict['channels'] = dChannels
    lOrder = sorted(dChannels)
    sType = 'Live'
    if action == 'fav':
        lOrder = sorted(Dict['fav'])
        sType = 'Favourite'

    nextPage = None
    chPerPage = Prefs["epgChanPerPage"]
    if chPerPage == "All":
        lChannelsToShow = lOrder
        oc.title2 = '{} Channels'.format(sType)
    else:
        iChannels = len(lOrder) 
        pages = iChannels / int(chPerPage)
        reminder = iChannels % int(chPerPage)
        if reminder:
            pages = pages + 1
        if int(page) < pages:
            nextPage = int(page) + 1
        if len(lOrder[(int(page)-1)*int(chPerPage):]) < int(chPerPage):
            lChannelsToShow = lOrder[(int(page)-1)*int(chPerPage):]
        else:   
            lChannelsToShow = lOrder[(int(page)-1)*int(chPerPage):int(chPerPage)*int(page)]
        oc.title2 = '{} Channels {}/{}'.format(sType,page,pages)
  
    bContinue = True

    if bContinue:
        for channel in lChannelsToShow:
            if channel in Dict['channels']:
                channelTitle = unicode(Dict['channels'][channel]['channel_title'])
                channelDesc = unicode(Dict['channels'][channel]['channel_description'])
                channelName = Dict['channels'][channel]['channel_name']
                if not channelTitle:
                    channelTitle = channelName
                channelCid = Dict['channels'][channel]['cid']
                channelImage = Dict['channels'][channel]['channel_logo_url']
                channelHost = Dict['channels'][channel]['user_name']
                channelTags = Dict['channels'][channel]['channel_tags']
                thumb = channelImage
                oc.add(DirectoryObject(key=Callback(ChannelMenu,cid=channel),title=channelTitle,thumb=thumb,summary=channelDesc))
            else:
                oc.add(DirectoryObject(key=Callback(ChannelMenu,cid=channel),title=channel,summary='Channel no longer available'))
        if not dChannels:
            Log('Channels list from API is EMPTY')
            return MessageContainer('ERROR',L("MESSAGE_NO_CHANNELS"))
        if nextPage:
            oc.add(DirectoryObject(key=Callback(LiveChannels,page=nextPage,action=action),title='NEXT',summary='Page: {}'.format(nextPage),thumb=R('next.jpg')))
    else:
        return MessageContainer('ERROR',L("MESSAGE_FAV_NOT_AVAILABLE"))
    return oc


@route('/video/weebtv/channel/{cid}')
def ChannelMenu(cid):
    Log('CID2: {}'.format(cid))
    oc = ObjectContainer()
    oc.no_cache = True
    if cid in Dict['channels']:
        channelDict = Dict['channels'][cid]
        oc = ObjectContainer()
        oc.no_cache = True
        oc.title2 = channelDict['channel_title']
        duration = None
        originally_available_at = None
        show = None

        title = unicode(channelDict['channel_title'])
        summary = unicode(channelDict['channel_description'])
        thumb = channelDict['channel_image']
        show = title
        oc.add(EpisodeObject(
            url = '{}/channel/{}'.format(const.mainUrl,channelDict['channel_name']),
            title = title,
            summary = summary,
            duration = duration,
            show = show,
            source_title = unicode(channelDict['channel_title']),
            originally_available_at = originally_available_at,
            thumb = thumb))
        #oc.add(PopupDirectoryObject(key=Callback(RecordMenu,cid=cid),title=L("SUBMENU_RECORD"),summary=L("SUBMENU_RECORD_SUMMARY")))
        #oc.add(DirectoryObject(key=Callback(ShowChannelEpg,cid=cid),title=L("SUBMENU_EPG"),summary=L("SUBMENU_EPG_SUMMARY")))
    if Dict['fav']: 
        if cid in Dict['fav']:    
            oc.add(DirectoryObject(key=Callback(FavRemoveChannel,cid=cid),title=L("SUBMENU_REMOVE"),thumb=R('favorites.png')))
        else:
            oc.add(DirectoryObject(key=Callback(FavAddChannel,cid=cid),title=L("SUBMENU_ADD"),thumb=R('favorites.png')))
    else:
        oc.add(DirectoryObject(key=Callback(FavAddChannel,cid=cid),title=L("SUBMENU_ADD"),thumb=R('favorites.png')))
    return oc


@route('/video/weebtv/fav_add')
def FavAddChannel(cid):
    if Dict['fav']:
        if cid not in Dict['fav']:
            Dict['fav'][cid] = True
            return MessageContainer(cid,L("MESSAGE_ADDED"))
    else:
        Dict['fav'][cid] = True
        return MessageContainer(cid,L("MESSAGE_ADDED"))


@route('/video/weebtv/fav_remove')
def FavRemoveChannel(cid):
    if Dict['fav']:
        if cid in Dict['fav']:
            Dict['fav'].pop(cid)
            return MessageContainer(cid,L("MESSAGE_REMOVED"))
    else:
        return MessageContainer(cid,L("MESSAGE_NOTHING"))


@route('/video/weebtv/record')
def RecordMenu(cid):
    channelDict = Dict['channels'][cid]
    oc = ObjectContainer()
    oc.title2 = 'REC: {}'.format(channelDict['channel_title'])
    oc.add(DirectoryObject(key=Callback(StartRecord,cid=cid,query=1800),title=str(L("OPTION_RECORD")).format(1800/60)))
    oc.add(DirectoryObject(key=Callback(StartRecord,cid=cid,query=3600),title=str(L("OPTION_RECORD")).format(3600/60)))
    oc.add(DirectoryObject(key=Callback(StartRecord,cid=cid,query=5400),title=str(L("OPTION_RECORD")).format(5400/60)))
    oc.add(DirectoryObject(key=Callback(StartRecord,cid=cid,query=7200),title=str(L("OPTION_RECORD")).format(7200/60)))
    oc.add(DirectoryObject(key=Callback(StartRecord,cid=cid,query=9000),title=str(L("OPTION_RECORD")).format(9000/60)))
    oc.add(InputDirectoryObject(key=Callback(StartRecord,cid=cid),title=L("OPTION_RECORD_CUSTOM"),prompt=L("MESSAGE_FOR_HOW_LONG")))
    #Log(output)
    return oc


@route('/video/weebtv/rec')
def ManageRecordings():
    oc = ObjectContainer()
    oc.title2 = L("MENU_MANAGE_RECORDINGS")
    oc.add(DirectoryObject(key=Callback(RecordingsMenu),title=L("SUBMENU_RECORDINGS")))
    oc.add(DirectoryObject(key=Callback(LiveRecordingsMenu),title=L("SUBMENU_RECORDNIG_NOW")))
    oc.add(DirectoryObject(key=Callback(StopRecord),title=L("SUBMENU_STOP_ALL")))
    return oc


@route('/video/weebtv/rec/now')    
def LiveRecordingsMenu():
    oc = ObjectContainer()
    oc.no_cache = True
    oc.title2 = L("SUBMENU_RECORDNIG_NOW")
    dRec = Dict['rec']
    for pid in dRec:
        oc.add(DirectoryObject(key=Callback(DoNothing),title=dRec[pid]['filename']))
    if not dRec:
        return MessageContainer('ERROR',L("MESSAGE_NO_LIVE"))
    return oc


@route('/video/weebtv/rec/recorded')    
def RecordingsMenu():
    oc = ObjectContainer()
    oc.no_cache = True
    oc.title2 = L("SUBMENU_RECORDINGS")
    if Prefs['downloadPath'] == './':
        return MessageContainer('WARNING',L("MESSAGE_DIR_NOT_SET"))
    lFiles = GetRecordings()
    for file in lFiles:
        bLive = False
        for item in Dict['rec']:
            if file == Dict['rec'][item]['filename']:
                bLive = True
        if bLive:
            file = 'LIVE: {}'.format(file)
        oc.add(DirectoryObject(key=Callback(DoNothing),title=file))
    if not lFiles:
        return ObjectContainer(header='ERROR',message=L("MESSAGE_NO_RECORDED"))
    return oc


def Scanner(interval=30):
    Log('Starting to monitor live recordings every {} seconds'.format(interval))
    cmd = 'ps x'
    while True:
        live = copy(Dict['rec'])
        #check for any finished recordings, and remove them from Dict['rec']
        if live:
            output = subprocess.check_output(cmd.split())
        else:
            Log('No live recordings')
        for pid in live:
            if output:
                Log(output)
                output = output.splitlines()
                pids = []
                for line in output:
                    if 'rtmpdump' in line:
                        pids.append(line.split()[0].strip())
                if str(pid) in pids:
                    Log('process {} is still live'.format(pid))
                else:
                    Log('process {} is no longer live'.format(pid))
                    Thread.AcquireLock('dict')
                    Dict['rec'].pop(pid)
                    Thread.ReleaseLock('dict')
            else:
                Log('Failed to get output from "{}" command'.format(cmd))
        #check for any programmed recordings in 2xinterval
        #TODO
                    
        sleep(interval)
        

def GetRecordings():
    output = subprocess.check_output(['ls',Prefs['downloadPath']])
    lFiles = findall('weebtv_.*_[0-9]*\.flv',output)
    return lFiles
    

@route('/video/weebtv/rec/start')
def StartRecord(cid,query):
    if Prefs['downloadPath'] == './':
        return MessageContainer('ERROR',L("MESSAGE_DIR_NOT_SET"))
    channelDict = Dict['channels'][cid]
    multi = channelDict['multibitrate']
    params = api.GetLinkInfo(channelDict['cid'],multi,Prefs['username'],Prefs['password'])
    quality = ''
    if Prefs['recQuality'] == 'High' and int(multi) == 1:
        quality = Prefs['recQuality']
    if params['rtmpLink']:
        channelCid = channelDict['cid']
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
        filename = 'weebtv_{}_{}.flv'.format(channelDict['channel_name'],timestamp)
        rtmpDump = "rtmpdump -V -r {0} -y {1}{6} -a {1}/{2} -p token -s {3} --live -o {4}/{5}".format(params['rtmpLink'],params['playPath'],channelCid,params['ticket'],Prefs['downloadPath'],filename,quality)
        Log('Start recording {} - {}'.format(channelDict['channel_name'],filename))
        Log(rtmpDump)
        absPath = os.path.abspath(os.path.curdir)
        absPath = absPath.replace('Plug-in Support/Data/tv.weeb.plexapp.weebtv','Plug-ins/WeebTV.bundle/Contents/Code/')
        absPath = absPath.replace(' ','\ ')
        cmd = '{}dumpstream.py "{}" {}'.format(absPath,rtmpDump,query)
        Log(cmd)
        process = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True,preexec_fn=os.setsid)
        Dict['rec'][process.pid] = {'filename':filename,'date':'timestamp','title':channelDict['channel_name']}
        Dict.Save()
        message = str(L("MESSAGE_STARTED")).format(filename,query)
    else:
        Log("Not recording - params are wrong: {}".format(params))
        message = L("MESSAGE_FAILED")
    return MessageContainer('RECORD',message)


@route('/video/weebtv/rec/stop')
def StopRecord(pid=None):
    if pid:
        dStop = {pid:''}
    else: #stop all
        dStop = copy(Dict['rec'])
    for pid in dStop:
        Log('Stopping PID: {}'.format(pid))
        try: #TODO: check for that process on processes list firts
            os.killpg(pid,signal.SIGTERM)
        except:
            pass
        if pid in Dict['rec']:
            Dict['rec'].pop(pid)
            Dict.Save()
    return ObjectContainer(header='EMPTY',message=L("MESSAGE_STOPPED"))


@route('/video/weebtv/account')
def MyAccount():
    oc = ObjectContainer()
    oc.title2 = L("MENU_MY_ACCOUNT")
    if not Dict['loggedIn']:
        Dict['loggedIn'] = api.Login(Prefs['username'],Prefs['password'])
    dAcc = api.AccountDetails()
    Log(dAcc)
    for item in dAcc:
        oc.add(DirectoryObject(key=Callback(DoNothing),title='{}: {}'.format(item,dAcc[item])))    
    return oc


def DoNothing():
    return


