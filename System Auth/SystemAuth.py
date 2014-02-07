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
from xdm import helper
import cherrypy
import os.path
import hashlib
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader, DictLoader

class SystemAuth(System):
    identifier = "fr.torf.systemauth"
    version = "0.84"
    _config = OrderedDict([
               ('login_user', '')
               ])

    _hidden_config = {'login_password': ''}

    def _saveNewPassword(self, pwdfirst, pwdsecond):
        if not pwdfirst or not pwdsecond:
            return (False, {'callFunction': 'systemauth_' + self.instance + '_addpwdchange', 'functionData': {}}, "You have to fill the two field.")

        if pwdfirst != pwdsecond:
            return (False, {'callFunction': 'systemauth_' + self.instance + '_addpwdchange', 'functionData': {}}, "Password and confirmation aren't identical.")

        newpwd = hashlib.sha512(str(pwdfirst)).hexdigest()

        self.hc.login_password = newpwd
        
        cherrypy.server.restart()

        return (True, {'callFunction': 'systemauth_' + self.instance + '_clear', 'functionData': {}}, "Password changed.")
    _saveNewPassword.args = ['pwdfirst','pwdsecond']

    def _changePassword(self):
        return (True, {'callFunction': 'systemauth_' + self.instance + '_addpwdchange', 'functionData': {}}, "")
    _changePassword.args = []

    def getConfigHtml(self):
        filepath = os.path.join(self.get_plugin_isntall_path()['path'], 'config.ji2')
        with open(filepath, "r") as f:
            tpl = f.read()
        env = Environment(loader=DictLoader({'this': tpl}), extensions=['jinja2.ext.i18n'])
        elementTemplate = env.get_template('this')
        return elementTemplate.render(plugin_instance=self.instance, plugin_identifier=self.identifier)

    def _libsha(self):
        filepath = os.path.join(self.get_plugin_isntall_path()['path'], 'sha512.js')
        with open(filepath, 'r') as f:
            result = f.read()
        return result
    _libsha.rest = True

    config_meta = { 'login_user': {'on_change_actions': ['serverReStart']},
                    'plugin_buttons': {'changePassword': {'action': _changePassword,
                                                                 'name': 'Change password',
                                                                 'desc': 'Change the login password'}
                                       },
                    'plugin_desc': 'Authentification account system. (It handles access to XDM, be careful)'
                  }
