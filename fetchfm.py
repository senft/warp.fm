#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import defaultdict
from datetime import datetime as datetime
import time
import random
from operator import itemgetter
import urllib
import urllib2
try:
    import json
except ImportError:
    import simplejson as json

import config


NUM_RANDOM_TRACKS = 10
NUM_TOP_TRACKS = 10
NUM_TOP_ARTISTS = 5
NUM_TOP_ALBUMS = 5


class FetchFM:
    def __init__(self):
        self.API_URL = config.API_URL
        self.API_KEY = config.API_KEY
        self.start, self.end = self._get_timestamps()

    def _get_timestamps(self):
        """ Takes the current date, substracts one year and returns two
        timestamps for that day (00:00 and 23:59) """
        today = datetime.utcnow()

        # TODO: This needs to be checked.. is the date correct?
        date_start = datetime(today.year - 1, today.month, today.day, 0, 0, 0)
        date_end = datetime(today.year - 1, today.month, today.day, 23, 59, 0)

        ts_start = int(time.mktime(date_start.timetuple()))
        ts_end = int(time.mktime(date_end.timetuple()))

        return (ts_start, ts_end)

    def _get_formated_day(self):
        # TODO: output nicer (localized) date
        date = datetime.fromtimestamp(self.start)
        return date.strftime('%A, %d.  %B %Y')
        #return date.strftime('%x')

    def get_userinfo(self, username):
        result = None
        query = {'method': 'user.getInfo',
                 'user': username,
                 'api_key': self.API_KEY,
                 'format': 'json'}

        try:
            #Create an API Request
            url = self.API_URL + "?" + urllib.urlencode(query)

            #Send Request and Collect it
            data = urllib2.urlopen(url)
            result = json.load(data)

            #Close connection
            data.close()
        except urllib2.HTTPError, e:
            print "HTTP error: %d" % e.code
        except urllib2.URLError, e:
            print "Network error: %s" % e.reason.args[1]

        return result['user']

    def get_tracks(self, username):
        result = {}

        # TODO This doesn't get all tracks if the user listened 200+ track that
        # day
        query = {'method': 'user.getRecentTracks',
                 'user': username,
                 'from': self.start,
                 'to': self.end,
                 'api_key': self.API_KEY,
                 'limit': 200,
                 'format': 'json'}

        try:
            #Create an API Request
            url = self.API_URL + "?" + urllib.urlencode(query)

            #Send Request and Collect it
            data = urllib2.urlopen(url)

            #Print it
            response_data = json.load(data)

            result = self._parse_response(response_data)

            #Close connection
            data.close()
        except urllib2.HTTPError, e:
            print "HTTP error: %d" % e.code
        except urllib2.URLError, e:
            print "Network error: %s" % e.reason.args[1]

        return result

    def _parse_response(self, data):
        result = {}
        try:
            tracks = data['recenttracks']['track']
            result['tracks'] = []

            result['date'] = self._get_formated_day()

            for track in tracks:

                if '@attr' in track:
                    if 'nowplaying' in track['@attr']:
                        if track['@attr']['nowplaying'] == 'true':
                            # user.getRecentTracks includes the song currently
                            # playing (if there is one) (even if it is > "to").
                            #print 'Skipped currently playing track: ', track
                            continue

                timestamp = float(track['date']['uts'])
                time = datetime.fromtimestamp(timestamp).strftime('%H:%M')
                streamable = track['streamable'] == '1'

                result['tracks'].append(
                    {'artist': {'name' : track['artist']['#text']},
                     'track': {'title': track['name'],
                               'album': track['album']['#text'],
                               'url': track['url'],
                               'streamable': streamable,
                               'time': time,
                               'img_small': track['image'][0]['#text']}})

            result['random_tracks'] = self._get_random_tracks(result['tracks'])
            result['top_tracks'] = self._parse_top_tracks(result['tracks'])
            result['top_artists'] = self._parse_top_artists(result['tracks'])
            result['top_albums'] = self._parse_top_albums(result['tracks'])

        except KeyError, e:
            print 'Error fetching data:', e

        return result

    def _get_random_tracks(self, tracks):
        # If we have 10+ tracks pick 10 random ones, else pick all
        if len(tracks) <= NUM_RANDOM_TRACKS:
            rtracks = tracks
        else:
            rtracks = random.sample(tracks, NUM_RANDOM_TRACKS)
        rtracks = sorted(rtracks, key=lambda x: x['track']['time'])
        return rtracks

    def _parse_top_tracks(self, tracks):
        # TODO This results in a:
        # <a href={{ track.track.track.url }}>{{ track.track.track.title }}</a>
        # in the template...
        count = {}
        for track in tracks:
            title = ''.join([track['artist']['name'], ' - ',
                                   track['track']['title']])
            if title in count:
                count[title]['count'] += 1
            else:
                count[title] = {'count': 1, 'track': track}

        result = sorted(count.itervalues(), key=itemgetter('count'),
                        reverse=True)

        return result[:NUM_TOP_TRACKS]

    def _parse_top_artists(self, tracks):
        d = defaultdict(int)
        for track in tracks:
            name = track['artist']['name']
            if name:
                d[name] += 1
        result = sorted(d.iteritems(), key=itemgetter(1), reverse=True)
        return result[:NUM_TOP_ARTISTS]

    def _parse_top_albums(self, tracks):
        d = defaultdict(int)
        for track in tracks:
            album = track['track']['album'].strip()
            if album:
                d[album] += 1
        result = sorted(d.iteritems(), key=itemgetter(1), reverse=True)
        return result[:NUM_TOP_ALBUMS]
