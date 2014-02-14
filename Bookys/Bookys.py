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
import BeautifulSoup

from xdm.plugins import *
from xdm import helper

import requests
import re
import urllib 
import unicodedata
import os.path
import pickle
import base64

class Bookys(Indexer):
    version = "0.102"
    identifier = "fr.torf.bookys"
    
    _config = {'authkey': '',
               'comment_on_download':False,
               'enabled': True,
               'username': '',
               'password' : '' }

    _hidden_config = { 'passkey' : '',
                      'userId' : '',
                      'cryptedPassword' : '' }

    _currentSessionId = None
    _generatedCaptchaId = None

    addMediaTypeOptions = ['de.lad1337.books']
    types = ['de.lad1337.torrent']

    def _baseUrl(self):
        return "https://bookys.net"

    def _loginUrl(self):
        return "%s/login.php" % self._baseUrl()        

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
            log.info("No search results for %s." % termList)
        
        return downloads

    def _searchTerm(self, terms, element, downloads):
        webResult = self._getWebResponse(self._searchUrl(), { 'search' : terms })

        if not webResult[0]:
            log.info("The search of '%s' with '%s' url failed (%s)." % (terms, self._searchUrl(), webResult[1]))
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
            torrentName = urllib.unquote(torrentName)
            
            # Add the torrent with correct size and external id.
            d = Download()
            d.url = self._getTorrentUrl(torrentid)
            d.name = torrentName
            d.element = element
            d.size = self._getTorrentSize(div.getText())
            d.external_id = torrentid
            d.type = 'de.lad1337.torrent'
            downloads.append(d)

    def _getWebResponse(self, url, params, cookies):
        try:
            response = requests.get(url, params=params, verify=False, cookies=cookies)
        except requests.exceptions.RequestException:
            log.error("Error during connection on %s" % self)
            return (False, 'Please check network !')

        if not response.status_code == requests.codes.ok:
            return (False, "Error %s !" % response.status_code)

        print { 'response':response.text }

        return (True, response.text)
    
    def _generateCaptcha(self):
        session = requests.Session()

        # get new session
        session.post("https://bookys.net/captcha/newsession.php", verify=False)

        # get image url
        response = session.post("https://bookys.net/captcha/image_req.php", verify=False)
        # regex extract from src="captcha/GD_Security_image.php?1391434819"
        match = re.search(r'src="captcha/GD_Security_image.php\?(\d+)"', response.text)
        if not match:
            return (False, {}, "Can't generate captcha.")

        self._generatedCaptchaId = str(match.group(1))

        # get image binary and write image file.
        imgResponse = session.get('https://bookys.net/captcha/GD_Security_image.php?'+self._generatedCaptchaId, verify=False)
        imgContent = imgResponse.content

        with open(os.path.join(self.get_plugin_isntall_path()['path'],'captcha_%s.png' % self._generatedCaptchaId), 'wb') as f:
            f.write(imgContent)

        # call js callback to show captcha image and form.
        return (True, {'callFunction': 'bookys_' + self.instance + '_addcaptcha',
                       'functionData': { 'session' :  base64.b64encode(pickle.dumps(session)), 'id' : self._generatedCaptchaId } }
                     , 'Captcha generated.')

    def _validateCaptcha(self, username, password, sessionid, captcha):
        session = pickle.loads(base64.b64decode(sessionid))

        process = session.get('https://bookys.net/captcha/process.php?captcha='+captcha, verify=False, timeout=30)
        if process.text != "1":
            return (False, {}, "Bad captcha, try again.") # todo: js callback to get new captcha

        payload = { 'username':username, 'password':password, 'captcha':captcha }

        response = session.post('https://bookys.net/takelogin.php', verify=False, data=payload)

        if "<title>Bookys :: Home</title>" in response.text:
            if 'tb_uid' in session.cookies and 'tb_pass' in session.cookies:
                return self._gatherPasskey(session.cookies['tb_uid'], session.cookies['tb_pass'])
        
        return (False, {}, "Bad login or password !")
    _validateCaptcha.args = ['username', 'password', 'sessionid', 'captcha']

    def _gatherPasskey(self, userId, cryptedPassword):
        data = {}

        webResult = self._getWebResponse(self._linksUrl(), {}, dict(tb_uid=userId, tb_pass=cryptedPassword))

        if not webResult[0]:
            return (False, {}, 'Gather passkey failed ! (%s)' % webResult[1]) # todo: js callback to get new captcha

        soup = BeautifulSoup.BeautifulSoup(webResult[1], "html.parser")
        liste = soup.find("ul", {"class" : "list"})
        if liste:
            item = liste.find("li")
            if item:
                link = item.find("a")
                rssLink = link['href']
            else:
                return (False, {}, "Gather passkey failed ! (Parse error)") # todo: js callback to get new captcha
        else:
            return (False, {}, "Gather passkey failed ! (Parse error)") # todo: js callback to get new captcha
        
        match = re.search(r'&passkey=(\w+)', rssLink)
        if match:
            passkey = match.group(1)
        else:
            return (False, {}, "Gather passkey failed ! (Parse link error)") # todo: js callback to get new captcha

        self.hc.passkey = passkey
        self.hc.userId = useId
        self.hc.cryptedPassword = cryptedPassword

        return (True, {}, 'Passkey loaded.') # Todo: remove captcha.

    def getConfigHtml(self):
        return """<script>
                function bookys_""" + self.instance + """_spreadFields(data){
                  console.log(data);
                  $.each(data, function(k,i){
                      $('#""" + helper.idSafe(self.name) + """ input[name$="'+k+'"]').val(i)
                  });
                };

                function bookys_""" + self.instance + """_addcaptcha(data) {
                    console.log(data);
                    sessiondump = data['session'];
                    captchaid = data['id'];
                    $('#block_""" + helper.idSafe(self.name) + """_captcha').remove();

                    js = '<div id="block_""" + helper.idSafe(self.name) + """_captcha" class="control-group">';
                    js += '<label class="control-label" title="">Captcha</label>';
                    js += '<div class="controls">';
                    js += '<img src="/api/rest""" + ('/%s/%s/' % (self.identifier, self.instance)) +  """captchaimage?cid='+captchaid+'" alt="'+captchaid+'" />';
                    js += '<input data-belongsto="'+""" + helper.idSafe(self.name) + """+'" name="Bookys-""" + self.instance + """-sessionid" data-configname="sessionid" type="text" value="'+sessiondump+'" onchange="" title="" data-original-title="" style="height:0px;visibility:collapse;float:right;" />';
                    js += '<input data-belongsto="'+""" + helper.idSafe(self.name) + """+'" name="Bookys-""" + self.instance + """-captcha" data-configname="captcha" type="text" value="" onchange="" title="" data-original-title="" />';
                    js += '<input type="button" class="btn" value="Validate captcha" onclick="pluginAjaxCall(this, \\\'Bookys\\\', \\\'""" + self.instance + """\\\', \\\'""" + helper.idSafe(self.name) + """_content\\\', \\\'_validateCaptcha\\\')" data-original-title="" title="" />';
                    js += '</div></div>';

                    $('#""" + helper.idSafe(self.name) + """_content .control-group').last().after(js);
                };
                </script>
        """
    
    
    config_meta = {
        'plugin_desc': 'Bookys.net torrent indexer.',
        'plugin_buttons': {'generate_captcha' : {'action': _generateCaptcha, 'name': 'Generate Captcha'}}
          }

    def _captchaimage(self, cid):
        filepath = os.path.join(self.get_plugin_isntall_path()['path'], 'captcha_%s.png' % cid)
        if not os.path.exists(filepath):
            return None

        result = ''
        with open(filepath, 'rb') as f:
            result = f.read()

        return result
    _captchaimage.args = ['cid']
    _captchaimage.rest = True
