#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import cherrypy
from jinja2 import Environment, FileSystemLoader
from fetchfm import FetchFM

env = Environment(loader=FileSystemLoader('templates'))


class WarpFM():
    @cherrypy.expose
    def index(self):
        tmpl = env.get_template('index.html')
        return tmpl.render()

    @cherrypy.expose
    def warp(self, username):
        fetch = FetchFM()
        userinfo = fetch.get_userinfo(username)
        result = fetch.get_tracks(username)

        if result and userinfo:
            tracks = result['tracks']

            # Tracks played that day
            tracks_played = len(tracks)

            # Total tracks played
            playcount = int(userinfo['playcount'])

            # Tracks played that day / Total tracks played
            percentage = '%.2f' % (tracks_played / (playcount / 100.0))

            tmpl = env.get_template('warp.html')
            return tmpl.render(name=username,
                               random_tracks=result['random_tracks'],
                               playcount=playcount,
                               tracks_played=tracks_played,
                               percentage=percentage,
                               date=result['date'],
                               top_tracks=result['top_tracks'],
                               top_artists=result['top_artists'],
                               top_albums=result['top_albums'])
        else:
            return 'Error fetching data.'

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/css': {'tools.staticdir.on': True,
                     'tools.staticdir.dir': os.path.join(current_dir,
                                                         'templates', 'css')}}

    cherrypy.quickstart(WarpFM(), '/', config=conf)
