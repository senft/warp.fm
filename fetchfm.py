#!/usr/bin/env python2
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

    def get_userinfo(self, username):
        result = None
        query = {'method': 'user.getInfo',
                 'user': username,
                 'api_key': self.API_KEY,
                 'format': 'json'}

        #print 'Query: ', query

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
        start, end = self._get_timestamps()

        # TODO This doesn't get all tracks if the user listened 200+ track that
        # day
        query = {'method': 'user.getRecentTracks',
                 'user': username,
                 'from': start,
                 'to': end,
                 'api_key': self.API_KEY,
                 'limit': 200,
                 'format': 'json'}

        #print 'Query: ', query

        try:
            #Create an API Request
            url = self.API_URL + "?" + urllib.urlencode(query)

            #Send Request and Collect it
            data = urllib2.urlopen(url)

            #Print it
            response_data = json.load(data)

            result = self._parse_response(response_data, start)

            #Close connection
            data.close()
        except urllib2.HTTPError, e:
            print "HTTP error: %d" % e.code
        except urllib2.URLError, e:
            print "Network error: %s" % e.reason.args[1]

        return result

    def _parse_response(self, data, date):
        result = {}
        try:
            tracks = data['recenttracks']['track']
            result['tracks'] = []

            # TODO: output nicer date
            dt_date = datetime.fromtimestamp(date)
            result['date'] = dt_date.strftime('%A, %d.  %B %Y')
            #result['date'] = datetime.fromtimestamp(date).strftime('%x')

            for track in tracks:

                if '@attr' in track:
                    if 'nowplaying' in track['@attr']:
                        if track['@attr']['nowplaying'] == 'true':
                            # user.getRecentTracks includes the song currently
                            # playing (if there is one) (even if it is > "to").
                            print 'Skipped currently playing track: ', track
                            continue

                timestamp = float(track['date']['uts'])
                time = datetime.fromtimestamp(timestamp).strftime('%H:%M')

                result['tracks'].append(
                    {'artist': {'name': track['artist']['#text']},
                     'track': {'title': track['name'],
                               'album': track['album']['#text'],
                               'url': track['url'],
                               'time': time,
                               'img_small':
                               track['image'][0]['#text']}})

            # If we have 10+ tracks pick 10 random ones, else pick all
            if len(result['tracks']) <= NUM_RANDOM_TRACKS:
                result['random_tracks'] = result['tracks']
            else:
                result['random_tracks'] = random.sample(result['tracks'],
                                                        NUM_RANDOM_TRACKS)
            # TODO sort random tracks by the time were played

            result['top_tracks'] = self._parse_top_tracks(result['tracks'])
            result['top_artists'] = self._parse_top_artists(result['tracks'])
            result['top_albums'] = self._parse_top_albums(result['tracks'])

        except KeyError, e:
            print 'Error fetching data:', e

        return result

    def _parse_top_tracks(self, tracks):
        d = defaultdict(int)
        for track in tracks:
            artisttitle = ''.join([track['artist']['name'],
                                   ' - ', track['track']['title']])
            d[artisttitle] += 1
        result = sorted(d.iteritems(), key=itemgetter(1), reverse=True)
        return result[:NUM_TOP_TRACKS]

    def _parse_top_artists(self, tracks):
        d = defaultdict(int)
        for track in tracks:
            d[track['artist']['name']] += 1
        result = sorted(d.iteritems(), key=itemgetter(1), reverse=True)
        return result[:NUM_TOP_ARTISTS]

    def _parse_top_albums(self, tracks):
        d = defaultdict(int)
        for track in tracks:
            d[track['track']['album']] += 1
        result = sorted(d.iteritems(), key=itemgetter(1), reverse=True)
        return result[:NUM_TOP_ALBUMS]
