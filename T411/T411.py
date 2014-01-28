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
import requests
from xdm import helper

class T411(Indexer):
    version = "0.111"
    identifier = "fr.torf.t411"
    _config = {'username': '',
               'password':'',
               'enabled': True,
               'comment_on_download':False }

    types = ['de.lad1337.torrent']

    _apiToken = ''
    _baseUrl = 'https://api.t411.me'

    def _getUrl(self, path):
        return "%s%s" % (self._baseUrl, path)

    def _getApiToken(self, username=None, password=None):
        # if first request : get token
        if self._apiToken == '':
            if username and password:
                payload = {'username' : username,
                            'password' : password }
            else:
                payload = {'username' : self.c.username,
                           'password' : self.c.password }

            response = requests.post(self._getUrl('/auth'), data=payload)
            data = response.json()
            if 'error' in data:
                self._apiToken = ''
                return (False, data['error'])

            self._apiToken = data["token"]
        return (True, self._apiToken)

    def _getWebResponse(self, urlPath, params, username=None, password=None):
        token = self._getApiToken(username, password)
        # Handle token error
        if token[0] == False:
            return (False, token[1], '')
        # Request with token header
        headers = { 'Authorization' : token[1] }

        try:
            response = requests.get(self._getUrl(urlPath), params=params, headers=headers)
        except requests.exceptions.RequestException:
            log.error("Error during connection on $s" % self)
            return (False, 'Please check network !', '')

        # get json data
        data = response.json()
        # handle request error
        if 'error' in data:
            log.error("Error during request on $s" % self)
            return (False, 'Request error : %s' % data['error'], '')
        return (True, data, token[1])

    def searchForElement(self, element):
        category = str(self._getCategory(element))
        # category can be None
        if category is None:
            log.warning("No category found for %s" % element)
            return []
        # split into list and remove whitespace
        trackerCategories = [cat.strip() for cat in category.split(',')]
        
        downloads = []

        termList = [term.strip().replace(' ', '.') for term in element.getSearchTerms()]
        
        for term in termList:
            for trackerCategory in trackerCategories:
                self._searchInCategory(trackerCategory, term, element, downloads)

        if len(downloads) == 0:
            log.info("No search results for %s." % termList)
                    
        return downloads

    def _searchInCategory(self, category, terms, element, downloads):
        webResult = self._getWebResponse("/torrents/search/%s" % terms, { 'cid' : category })
        
        if webResult[0] == False:
            log.error(webResult[1])
            return

        log.info("T411 search for terms %s in category %s." % (terms, category))

        data = webResult[1]
        for item in data['torrents']:
            title = item['name']
            log.info("%s found on T411.me: %s" % (element.type, title))
            
            # Add the torrent with correct size and external id.
            d = Download()
            d.url = self._getUrlFromId(item['id'])
            d.name = title
            d.element = element
            d.size = int(item['size'])
            d.external_id = item['id']
            d.type = 'de.lad1337.torrent'
            d.extra_data['headers'] = { 'Authorization' : webResult[2] }
            d.extra_data['stats'] = { 'seeders' : item['seeders'],
                                         'leechers' : item['leechers'],
                                         'completed' : item['times_completed'] }
            downloads.append(d)

    def _getUrlFromId(self, torrentId):
        return self._getUrl('/torrents/download/%s' % torrentId)

    def _testConnection(self, username, password):
        webResult = self._getWebResponse('/users/profile/96660867', { }, username, password)
        
        if webResult[0] == False:
            return (False, {}, webResult[1])
        return (True, {}, 'Connection made!')
    _testConnection.args = ['username', 'password']

    def _gatherCategories(self, username, password):
        data = {}
        # Fill categories
        webResult = self._getWebResponse('/categories/tree', { }, username, password)

        if webResult[0] == False:
            return (False, {}, webResult[1])

        categories = [webResult[1][cat] for cat in webResult[1]]
        for cat in categories:
            if 'id' in cat:
                subcategories = [cat['cats'][subcat] for subcat in cat['cats']]
                for subcat in subcategories:
                    if "Film/Vid" in cat['name'] and subcat['name'] == "Film":
                        data['Movies'] = subcat['id']

                    elif cat['name'] == "Audio" and subcat['name'] == "Musique":
                        data['Music'] = subcat['id']

                    elif cat['name'] == "eBook" and subcat['name'] in "Bds Comics Livres Mangas Presse":
                        data['Books'] = subcat['id']

                    elif "Jeu vid" in cat['name']:
                        if subcat['name'] == "Windows":
                            data['PC'] = subcat['id']
                        elif subcat['name'] == "Nintendo":
                            data["Wii"] = subcat['id']
                            data["WiiU"] = subcat['id']
                        elif subcat['name'] == "Sony":
                            data["PS3"] = subcat['id']
                        elif subcat['name'] == "Microsoft":
                            data["Xbox360"] = subcat['id']

        data["Games"] = "%s,%s,%s,%s" % (data["PC"], data["Wii"], data["PS3"], data["Xbox360"]) 

        # Call the javascript function to fill fields.
        dataWrapper = {'callFunction': 
                            't411_' + self.instance + '_spreadCategories',
                       'functionData': 
                            data
                       }
        # Show a message to say its done.
        return (True, dataWrapper, '%s categories loaded' % len(data))
    _gatherCategories.args = ['username', 'password']

    def getConfigHtml(self):
        return """<script>
                function t411_""" + self.instance + """_spreadCategories(data){
                  console.log(data);
                  $.each(data, function(k,i){
                      $('#""" + helper.idSafe(self.name) + """ input[name$="'+k+'"]').val(i)
                  });
                };
                </script>
        """

    config_meta = {
        'plugin_desc': 'T411.me torrent indexer.',
        'plugin_buttons': 
            {'gather_gategories': 
                {'action': _gatherCategories, 'name': 'Get categories'},
            'test_connection': 
                {'action': _testConnection, 'name': 'Test connection'}}
          }
