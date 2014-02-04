import tvdb_api
import tvdb_exceptions

""" Encapsulates the tvdb api in order to get only but easier the alternative title
of a tv show, searching them by thetvdb id or original name.
"""
class thetvdb:
    _tvdb = None

    def __init__(self, apiKey=None):
        self._tvdb = tvdb_api.Tvdb(apikey=apiKey)

    """ Search for a show id using its name.
    """
    def getShowId(self, showName):
        showName = showName.strip()
        return int(self._tvdb[showName]['id'])

    """ Gets all alternative titles of a tv show.
    Returns a list of json object {'lang': <lang>, 'title': <alternativeTitle>}.
    """
    def getAlternativeTitles(self, searchInfo):
        if isinstance(searchInfo, (int, long)):
            result = []
            for lang in self._tvdb.config['valid_languages']:
                title = self.getAlternativeTitle(searchInfo, lang)
                if title is not None:
                    result.append(title)
            return result
        else:
            return self.getAlternativeTitles(self.getShowId(searchInfo))

    """ Get the alternative title of a tv show in a language. (using iso 2 characters language name)
    """
    def getAlternativeTitle(self, searchInfo, language):
        language = language.strip().lower()

        if isinstance(searchInfo, (int, long)):
            try:
                seriesInfoEt = self._tvdb._getetsrc(self._tvdb.config['url_seriesInfo'] % (searchInfo, language))
            except tvdb_exceptions.tvdb_error:
                return None

            for curInfo in seriesInfoEt.findall("Series")[0]:
                tag = curInfo.tag.lower()
                value = curInfo.text

                if value is not None:
                    if tag == "seriesname":
                        return { 'lang': language, 'title': self._tvdb._cleanData(value) }
            return None
        else:
            return self.getAlternativeTitle(self.getShowId(searchInfo), language)
