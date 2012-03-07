#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import cherrypy
from jinja2 import Environment, FileSystemLoader
from fetchfm import FetchFM

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    loader=FileSystemLoader(os.path.join(CURRENT_DIR, 'templates/')))


class WarpFM():
    @cherrypy.expose
    def index(self):
        tmpl = env.get_template('index.html')
        return tmpl.render()

    @cherrypy.expose
    def warp(self, username=None):
        if not username:
            raise cherrypy.HTTPRedirect("index")

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
            tmpl = env.get_template('nodata.html')
            return tmpl.render(username=username,
                               date=fetch.get_formated_day())

if __name__ == '__main__':
    conf = {'/css': {'tools.staticdir.on': True,
                     'tools.staticdir.dir': os.path.join(CURRENT_DIR,
                                                         'templates', 'css')}}
    cherrypy.quickstart(WarpFM(), '/', config=conf)
