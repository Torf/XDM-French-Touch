# Author: Torf
# URL: https://github.com/Torf/XDM-Transmission
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

from xdm.plugins import *
from lib import requests
from libs.TransmissionClient import TransmissionClient

class Transmission(Downloader):
    version = "0.105"
    identifier = "fr.torf.transmission"
    _config = { 'host': 'http://localhost:9091/',
                'username' : '',
                'comment_on_download': False,
                'password' : '' }
    _torrents = []
    types = ['de.lad1337.torrent']
    addMediaTypeOptions = 'runFor'
    _client = None

    def addDownload(self, download):
        if not self._client:
            self._client = TransmissionClient(self.c.host, self.c.username, self.c.password)

        # if headers, have to download then transmit content.
        if 'headers' in download.extra_data:
            headers = download.extra_data['headers'] if 'headers' in download.extra_data else { }
            response = requests.get(download.url, headers=headers)
            if response.status_code == 200:
                result = self._client.addNewTorrentData(response.content, True)
            else:
                log.info("Download torrent file for transmission failed with url %s" % download.url)
                return False
        else:
            result = self._client.addNewTorrentLink(download.url, True)

        if result['success']:
            download.extra_data['hash'] = result['hash']
            log.info("Download sent to rutorrent as %s." % result['hash'])
            return True
        else:
            return False

    def _testConnection(self, host, username, password):
        try:
            client = TransmissionClient(host, username, password)
            log.info("Connected to transmission.")
        except Exception as e:
            return (False, {}, 'Connection failed (%s), check settings.' % e)
        return (True, {}, 'Connection Established!')
    _testConnection.args = ['host', 'username', 'password']

    def _findDownload(self, torrenthash):
        try:
            return Download.where_extra_data({'hash': torrenthash})
        except Download.DoesNotExist:
            pass
        return None

    def getDownloadPercentage(self, element):
        if not self._client:
            self._client = TransmissionClient(self.c.host, self.c.username, self.c.password)
        if not self._torrents:
            self._torrents = self._client.getTorrents()['torrents']
        for item in self._torrents:
            download = self._findDownload(item['hash'])
            if download == None:
                continue

            if download.element.id != element.id:
                continue

            percentage = item['percentDone'] * 100
            return percentage
        return 0

    def getElementStaus(self, element):
        if not self._client:
            self._client = TransmissionClient(self.c.host, self.c.username, self.c.password)

        download = Download()
        download.status = common.UNKNOWN
        if not self._torrents:
            self._torrents = self._client.getTorrents()['torrents']
        for item in self._torrents:
            download = self._findDownload(item['hash'])
            if download == None:
                continue

            if download.element.id != element.id:
                continue

            if item['leftUntilDone'] == 0:
                return (common.DOWNLOADED, download, item['storage'])
            elif item['leftUntilDone'] > 0:
                return (common.DOWNLOADING, download, '')
            else:
                return (common.FAILED, download, '')
        return (common.UNKNOWN, download, '')

    config_meta = {'plugin_desc': 'Transmission downloader.',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}}
                   }
