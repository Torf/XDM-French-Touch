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
from dependencies.thetvdb import thetvdb
from dependencies.tmdb import tmdb

class AlternativeTitles(SearchTermFilter):
    version = "0.12"
    identifier = "fr.torf.alternativetitles"
    addMediaTypeOptions = 'runFor'
    config_meta = {'plugin_desc': 'Gets alternative titles from http://www.themoviedb.org/ and http://thetvdb.com/.' }

    _config = {'enabled': True,
               'title_language_de' : False,
               'title_language_en' : False,
               'title_language_fr' : False,
               'title_language_es' : False } 

    _thetvdb = None

    def __init__(self, instance='Default'):
        SearchTermFilter.__init__(self, instance=instance)
        tmdb.configure('5c235bb1b487932ebf0a9935c8b39b0a', 'EN')
        self._thetvdb = thetvdb.thetvdb()

    def compare(self, element, terms):
        if element.type == "Movie":
            return self._compare_movies(element, terms)
        elif element.type == "Show":
            return self._compare_shows(element, terms)
        else:
            log.info("i only work for Movies and Shows, i got a %s" % element.type)
            return terms

    def _compare_movies(self, element, terms):
        tmdb_id = element.getIdentifier('tmdb')
        if not tmdb_id:
            log.info("no tmdb_id found for %s" % element)

            movies = tmdb.Movies(element.name, limit=True)
            for tmdb_movie in movies:
                movie = tmdb_movie
                break
        else:
            movie = tmdb.Movie(tmdb_id)

        if not movie:
            log.info("no movie found in themoviedb for %s" % element)
            return terms

        alts = movie.get_alternative_titles()

        for alternative in alts:
            langconfig = self.c.getConfig("title_language_%s" % alternative['lang'].lower())
            if langconfig:
                if langconfig.value:
                    terms.append(alternative['title'])

        return terms

    def _compare_shows(self, element, terms):
        tvdb_id = element.getIdentifier('tvdb')

        if tvdb_id is not None:
            alternatives = self._thetvdb.getAlternativeTitles(tvdb_id)
        else:
            log.info("no tvdb_id found for %s" % element)
            alternatives = self._thetvdb.getAlternativeTitles(element.name)
        
        if alternatives is None:
            log.info("no show found in thetvdb for %s" % element)
            return terms

        for alternative in alternatives:
            langconfig = self.c.getConfig("title_language_%s" % alternative['lang'].lower())
            if langconfig:
                if langconfig.value:
                    terms.append(alternative['title'])

        return terms