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
import tmdb

class AlternativeTitles(SearchTermFilter):
    version = "0.102"
    identifier = "fr.torf.alternativetitles"
    addMediaTypeOptions = 'runFor'
    config_meta = {'plugin_desc': 'Gets alternative titles from http://www.themoviedb.org/.',
                  }

    _config = {'enabled': True } 

    _hidden_config = {'languages': [{'code':'DE', 'name':'Deutch'},
                                    {'code':'EN', 'name':'English'},
                                    {'code':'FR', 'name':'French'},
                                    {'code':'ES', 'name':'Spanish'}],
                        'tmdb_lang' : 'EN'}

    def __init__(self, instance='Default'):
        for language in self._hidden_config['languages']:
            self._config['title_language_' + language['code']] = False

        SearchTermFilter.__init__(self, instance=instance)
        tmdb.configure('5c235bb1b487932ebf0a9935c8b39b0a', self.hc.tmdb_lang)

    def compare(self, element, terms):
        if element.type != "Movie":
            log("i only work for Movies, i got a %s" % element.type)
            return terms

        tmdb_id = element.getIdentifier('tmdb')
        if not tmdb_id:
            log("no tmdb_id found for %s" % element)

            movies = tmdb.Movies(element.name, limit=True)
            for tmdb_movie in movies:
                movie = tmdb_movie
                break
        else:
            movie = tmdb.Movie(tmdb_id)

        if not movie:
            log("no movie found in themoviedb for %s" % element)
            return terms

        for alternative in movie.get_alternative_titles():
            if self._config['title_language_' + alternative['lang']]:
                terms.append(alternative['title'])

        return terms
