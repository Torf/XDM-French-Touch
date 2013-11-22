import xmlrpclib
from RequestsTransport import RequestsTransport

class RutorrentClient:
	_host = ''

	def __init__(self, host, username, password):
		self._host = host

		transport = RequestsTransport()
		transport.setCredentials(username, password)
		self._rutorrentServer = xmlrpclib.ServerProxy(self._rpcUrl(), verbose=False, transport=transport)

	def _baseUrl(self):
		if not self._host.startswith('http'):
			self._host = 'http://%s' % self._host
		if self._host.endswith('/'):
			return "%s" % self._host
		else:
			return "%s/" % self._host

	def _rpcUrl(self):
		return '%splugins/rpc/rpc.php' % self._baseUrl()

	def _parseTorrentResponse(self, response):
		return { 'hash' : response[0],
				 'stopped' : response[1] == '0',
				 'name' : response[2],
				 'size' : int(response[3]),
				 'downloaded' : int(response[4]),
				 'left' : int(response[5]),
				 'active' : response[6] != '0',
				 'storage' : response[7] }

	def getRtorrentVersion(self):
		return self._rutorrentServer.system.client_version()

	def getLibtorrentVersion(self):
		return self._rutorrentServer.system.library_version()

	def addNewTorrentLink(self, downloadLink, autoStart = False):
		if autoStart:
			result = self._rutorrentServer.load_start(downloadLink)
		else:
			result = self._rutorrentServer.load(downloadLink)
		return result == 0

	def addNewTorrentData(self, torrentContent, autoStart = False):
		if autoStart:
			result = self._rutorrentServer.load_raw_start(torrentContent)
		else:
			result = self._rutorrentServer.load_raw(torrentContent)
		return result == 0

	def getTorrent(self, torrentHash):
		multicall = xmlrpclib.MultiCall(self._rutorrentServer)

		multicall.d.get_hash(torrentHash) 		# torrent hash
		multicall.d.get_state(torrentHash)		# torrent state 0:stopped, 1:started
		multicall.d.get_name(torrentHash)		# torrent name
		multicall.d.get_size_bytes(torrentHash)	# torrent size in bytes
		multicall.d.get_bytes_done(torrentHash)	# already dowloaded size in bytes
		multicall.d.get_left_bytes(torrentHash)	# rest to download size in bytes
		multicall.d.is_active(torrentHash)		# if torrent is active of not (downloading/seeding). 1: active, 0 not active
		multicall.d.get_base_path(torrentHash)	# path on the hdd of the downloaded content

		response = multicall()
		return self._parseTorrentResponse(response)
	
	def getTorrents(self):
		multicall = xmlrpclib.MultiCall(self._rutorrentServer)

		multicall.d.multicall("main", # view
			"d.get_hash=", # torrent hash
			"d.get_state=", # torrent state 0:stopped, 1:started
			"d.get_name=", # torrent name
			"d.get_size_bytes=", # torrent size in bytes
			"d.get_bytes_done=", # already dowloaded size in bytes
			"d.get_left_bytes=", # rest to download size in bytes
			"d.is_active=", # if torrent is active of not (downloading/seeding). 1: active, 0 not active
			"d.get_base_path=") # path on the hdd of the downloaded content

		response = multicall()
		return [self._parseTorrentResponse(x) for x in response[0]]

