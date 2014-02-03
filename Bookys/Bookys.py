# Author: Torf
# URL: https://github.com/torf/XDM-Gks
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

from xdm.plugins import *
from lib import requests

from libs.bs4 import BeautifulSoup

from xdm import helper
import re
import urllib 
import unicodedata

class Bookys(Indexer):
    version = "0.101"
    identifier = "fr.torf.bookys"
    
    _config = {'authkey': '',
               'comment_on_download':False,
               'enabled': True,
               'username': '',
               'password' : '' }

    _hidden_config = { 'passkey' : '',
                      'userId' : '',
                      'cryptedPassword' : '' }

    config_meta = {
        'plugin_desc': 'Bookys.net torrent indexer.',
        'plugin_buttons': {'test_connection':    {'action': _testConnection, 'name': 'Test connection'}}
          }

    types = ['de.lad1337.torrent']


    def _baseUrl(self):
        return "https://bookys.net"

    def _linksUrl(self):
        return "%s/links.php" % self._baseUrl()

    def _searchUrl(self):
        return "%s/browse.php" % self._baseUrl()

    def _getTorrentUrl(self, torrentId):
        return "%s/downloads/%s/passkey.torrent/%s" % (self._baseUrl(), torrentId, self.hc.passkey)

    def _getTorrentSize(self, description):
        match = re.search(r'Taille: (\d+\.\d+) ([TGMKtgmk])o', description)
        if match:
            size = float(match.group(1))
            if match.group(2).upper() == "T":
                size = size * 1024 * 1024 * 1024
            elif match.group(2).upper() == "G":
                size = size * 1024 * 1024
            elif match.group(2).upper() == "M":
                size = size * 1024
            
            return int(size * 1024) #result in bytes
        else:
            log.info("Can't find the torrent size in %s" % {'text' : description})
        return 0

    def searchForElement(self, element):      
        downloads = []
        termList = [term.strip().replace('+', ' ') for term in element.getSearchTerms()]
        
        for term in termList:
                self._searchTerm(term, element, downloads)
                
        if len(downloads) == 0:
            log.info("No search results for %s." % terms)
                    
        return downloads

    def _searchTerm(self, terms, element, downloads):
        webResult = self._getWebResponse(self._searchUrl(), { 'search' : terms })

        if not webResult[0]:
            log.info("The search of '%s' with '%s' url failed (%s)." % (terms, response.url, webResult[1]))
            return downloads

        # Gets each result
        divs = webResult[1].find_all("div", {"class" : "browse-book-right"})
        
        # For each torrent result
        for div in divs:
            # Gets the right torrent description div
            descDiv = div.find("div", {"class" : "browse-book-button"})
            if not descDiv: continue

            # Get the second button link "Download".
            links = descDiv.find_all("a")
            if not len(links) == 2: continue
            href = links[1]['href']

            # Gets torrent name and ID from link
            match = re.search(r'downloads/(\d+)/(.+)\.torrent', href)
            if not match: continue

            torrentid = match.group(1)
            torrentName = match.group(2).replace('+', ' ')

            # Normalize and convert to ASCII the torrent name
            torrentName = unicodedata.normalize('NFKD', torrentName)
            torrentName = torrentName.encode('ascii', 'ignore')
            torrentName=urllib.unquote(torrentName)
            
            # Add the torrent with correct size and external id.
            d = Download()
            d.url = self._getTorrentUrl(torrentid)
            d.name = torrentName
            d.element = element
            d.size = self._getTorrentSize(div.getText())
            d.external_id = torrentid
            d.type = 'de.lad1337.torrent'
            downloads.append(d)

    def _getWebResponse(self, url, params, **kwargs):
        if "userId" in kwargs and "cryptedPassword" in kwargs:
            cookies = dict(tb_uid=kwargs['userId'], tb_pass=kwargs['cryptedPassword'])
        else:
            cookies = dict(tb_uid=self.hc.userId, tb_pass=self.hc.cryptedPassword)

        try:
            response = requests.get(url, params=params, cookies=cookies)
        except requests.exceptions.RequestException:
            log.error("Error during connection on $s" % self)
            return (False, 'Please check network !')

        if not response.status_code == requests.codes.ok:
            return (False, "Error %s !" % response.status_code)

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find('title')
        if not title: return (False, "Incomprehensible HTML !")

        if title.getText().lower() == "bookys :: connexion":
            return (False, "Wrong login or password !")

        return (True, soup)

    def _testConnection(self, userId, cryptedPassword):
        webResult = self._getWebResponse(self._searchUrl(), {}, userId=userId, cryptedPassword=cryptedPassword)

        if not webResult[0]:
            return (False, {}, "Connection failed ! (%s)" % webResult[1])

        return (True, {}, 'Connection made!')
    _testConnection.args = ['userId', 'cryptedPassword']
    
    def _gatherPasskey(self, userId, cryptedPassword):
        data = {}

        webResult = self._getWebResponse(self._linksUrl(), {}, userId=userId, cryptedPassword=cryptedPassword)

        if not webResult[0]:
            return (False, {}, 'Gather passkey failed ! (%s)' % webResult[1])

        liste = webResult[1].find("ul", {"class" : "list"})
        if liste:
            item = liste.find("li")
            if item:
                link = item.find("a")
                rssLink = link['href']
            else:
                return (False, {}, "Gather passkey failed ! (Parse error)")
        else:
            return (False, {}, "Gather passkey failed ! (Parse error)")
        
        match = re.search(r'&passkey=(\w+)', rssLink)
        if match:
            data["Passkey"] = match.group(1)
        else:
            return (False, {}, "Gather passkey failed ! (Parse link error)")

        # Call the javascript function to fill fields.
        dataWrapper = {'callFunction': 
                        'bookys_' + self.instance + '_spreadPasskey',
                        'functionData': 
                        data
                        }

        return (True, dataWrapper, 'Passkey loaded')
    _gatherPasskey.args = [ "userId", "cryptedPassword" ]
    
    def getConfigHtml(self):
        return """<script>
                function gks_""" + self.instance + """_spreadPasskey(data){
                  console.log(data);
                  $.each(data, function(k,i){
                      $('#""" + helper.idSafe(self.name) + """ input[name$="'+k+'"]').val(i)
                  });
                };

                    $('#""" + helper.idSafe(self.name) + """_content .control-group').last().after('<div class="control-group"><label class="control-label" title="">Captcha</label><div class="controls"><img src="https://s.gks.gs/img/img/11-2013/GD_Security_image.jpg" /><input data-belongsto="T411_Default" name="T411-Default-captcha" data-configname="captcha" type="text" value="" onchange="" title="" data-original-title="" /><input type="button" class="btn" value="Validate captcha" onclick="" data-original-title="" title="" /></div></div>');
                </script>

        """
    
    
