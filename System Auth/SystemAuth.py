# Author: Torf
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

from xdm.plugins import System
from collections import OrderedDict
import cherrypy
import os.path

class SystemAuth(System):
    identifier = "fr.torf.systemauth"
    version = "0.4"
    _config = OrderedDict([
               ('login_user', '')
               ])

    _hidden_config = {'login_password': ''}

    def _saveNewPassword(self, pwdfirst, pwdsecond):
    	if not pwdfirst or not pwdsecond:
    		return (False, {'callFunction': 'systemauth_' + self.instance + '_addpwdchange', 'functionData': {}}, "You have to fill the two field.")

    	if pwdfirst != pwdsecond:
    		return (False, {'callFunction': 'systemauth_' + self.instance + '_addpwdchange', 'functionData': {}}, "Password and confirmation aren't identical.")

    	self.hc.login_password = pwdfirst
        cherrypy.server.restart()

    	return (True, {'callFunction': 'systemauth_' + self.instance + '_clear', 'functionData': {}}, "Password changed.")

    def _changePassword(self):
    	return (True, {}, "")

    def getConfigHtml(self):
        return """<script>
        		function systemauth_""" + self.instance + """_precrypt() {

        		}

        		function systemauth_""" + self.instance + """_clear() {
        			$('#block_""" + helper.idSafe(self.name) + """_pwdchange').remove();
        		}

                function systemauth_""" + self.instance + """_addpwdchange() {
                    $('#block_""" + helper.idSafe(self.name) + """_pwdchange').remove();

                    js = '<div id="block_""" + helper.idSafe(self.name) + """_pwdchange" class="control-group">';

                    js += '<div class="control-group"><label class="control-label" title="">login password</label>';
					js += '<div class="controls"><input data-belongsto="'+""" + helper.idSafe(self.name) + """+'" name="SystemAuth-""" + self.instance + """-pwdfirst" data-configname="pwdfirst" type="password" value="" onchange="" title="" data-original-title="">'
					js += '</div></div>';

                    js += '<div class="control-group"><label class="control-label" title="">confirm</label>';
					js += '<div class="controls"><input data-belongsto="'+""" + helper.idSafe(self.name) + """+'" name="SystemAuth-""" + self.instance + """-pwdsecond" data-configname="pwdsecond" type="password" value="" onchange="" title="" data-original-title="">'
					js += '</div></div>';

					js += '<div class="controls">'
					js += '<input type="button" class="btn" value="Save new password" onclick="systemauth_""" + self.instance + """_precrypt();pluginAjaxCall(this, \\\'SystemAuth\\\', \\\'""" + self.instance + """\\\', \\\'""" + helper.idSafe(self.name) + """_content\\\', \\\'_saveNewPassword\\\');" data-original-title="" title="" />';
                    js += '</div></div>';

                    $('#""" + helper.idSafe(self.name) + """_content .control-group').last().after(js);
                };
                </script>
        """

    def _SHA3JS(self):
        filepath = os.path.join(self.get_plugin_isntall_path()['path'], 'sha3.js')
        if not os.path.exists(filepath):
            return filepath

        result = ''
        with open(filepath, 'rb') as f:
            result = f.read()

        return result
    _SHA3JS.rest = True

    config_meta = { 'login_user': {'on_change_actions': ['serverReStart']},
			        'plugin_buttons': {'changePassword': {'action': _changePassword,
			                                                     'name': 'Change password',
			                                                     'desc': 'Change the login password'}
			                           }
			      }
