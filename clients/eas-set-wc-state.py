#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    eas-set-wc-state.py - small tool for setting the WC occupation state of an EAS server instance
    Copyright (C) 2019 Julian Hartig

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


if len(sys.argv) < 3 or (sys.argv[2]!="0" and sys.argv[2]!="1"):
    print("Usage: eas-set-wc-state.py SERVER 0|1")
    print ("where 0 means free and 1 means occupied")
    sys.exit(1)

easclient = Component(
    transports=u"ws://%s/ws" % (sys.argv[1]),
    realm=u"eas",
)

@easclient.on_join
@inlineCallbacks
def join(session, details):
    print("Joined session")
    try:
        wcstate = False
        if sys.argv[2]=="1":
            wcstate = True
        res = yield session.call(u'com.eas.set_wc_state', wcstate)
    except ApplicationError as e:
        print("ApplicationError, aborting: %s" % (e))

    yield session.leave()


if __name__ == '__main__':
    run([easclient])