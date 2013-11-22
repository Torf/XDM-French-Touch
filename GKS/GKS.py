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
from xdm import helper
from xml.dom.minidom import parseString
from xml.dom.minidom import Node
import unicodedata
import re

def get_xml_text(node):
    text = ""
    for child_node in node.childNodes:
        if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
            text += child_node.data
    return text.strip()

def isValidItem(terms,  title):
    for term in terms.split('+'):
        if not (term in title):
            return False
    return True

def getTorrentExternalId(uploadLink):
    match = re.search(r'private-get/(\d+)/', uploadLink)
    if match:
        return match.group(1)
    else:
        log.error("Can't find the torrent id in %s" % uploadLink)
    return uploadLink

def getTorrentSize(description):
    match = re.search(r'Taille : (\d+\.\d+) ([TGMK])o', description)
    if match:
        size = float(match.group(1))
        if match.group(2) == "T":
            size = size * 1024 * 1024 * 1024
        elif match.group(2) == "G":
            size = size * 1024 * 1024
        elif match.group(2) == "M":
            size = size * 1024
        
        return int(size * 1024) #result in bytes
    else:
        log.error("Can't find the torrent size in %s" % description)
    return 0

class GKS(Indexer):
    version = "0.117"
    identifier = "fr.torf.gks"
    
    _config = {'authkey': '',
               'comment_on_download':False,
               'enabled': True }

    types = ['de.lad1337.torrent']

    def _baseUrlRss(self):
        return "https://gks.gs/rdirect.php"

    def searchForElement(self, element):      
        category = str(self._getCategory(element))
        # category can be None
        if category is None:
            log.warning("No category found for %s" % element)
            return []
        # split into list and remove whitespace
        trackerCategories = [cat.strip() for cat in category.split(',')]
        
        downloads = []
        termList = [term.strip().replace(' ', '+') for term in element.getSearchTerms()]
        
        for term in termList:
            for trackerCategory in trackerCategories:
                self._searchInCategory(trackerCategory, term, element, downloads)
                
        if len(downloads) == 0:
            log.info("No search results for %s." % terms)
                    
        return downloads

    def _searchInCategory(self, category, terms, element, downloads):
        payload = { 'ak' : self.c.authkey,
                        'type' : 'search',
                        'category': category, 
                        'q' : terms,
                        'order' : 'desc',
                        'sort' : 'normal' }
            
        webResult = self._getWebResponse(self._baseUrlRss(), payload)
        
        if webResult[0] == False:
            log.error(webResult[1])
            return


        parsedXML = parseString(webResult[1])
        
        channel = parsedXML.getElementsByTagName('channel')[0]
        items = channel.getElementsByTagName('item')
        
        log.info("Gks search for terms %s in category %s." % (terms, category))

        for item in items:
            title = get_xml_text(item.getElementsByTagName('title')[0])
            
            if title == "Aucun Resultat":
                return
            # Checks that the torrent title has as least the element name.
            if isValidItem(element.getName(), title):
                # Gets the rest of data in XML
                description = get_xml_text(item.getElementsByTagName('description')[0])
                url = get_xml_text(item.getElementsByTagName('link')[0])

                log.info("%s found on Gks.gs: %s" % (element.type, title))
                
                # Add the torrent with correct size and external id.
                d = Download()
                d.url = url
                d.name = title
                d.element = element
                d.size = getTorrentSize(description)
                d.external_id = getTorrentExternalId(url)
                d.type = 'de.lad1337.torrent'
                downloads.append(d)

    def _getWebResponse(self, url, params):
        try:
            rawResponse = requests.get(url, params=params, verify=False)
        except requests.exceptions.RequestException:
            log.error("Error during test connection on $s" % self)
            return (False, 'Please check network !')
        # Normalize and convert to ASCII
        rawResponse = unicodedata.normalize('NFKD', rawResponse.text)
        response = rawResponse.encode('ASCII', 'ignore')
        # Check if there is a authkey error.
        if response == "Bad Key":
            return (False, 'Wrong GKS.gs AuthKey !')
        return (True, response)

    def _testConnection(self, authkey):
        payload = { 'ak' : authkey }
        
        webResult = self._getWebResponse(self._baseUrlRss(), payload)

        if webResult[0] == False:
            return (False, {}, webResult[1])
        return (True, {}, 'Connection made!')
    _testConnection.args = ['authkey']
    
    def _gatherCategories(self):
        data = {}
        # 5:DVDRip/BDRip, 6:DVDRip/BDRip VOSTFR, 15:HD 720p, 
        # 16:HD 1080p, 17:Full BluRay, 19:DVDR, 21:Anime
        data["Movies"] = "5,6,15,16,17,19,21" 
        # 24:eBooks
        data["Books"] = "24"        
        # 29:PC Games, 30:Nintendo DS/3DS, 31:Wii, 
        # 32:Xbox 360, 34:PSP, 38:PS3
        data["Games"] = "29,30,31,32,34,38"
        # 29:PC Games
        data["PC"] = "29"
        # 38:PS3
        data["PS3"] = "38"
        # 31:Wii
        data["Wii"] = "31"
        # 31:Wii
        data["WiiU"] = "31"
        # 32:Xbox 360
        data["Xbox360"] = "32"
        # 39 : Flac
        data["Music"] = "39"
        # Call the javascript function to fill fields.
        dataWrapper = {'callFunction': 
                            'gks_' + self.instance + '_spreadCategories',
                       'functionData': 
                            data
                       }
        # Show a message to say its done.
        return (True, dataWrapper, '%s categories loaded' % len(data))
    _gatherCategories.args = []
    
    def getConfigHtml(self):
        return """<script>
                function gks_""" + self.instance + """_spreadCategories(data){
                  console.log(data);
                  $.each(data, function(k,i){
                      $('#""" + helper.idSafe(self.name) + """ input[name$="'+k+'"]').val(i)
                  });
                };
                </script>
        """
    
    config_meta = {
        'plugin_desc': 'Gks.gs torrent indexer.',
        'plugin_buttons': 
            {'gather_gategories': 
                {'action': _gatherCategories, 'name': 'Get categories'},
            'test_connection': 
                {'action': _testConnection, 'name': 'Test connection'}}
          }
