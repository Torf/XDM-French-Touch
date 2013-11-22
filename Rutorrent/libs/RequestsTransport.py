from lib import requests
from lib.requests import auth

import xmlrpclib
import unicodedata

class RequestsTransport(xmlrpclib.Transport):
	# override this if you'd like to https
	use_https = False

	_username = ''
	_password = ''

	def setCredentials(self, username, password):
		self._username = username
		self._password = password

	def request(self, host, handler, request_body, verbose):
		"""
		Make an xmlrpc request.
		"""
		url = self._build_url(host, handler)
		try:
			resp = requests.post(url, data=request_body, timeout=30, auth=auth.HTTPDigestAuth(self._username, self._password))
		except ValueError:
			raise
		except Exception:
			raise # something went wrong
		else:
			try:
				resp.raise_for_status()
			except requests.RequestException as e:
				raise xmlrpclib.ProtocolError(url, resp.status_code, str(e), resp.headers)
			else:
				return self.parse_response(resp, verbose)

	def parse_response(self, resp, verbose):
		"""
		Parse the xmlrpc response.
		"""
		p, u = self.getparser()

		# Normalize and convert to ASCII (removes diacritics)
		response = unicodedata.normalize('NFKD', resp.text)
		response = response.encode('ASCII', 'ignore')

		if verbose:
			print response

		p.feed(response)
		p.close()
		return u.close()

	def _build_url(self, host, handler):
		url = 'https://' if self.use_https else 'http://'
		url += host + handler
		return url