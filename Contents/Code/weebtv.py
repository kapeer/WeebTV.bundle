# -*- coding: utf-8 -*-
import urllib, urllib2, httplib
import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import threading
import simplejson as json
import datetime
import time
import traceback

scriptID = 'plugin.video.polishtv.live'
t = sys.modules[ "__main__" ].language
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
#sys.path.append( os.path.join( os.getcwd(), "../" ) )

import pLog, settings, Parser, Navigation, pCommon, Errors

log = pLog.pLog()

mainUrl = 'http://weeb.tv'
playerUrl = mainUrl + '/api/setplayer'
apiUrl = mainUrl + '/api/getChannelList'
iconUrl = 'http://static2.weeb.tv/ci/'
HOST = 'XBMC'

login = ptv.getSetting('weebtv_login')
password = ptv.getSetting('weebtv_password')
multi = ptv.getSetting('weebtv_hq')
record = ptv.getSetting('weebtv_rec')
rtmppath = ptv.getSetting('default_rtmp')
dstpath = ptv.getSetting('default_dstpath')
timedelta_h = ptv.getSetting('default_timedelta_hours')
timedelta_m = ptv.getSetting('default_timedelta_minutes')
strmdir = ptv.getSetting('weebtv_strm')
sortby = ptv.getSetting('weebtv_sort')
dbg = ptv.getSetting('default_debug')

VIDEO_MENU = [ "Nagrywanie", "Odtwarzanie", "Zaprogramowanie nagrania" ]

SKINS = {
        'confluence': { 'opt1': 500, 'opt2': 50 },
        'transparency': { 'opt1': 53, 'opt2': 590 }
}




class Channels:
	def __init__(self):
		self.common = pCommon.common()
		self.exception = Errors.Exception()

	def dec(self, string):
		json_ustr = json.dumps(string, ensure_ascii=False)
		return json_ustr.encode('utf-8')

	def SortedTab(self, json):
		strTab = []
		outTab = []
		for v,k in json.iteritems():
			strTab.append(int(v))
			strTab.append(k)
			outTab.append(strTab)
			strTab = []
		outTab.sort(key=lambda x: x[0])
		return outTab
	
	def API(self, url):
            if login == "" or password == "":
                d = xbmcgui.Dialog()
                d.ok(t(55014).encode("utf-8"), t(55015).encode("utf-8"), t(55016).encode("utf-8"))
                exit()
            else:
		query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': True, 'return_data': True }
		res = { "0": "Null" }
		try:
			post = { 'username': login, 'userpassword': password }
			res = json.loads(self.common.getURLRequestData(query_data, post))
		except Exception, exc:
			res = { "0": "Error" }
			traceback.print_exc()
			self.exception.getError(str(exc))
			exit()
		return res

	def ChannelsList(self, url):
		action = 0
		channelsArray = self.SortedTab(self.API(url))
		if len(channelsArray) > 0:
			try:
				if channelsArray[0][1] == 'Null':
					msg = xbmcgui.Dialog()
					msg.ok("Błąd API", "Brak kanałów pobranych z API.")
				elif channelsArray[0][1] != 'Error' and channelsArray[0][1] != 'Null':
					for i in range(len(channelsArray)):
						row = channelsArray[i][1]
						cid = row['cid']
						name = self.dec(row['channel_name']).replace("\"", "")
						title = self.dec(row['channel_title']).replace("\"", "")
						if title == "":
							title = name;
						desc = self.dec(row['channel_description']).replace("\"", "")
						tags = self.dec(row['channel_tags']).replace("\"", "")
						img = row['channel_image']
						online = row['channel_online']
						rank = row['rank']
						bitrate = row['multibitrate']
						user = self.dec(row['user_name']).replace("\"", "")
						image = iconUrl + "no_video.png"
						if img == '1':
							image = iconUrl + cid + ".jpg"
						if online == '2':
							action = 1
						else:
							action = 0
						self.addChannel('weebtv', str(action), cid, title, image, desc, tags, user, name)
					s = Settings()
					s.setViewMode('other')
					xbmcplugin.endOfDirectory(int(sys.argv[1]))
			except KeyError, keyerr:
				msg = xbmcgui.Dialog()
				traceback.print_exc()
				msg.ok("Błąd API", "Błędny klucz odczytany z API.")				
		else:
			msg = xbmcgui.Dialog()
			msg.ok("Błąd API", "Brak kanałów pobranych z API.")

        def addChannel(self, service, action, cid, title, img, desc, tags, user, name):
            label = title
            liz = xbmcgui.ListItem(label, iconImage = "DefaultFolder.png", thumbnailImage = img)
            liz.setProperty("IsPlayable", "false")
            liz.setInfo(type = "Video", infoLabels={ "Title": title,
										   "Plot": desc,
										   "Studio": "WEEB.TV",
										   "Tagline": tags,
										   "Aired": user } )
            u = '%s?service=%s&action=%d&cid=%d&title=%s' % (sys.argv[0], str(service), int(action), int(cid), urllib.quote_plus(title))
            xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)
            if strmdir != 'None':
                if not os.path.isdir(strmdir):
                    os.mkdir(strmdir)
                FILE = open(os.path.join(strmdir, "%s.strm" % ''.join(c for c in title if c in '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')),"w+")
                FILE.write("plugin://plugin.video.polishtv.live/?service=%s&action=%d&cid=%s&title=%s" % (service, int(action), cid, urllib.quote_plus(title)))


class Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.is_active = True
        print "#Starting control WeebPlayer events#"

    def setPremium(self, premium):
        self.premium = premium
        
    def getPremium(self):
        return self.premium
    
    def onPlayBackPaused(self):
        print "#Im paused#"
        ThreadPlayerControl("Stop").start()
        self.is_active = False
        
    def onPlayBackResumed(self):
        print "#Im Resumed #"
        
    def onPlayBackStarted(self):
        print "#Playback Started#"
        try:
            print "#Im playing :: " + self.getPlayingFile()
        except:
            print "#I failed get what Im playing#"
            
    def onPlayBackEnded(self):
        msg = xbmcgui.Dialog()
        print "#Playback Ended#"
        self.is_active = False
        if self.getPremium() == 0:
            msg.ok("Błąd odtwarzania.", "Przekroczony limit lub zbyt duża liczba użytkowników.", "Wykup konto premium aby oglądać bez przeszkód.")
        else:
            msg.ok("Błąd odtwarzania.", "Serwer odrzucił połączenie z nieznanych przyczyn.")
        
    def onPlayBackStopped(self):
        print "## Playback Stopped ##"
        self.is_active = False
    
    def sleep(self, s):
        xbmc.sleep(s)
        
		

class Video:
    def __init__(self):
        self.common = pCommon.common()
        self.exception = Errors.Exception()
        
    def InputTime(self):
        nowTime = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
        text = None
        k = xbmc.Keyboard(str(nowTime.strftime("%H:%M")), "Początek nagrania: " + str(nowTime.strftime("%H:%M")) + ". Czas zakończenia [HH:MM]:")
        k.doModal()
        if (k.isConfirmed()):
            text = k.getText()
        return self.GetTime(text)
    
    def GetTime(self, end):
        rectime = 0
        if ":" in end:
            nowTime = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
            st = time.mktime(nowTime.timetuple())
            nowDate = str(nowTime.strftime("%Y-%m-%d"))
            t = end.split(":")
            tH = t[0]
            tM = t[1]
            tS = "00"
            endTime = nowDate + " " + str(tH) + ":" + str(tM) + ":" + str(tS) + ".0"
            endFormat = "%Y-%m-%d %H:%M:%S.%f"
            endTuple = time.strptime(endTime, endFormat)
            et = time.mktime(datetime.datetime(*endTuple[:7]).timetuple())
            rectime = int(et - st)
            if rectime < 0:
                rectime = 0
        return rectime
        

    def LinkParams(self, channel):
        data = None
        if login == '' and password == '':
            values = { 'cid': channel, 'platform': 'XBMC' }
        else:
            values = { 'cid': channel, 'username': login, 'userpassword': password, 'platform': 'XBMC' }
        try:
            parser = Parser.Parser()
            query_data = { 'url': playerUrl, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': True, 'return_data': True }
            resLink = self.common.getURLRequestData(query_data, values)
            params = parser.getParams(resLink)
            ticket = parser.getParam(params, "73")
            rtmpLink = parser.getParam(params, "10")
            playPath = parser.getParam(params, "11")
            premium = parser.getIntParam(params, "5")
            status = parser.getParam(params, "0")
            data = { 'rtmp': rtmpLink, 'ticket': ticket, 'playpath': playPath, 'premium': premium, 'status': status }
        except urllib2.URLError, urlerr:
            msg = xbmcgui.Dialog()
            data = { 'rtmp': None, 'ticket': None, 'playpath': None, 'premium': premium, 'status': status }
            traceback.print_exc()
            msg.ok("Błąd setPlayer.", "Nie uzyskano danych do autoryzacji.", "Sprawdź połączenie sieciowe.")
        return data

    def LinkPlayable(self, channel, bitrate):
        dataLink = {}
        vals = self.LinkParams(channel)
        rtmpLink = vals['rtmp']
        ticket = vals['ticket']
        playpath = vals['playpath']
        premium = vals['premium']
        status = vals['status']
        if bitrate == '1' and multi == 'true':
            playpath = playpath + 'HI'
        rtmp = str(rtmpLink) + '/' + str(playpath)
        rtmp += ' swfUrl='  + str(ticket)
        rtmp += ' pageUrl=token'
        rtmp += ' live=true'
        print 'Output rtmp link: %s' % (rtmp)
        return { 'rtmp': rtmp, 'premium': premium, 'status': status, 'ticket': '' }

    def LinkRecord(self, channel, bitrate):
        dataLink = {}
        vals = self.LinkParams(channel)
        rtmpLink = vals['rtmp']
        ticket = vals['ticket']
        playpath = vals['playpath']
        premium = vals['premium']
        status = vals['status']
        if bitrate == '1' and multi == 'true':
            playpath = playpath + 'HI'
        rtmp = str(rtmpLink) + '/' + str(playpath)
        return { 'rtmp': rtmp, 'premium': premium, 'status': status, 'ticket': ticket }

    def ChannelInfo(self, channel):
        chan = Channels()
        dataInfo = { 'title': '', 'image': '', 'bitrate': '' }
        try:
            channelsArray = chan.API(apiUrl)
            for v,k in channelsArray.items():
                if channel == int(k['cid']):
                    cid = k['cid']
                    title = chan.dec(k['channel_title']).replace("\"", "")
                    bitrate = k['multibitrate'] 
                    img = k['channel_image']
                    image = iconUrl + "no_video.png"
                    if img == '1':
                        image = iconUrl + cid + ".jpg"
                    dataInfo = { 'title': title, 'image': image, 'bitrate': bitrate }
                    break
        except TypeError, typerr:
            print typerr
        return dataInfo        

    def RunVideoLink(self, channel):
        rectime = 0
        item = 1
        videoLink = { 'status': '0' }
        val = self.ChannelInfo(channel)
        if record == 'true':
            d = xbmcgui.Dialog()
            item = d.select("Wybór", VIDEO_MENU)
            print 'item: ' + str(item)
            if item != '':
                if item == 1:
                    videoLink =  self.LinkPlayable(channel, val['bitrate'])
                elif item == 0:
                    dwnl = RTMPDownloader()
                    if dwnl.isRTMP(rtmppath):
                        rectime = self.InputTime()
                        videoLink =  self.LinkRecord(channel, val['bitrate'])
                    else:
                        msg = xbmcgui.Dialog()
                        msg.ok("Informacja", "Nie masz zainstalowanego rtmpdump")
                elif item == 2:
                    rec = Record()
                    rec.Init(channel, val['title'])
                    exit()
        else:
            videoLink =  self.LinkPlayable(channel, val['bitrate'])               
        if videoLink['status'] == '1':
            if videoLink['rtmp'].startswith('rtmp://') and item == 1:
                liz = xbmcgui.ListItem(val['title'], iconImage = val['image'], thumbnailImage = val['image'])
                liz.setInfo( type="Video", infoLabels={ "Title": val['title'], } )
                try:
                    player = Player()
                    player.setPremium(int(videoLink['premium']))
                    player.play(videoLink['rtmp'], liz)
                    while player.is_active:
                        player.sleep(100)
                except:
                    msg = xbmcgui.Dialog()
                    msg.ok("Błąd odtwarzania", "Wystąpił nieznany błąd.", "Odtwarzanie wstrzymano.")
            elif videoLink['rtmp'].startswith('rtmp://') and item == 0:
                if os.path.isdir(dstpath):
                    if rectime > 0:
                        dwnl = RTMPDownloader()
                        params = { "url": videoLink['rtmp'], "download_path": dstpath, "title": val['title'], "live": "true", "swfUrl": videoLink['ticket'], "pageUrl": "token", "duration": int(rectime) }
                        dwnl.download(rtmppath, params)
            else:
                msg = xbmcgui.Dialog()
                msg.ok("Błąd", "Odtwarzanie wstrzymane", "z powodu błędnego linku rtmp")
        else:
            msg = xbmcgui.Dialog()
            msg.ok("Informacja", "Wystąpił problem po stronie serwera weeb.tv")



class ThreadPlayerControl(threading.Thread):
	def __init__(self, command):
		self.command = command
		threading.Thread.__init__ (self)
	
	def run(self):
		xbmc.executebuiltin('PlayerControl(' + self.command + ')')


class RTMPDownloader: 
    def isRTMP(self, fpath):
        res = False
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            res = True
        return res

    def download(self, app, params = {}):
        td = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
        nt = time.mktime(td.timetuple())
        today = datetime.datetime.fromtimestamp(nt)
        file = os.path.join(str(params['download_path']), str(params['title']).replace(" ", "_") + "-" + str(today).replace(" ", "_").replace(":", ".") + ".flv")
        #rectime = int(60 * int(params['duration']))
        os.system(str(app) + " -B " + str(params['duration']) + " -r " + str(params['url']) + " -s " + str(params['swfUrl']) + " -p token -v live -o " + file)


class Record:
    def __init__(self):
        self.recdir = os.path.join(ptv.getAddonInfo('path'), "recs")
        self.cmddir = os.path.join(ptv.getAddonInfo('path'), "cmd")

    def input(self, text, header):
        k = xbmc.Keyboard(text, header)
        k.doModal()
        if (k.isConfirmed()):
            text = k.getText()
        return text
    
    def Init(self, channel, title):
        nowTime = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
        nowDate = str(nowTime.strftime("%Y-%m-%d"))
        nTime = str(nowTime.strftime("%H:%M"))
        s_Date = self.input(nowDate, "Wprowadź datę początku nagrania")
        s_Start = self.input(nTime, "Początek nagrania")
        e_Date = self.input(nowDate, "Wprowadź datę końca nagrania")
        e_End = self.input(nTime, "Koniec nagrania")
        setTime = self.SetTime(s_Date, s_Start, e_Date, e_End)
        nameRec = title.replace(" ", "_") + "_" + s_Date + "." + s_Start.replace(":", ".")
        opts = { 'service': 'weebtv', 'date': s_Date, 'start': s_Start, 'rectime': str(setTime[1]), 'name': nameRec, 'channel': channel, 'login': login, 'password': password, 'hq': multi, 'dst_path': dstpath, 'rtmp_path': rtmppath, 'hours_delta': timedelta_h, 'minutes_delta': timedelta_m, 'urlPlayer': playerUrl }
        self.saveFile(opts)
        xbmc.executebuiltin('AlarmClock(' + str(nameRec) + ', "RunScript(' + str(self.cmddir) + str(os.sep) + 'record.py, ' + str(self.recdir) + str(os.sep) + str(nameRec) + '.json)", ' + str(setTime[0]) + '))')
        
    def saveFile(self, opts = {}):
        out = json.dumps(opts)
        file = self.recdir + os.sep + opts['name'] + '.json'
        wfile = open(file, "w")
        wfile.write(out)
        wfile.close()

    def SetTime(self, startDate, startTime, endDate, endTime):
        nowTime = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
        start = startDate + " " + startTime + ":00.0"
        end = endDate + " " + endTime + ":00.0"
        format = "%Y-%m-%d %H:%M:%S.%f"
        startTuple = time.strptime(start, format)
        endTuple = time.strptime(end, format)
        nt = time.mktime(nowTime.timetuple())
        st = time.mktime(datetime.datetime(*startTuple[:7]).timetuple())
        et = time.mktime(datetime.datetime(*endTuple[:7]).timetuple())
        alarmtime = int(float(st - nt) / 60)
        rectime = int(et - st)
        return [ alarmtime, rectime ]

    def GetAlarmTime(self, startDate, startTime):
        nowTime = datetime.datetime.now() + datetime.timedelta(hours = int(timedelta_h), minutes = int(timedelta_m))
        start = startDate + " " + startTime + ":00.0"
        format = "%Y-%m-%d %H:%M:%S.%f"
        startTuple = time.strptime(start, format)
        nt = time.mktime(nowTime.timetuple())
        st = time.mktime(datetime.datetime(*startTuple[:7]).timetuple())
        alarmtime = int(float(st - nt) / 60)
        return alarmtime
        
    
    def loadFiles(self):
        if os.path.isdir(self.recdir):
            for fileName in os.listdir(self.recdir):
                pathFile = self.recdir + os.sep + fileName
                if pathFile.endswith('.json'):
                    raw = open(pathFile, 'r').read()
                    res = json.loads(raw)
                    alarmtime = self.GetAlarmTime(res['date'], res['start'])
                    if int(alarmtime) < 0:
                        os.remove(pathFile)
                    else:
                        xbmc.executebuiltin('CancelAlarm(' + str(res['name']) + ', silent)')
                        xbmc.executebuiltin('AlarmClock(' + str(res['name']) + ', "RunScript(' + str(self.cmddir) + str(os.sep) + 'record.py, ' + str(self.recdir) + str(os.sep) + str(res['name']) + '.json)", ' + str(alarmtime) + '))')


class WeebTV:
    def __init__(self):
        self.recdir = os.path.join(ptv.getAddonInfo('path'), "recs")
        self.strmdir = os.path.join(ptv.getAddonInfo('path'), "strm")
        
    def handleService(self):
        s = Settings()
        parser = Parser.Parser()
        params = parser.getParams()
        cid = parser.getIntParam(params, "cid")
        title = parser.getParam(params, "title")
        action = parser.getIntParam(params, "action")
        print "action: " + str(action) + ", title: " + str(title)
        if not os.path.isdir(self.strmdir):
            os.mkdir(self.strmdir)
        if not os.path.isdir(self.recdir):
            os.mkdir(self.recdir)
        if action == None:
			sortopt = 'online-alphabetical';
			if sortby == 'Now Viewed': sortopt = 'online-now-viewed';	
			elif sortby == 'Most Viewed': sortopt = 'online-most-viewed';				
			show = Channels()
			show.ChannelsList(apiUrl + "&option=" + sortopt)
        elif action == 1:
			s.setViewMode('other')
			if cid > 0 and title != "":
				init = Video()
				init.RunVideoLink(cid)
        elif action == 0:
			s.setViewMode('other')
			msg = xbmcgui.Dialog()
			msg.Warning(t(57005).encode('utf-8'), t(57006).encode('utf-8'), t(57007).encode('utf-8'), t(57008).encode('utf-8'))
            
    def handleRecords(self):
        d = xbmcgui.Dialog()
        rec = Record()
        qrec = d.yesno("Nagrywanie", "Czy odświeżyć nagrywanie wszystkich pozycji?")
        if qrec == 1:
            rec.loadFiles()
        
