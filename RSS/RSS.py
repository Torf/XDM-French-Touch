# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

# all xdm related plugin stuff you get with this line incl logger functions

# other libs should be imported as you need them but why dont you have a look at the libs xdm comes with
from xdm.plugins import *
import requests
import datetime

from xml.dom.minidom import parseString
from xml.dom.minidom import Node

from dateutil.parser import parse as parseDate
from babel.dates import format_datetime

from libs import bencode
import hashlib
import os
import os.path

def get_xml_text(node):
    text = ""
    for child_node in node.childNodes:
        if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
            text += child_node.data
    return text.strip()

def getTorrentHash(torrentPath):
        with open(torrentPath, 'rb') as f:
            metainfo = bencode.bdecode(f.read())
        info = metainfo['info']
        return hashlib.sha1(bencode.bencode(info)).hexdigest().upper()

def mergePath(*args):
    if len(args) <= 0:
        return ''

    result = args[0]
    for i in range(len(args) - 1):
        if not result.endswith('\\'):
            result += '\\'
        result += args[i+1]
    
    return result

def getRSSFeed(items):
    # XML Header
    rssContent  = '<?xml version="1.0" encoding="iso-8859-1"?>\r\n'
    rssContent += '<rss version="2.0">\r\n'
    rssContent += '\t<channel>\r\n'
    rssContent += '\t\t<title>XDM RSS Feed - AutoGet-It</title>\r\n'
    rssContent += '\t\t<link>http://xdm.lad1337.de</link>\r\n'
    rssContent += '\t\t<description>RSS feed generated by XDM to download.</description>\r\n'
    rssContent += '\t\t<lastBuildDate>%s</lastBuildDate>\r\n' % format_datetime(datetime.datetime.now(), 'E, d MMM yyyy HH:mm:ss', locale='en_US')
    rssContent += '\t\t<generator>XDM RSS downloader Plugin</generator>\r\n\r\n'

    # XML Content
    for item in items:
        rssContent += '\t\t<item>\r\n'
        rssContent += '\t\t\t<title>%s</title>\r\n' % item['title']
        rssContent += '\t\t\t<link>%s</link>\r\n' % item['link']
        rssContent += '\t\t\t<guid>%s</guid>\r\n' % item['guid']
        rssContent += '\t\t\t<pubDate>%s</pubDate>\r\n' % format_datetime(item['pubDate'], 'E, d MMM yyyy HH:mm:ss', locale='en_US')
        rssContent += '\t\t</item>\r\n'

    # XML Footer
    rssContent += '\t</channel>\r\n</rss>\r\n'
    return rssContent

def writeRssFeedToXML(feed, path):
    with open(path, 'wb') as f:
        f.write(feed)

class RSS(Downloader):
    version = "0.12"
    identifier = "fr.torf.rss"
    _config = { 'host' : 'http://localhost:8085/' }
    _torrents = []
    types = ['de.lad1337.torrent']
    addMediaTypeOptions = 'runFor'

    def addDownload(self, download):
        directory = mergePath(self.get_plugin_isntall_path()['path'], 'torrents\\')
        if not os.path.exists(directory):
            os.makedirs(directory)

        items = self._readRssFeed()
        newItem = self._getRssItem(download)

        now = datetime.datetime.now()
        maxAge = datetime.timedelta(days=7)

        resultItems = []
        if not newItem == None:
            resultItems.append(newItem)

        for item in items:
            if (now - item['pubDate']) < maxAge:
                resultItems.append(item)
            #else: 
            #   #remove old .torrents from folder.

        writeRssFeedToXML(getRSSFeed(resultItems), mergePath(self.get_plugin_isntall_path()['path'], 'rss.xml'))
        return True

    def _readRssFeed(self):
        filepath = mergePath(self.get_plugin_isntall_path()['path'], 'rss.xml')
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'rb') as f:
            xmldoc = parseString("\r\n".join(f.readlines()))

        itemlist = xmldoc.getElementsByTagName('item')
        items = []
        for item in itemlist:
            itemdate = parseDate(get_xml_text(item.getElementsByTagName('pubDate')[0])).replace(tzinfo=None)

            rssitem = {
                "title" : get_xml_text(item.getElementsByTagName('title')[0]),
                "link" :  get_xml_text(item.getElementsByTagName('link')[0]),
                "guid" : get_xml_text(item.getElementsByTagName('guid')[0]),
                "pubDate" :  itemdate }
            items.append(rssitem)
        return items

    def _getTorrentLink(self, torrentId):
        torrentLink = self.c.host
        if not ( torrentLink.startswith('http://') or torrentLink.startswith('https://') ):
            torrentLink = 'http://%s' % torrentLink
        if not torrentLink.endswith('/') :
            torrentLink = '%s/' % torrentLink

        torrentLink +='api/rest/%s/%s/torrent?tid=%08d' % (self.identifier, self.instance, torrentId)
        return torrentLink

    def _getRssItem(self, download):
        torrentId, torrentPath = self._downloadTorrent(download)
        if torrentPath == None:
            return None

        return {"title" : download.name,
                "link" :  self._getTorrentLink(torrentId),
                "guid" : getTorrentHash(mergePath(self.get_plugin_isntall_path()['path'], torrentPath)),
                "pubDate" :  datetime.datetime.now() }

    def _downloadTorrent(self, download):
        dstNum = 0
        dst = 'torrents\\%08d.torrent' % dstNum
        while os.path.exists(mergePath(self.get_plugin_isntall_path()['path'], dst)):
            dstNum += 1
            dst = 'torrents\\%08d.torrent' % dstNum

        headers = download.extra_data['headers'] if 'headers' in download.extra_data else { }
        r = requests.get(download.url, headers=headers)
        if r.status_code == 200:
            with open(mergePath(self.get_plugin_isntall_path()['path'], dst), 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
            return (dstNum, dst)
        else:
            return (0, None)

    def _rssFeed(self):
        filepath = mergePath(self.get_plugin_isntall_path()['path'], 'rss.xml')
        if not os.path.exists(filepath):
            return filepath

        result = ''
        with open(filepath, 'rb') as f:
            result = f.read()

        return result
    _rssFeed.rest = True

    def _torrent(self, tid):
        filepath = mergePath(self.get_plugin_isntall_path()['path'], 'torrents\\%08d.torrent' % tid)
        if not os.path.exists(filepath):
            return ''

        result = ''
        with open(filepath, 'rb') as f:
            result = f.read()

        return result
    _torrent.args = ['tid']
    _torrent.rest = True