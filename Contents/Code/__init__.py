# -*- coding: utf-8 -*-
import os, sys, datetime, signal, subprocess
from time import sleep
from re import findall
from copy import copy
from operator import itemgetter

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


