# Author: Torf
# URL: https://github.com/Torf/XDM-Rutorrent
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

from peewee import *
from xdm.plugins import *

import requests
from libs import RutorrentClient, bencode

import hashlib
import xmlrpclib
from xmlrpclib import Binary

class Rutorrent(Downloader):
    version = "0.124"
    identifier = "fr.torf.rutorrent"
    _config = { 'host': 'http://localhost/rutorrent',
                'username' : '',
                'comment_on_download': False,
                'password' : '' }
    _torrents = []
    types = ['de.lad1337.torrent']
    addMediaTypeOptions = 'runFor'

    def _getTorrentHash(self, download):
        headers = download.extra_data['headers'] if 'headers' in download.extra_data else { }
        response = requests.get(download.url, headers=headers)

        if response.status_code == 200:
            metainfo = bencode.bdecode(response.content)
            info = metainfo['info']
            return (True, Binary(response.content), hashlib.sha1(bencode.bencode(info)).hexdigest().upper())
        else:
            log.info("Download torrent file for rutorrent failed with url %s" % download.url)
            return (False, None, '')

    def addDownload(self, download):
        rutorrent = RutorrentClient.RutorrentClient(self.c.host, self.c.username, self.c.password)
        success, torrentContent, torrenthash = self._getTorrentHash(download)
        if not success:
            return False
        download.extra_data['hash'] = torrenthash

        if rutorrent.addNewTorrentData(torrentContent, True):
            log.info("Download sent to rutorrent as %s." % torrenthash)
            return True
        else:
            return False

    def _getTorrents(self):
        rutorrent = RutorrentClient.RutorrentClient(self.c.host, self.c.username, self.c.password)
        self._torrents = rutorrent.getTorrents()
        return self._torrents

    def _testConnection(self, host, username, password):
        try:
            rutorrent = RutorrentClient.RutorrentClient(host, username, password)
            log.info("Connected to rutorrent : rtorrent version %s." % rutorrent.getRtorrentVersion())
        except xmlrpclib.ProtocolError as error:
            return (False, {}, 'Connection failed (%s), check settings.' % error.errmsg)
        except Exception:
            return (False, {}, 'Connection failed (host unreachable), check settings.')
        return (True, {}, 'Connection Established!')
    _testConnection.args = ['host', 'username', 'password']

    def _findDownload(self, torrenthash):
        try:
            return Download.where_extra_data({'hash': torrenthash})
        except Download.DoesNotExist:
            pass
        return None

    def getDownloadPercentage(self, element):
        if not self._torrents:
            self._getTorrents()
        for item in self._torrents:
            download = self._findDownload(item['hash'])
            if download == None:
                continue

            if download.element.id != element.id:
                continue

            percentage = (float(item['downloaded']) / item['size']) * 100
            return percentage
        return 0

    def getElementStaus(self, element):
        download = Download()
        download.status = common.UNKNOWN
        if not self._torrents:
            self._getTorrents()
        for item in self._torrents:
            download = self._findDownload(item['hash'])
            if download == None:
                continue

            if download.element.id != element.id:
                continue

            if item['downloaded'] == item['size']:
                return (common.DOWNLOADED, download, item['storage'])
            elif item['downloaded'] < item['size']:
                return (common.DOWNLOADING, download, '')
            else:
                return (common.FAILED, download, '')
        return (common.UNKNOWN, download, '')

    config_meta = {'plugin_desc': 'Rutorrent downloader.',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}}
                   }
