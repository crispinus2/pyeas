#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    eas-populate-room.py - small tool for populating a room using a gdt file
    Copyright (C) 2018 Julian Hartig

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys
import codecs

from autobahn.twisted.component import Component
from autobahn.twisted.component import run
from autobahn.wamp.exception import ApplicationError
from twisted.internet.defer import inlineCallbacks


if len(sys.argv) < 4:
    print("Usage: eas-populate-room.py SERVER GDTFILE ROOM")
    sys.exit(1)

easclient = Component(
    transports=u"ws://%s/ws" % (sys.argv[1]),
    realm=u"eas",
)

infos = {}
room = sys.argv[3]

@easclient.on_join
@inlineCallbacks
def join(session, details):
    print("Joined session")
    try:
        if not 'dowhat' in infos or infos["dowhat"] == "CALL":
            res = yield session.call(u'com.eas.populate_room',
                                     room, infos["id"], infos["name"], infos["surname"], infos["title"])
        elif infos["dowhat"] == "LEAVE":
            res = yield session.call(u'com.eas.clear_room', room)
    except ApplicationError as e:
        print("ApplicationError, aborting: %s" % (e))

    yield session.leave()


if __name__ == '__main__':
    gdtfile = sys.argv[2]
    grabinfo = {
        3000: "id",
        3100: "nameprefix",
        3101: "name",
        3102: "surname",
        3104: "title",
        8402: "dowhat"
    }
    infos = {
        "id": 0,
        "nameprefix": "",
        "name": "",
        "surname": "",
        "title": ""
    }
    with codecs.open(gdtfile, encoding="iso-8859-15", mode="r") as f:
        for line in f:
            linelen = int(line[:3])
            feldkennung = int(line[3:7])
            inhalt = line[7:linelen - 2]
            if feldkennung in grabinfo:
                infos[grabinfo[feldkennung]] = inhalt

            print("Feld: %d Inhalt: %s" % (feldkennung, inhalt))

    print("Starting up component")
    run([easclient])