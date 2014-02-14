# -*- coding: utf-8 -*-
# Author: Torf
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
from xdm.helper import replace_x

class Diacritics(SearchTermFilter):
    version = "0.1"
    identifier = "fr.torf.diacritics"
    addMediaTypeOptions = 'runFor'
    _config = {}
    config_meta = {'plugin_desc': u'For each search term generate another one where é is replaced with e and so forth.'}

    _map = {u'é': u'e', u'É': u'E',
		    u'è': u'e', u'È': u'E',
		    u'ê': u'e', u'Ê': u'E',
		    u'ë': u'e', u'Ë': u'E',
		    u'à': u'a', u'À': u'A',
		    u'â': u'a', u'Â': u'A',
		    u'ä': u'a', u'Ä': u'A',
		    u'ç': u'c',
		    u'ù': u'u', u'Ù': u'U',
		    u'û': u'u', u'Û': u'U',
		    u'ü': u'u', u'Ü': u'U',
		    u'ô': u'o', u'Ô': u'O',
		    u'ö': u'o', u'Ö': u'O'}

    def compare(self, element, terms):
        log('Fixing diacritics for %s and %s' % (element, terms))
        out = list(terms)
        for t in terms:
            out.append(replace_x(t, self._map))
        return out
