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
import json
import re
from base64 import b64encode

class TransmissionClient:
	_host = ''

	def __init__(self, host, username, password):
		self._host = host
		self._session = requests.session()
		self._session.auth = (username, password)
		self._auth = self._getAuth()

	def _baseUrl(self):
		if not self._host.startswith(u'http'):
			self._host = u'http://%s' % self._host
		if self._host.endswith(u'/'):
			return u"%s" % self._host
		else:
			return u"%s/" % self._host

	def _rpcUrl(self):
		return u'%stransmission/rpc' % self._baseUrl()

	def _prettyPrint(self, jsonData):
		print json.dumps(jsonData, sort_keys=True, indent=4, separators=(',', ': '))

	def _rpcRequest(self, method, arguments = {}, returnsCode = False):
		post_data = json.dumps({'arguments': arguments,
								'method': method,
								})
		response = self._session.post(self._rpcUrl(), data=post_data)
		if returnsCode:
			return (response.status_code, json.loads(response.text))
		else:
			return json.loads(response.text)

	def _getAuth(self):
		post_data = json.dumps({u'method': u'session-get',})
		
		try:
			response = self._session.post(self._rpcUrl(), data=post_data.decode('utf-8'), timeout=60)
			auth = re.search(u'X-Transmission-Session-Id:\s*(\w+)', response.text).group(1)
		except:
			raise Exception(u'Host unreachable')
			return None


		self._session.headers.update({u'x-transmission-session-id': auth})

		#validating Transmission auth
		response = self._rpcRequest('session-get', returnsCode=True)
		if response[0] == 401:
			raise Exception(u'Invalid username or password')
		else:
			jsonresponse = response[1]
			#print json.dumps(jsonresponse, sort_keys=True, indent=4, separators=(',', ': '))
			if 'result' in jsonresponse and jsonresponse['result'] == 'success':
				return auth
			else:
				raise Exception(u'RPC method error')
				return None

	def addNewTorrentLink(self, downloadLink, autostart = False):
		arguments = { 'filename': downloadLink,
					'paused': 1 if not autostart else 0
					}
		response = self._rpcRequest('torrent-add', arguments=arguments)
		success = response['result'] == "success"
		torrentInfos = response['arguments']['torrent-added'] if success else {'hashString' : '', 'id' : 0}

		return {'success' : success, 'hash' : torrentInfos['hashString'], 'id' : torrentInfos['id']}

	def addNewTorrentData(self, torrentContent, autostart = False):
		arguments = { 'metainfo': b64encode(torrentContent),
						'paused': 1 if not autostart else 0
						}
		response = self._rpcRequest('torrent-add', arguments=arguments)
		success = response['result'] == "success"
		torrentInfos = response['arguments']['torrent-added'] if success else {'hashString' : '', 'id' : 0}
		
		return {'success' : success, 'hash' : torrentInfos['hashString'], 'id' : torrentInfos['id']}

	def getTorrent(self, torrentId):
		arguments = { 'fields': ['id', 'hashString', 'name', 'totalSize', 'percentDone', 'leftUntilDone', 'downloadDir'],
					'ids': [torrentId]
					}
		response = self._rpcRequest('torrent-get', arguments=arguments)
		success = response['result'] = 'success'
		torrentInfo = response['arguments']['torrents'][0]
		return {'success' : success, 'torrent' : torrentInfo}

	def getTorrents(self):
		arguments = { 'fields': ['id', 'hashString', 'name', 'totalSize', 'percentDone', 'leftUntilDone', 'downloadDir']}
		response = self._rpcRequest('torrent-get', arguments=arguments)
		success = response['result'] = 'success'
		torrentsInfo = response['arguments']['torrents']
		return {'success' : success, 'torrents' : torrentsInfo}