#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    eas-create-gdt.py - small tool for creating a xDT-File containing a patient id
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

import sys, os
import codecs


if len(sys.argv) < 3:
    print("Usage: eas-create-gdt.py FILENAME PATIENTID")
    sys.exit(1)


if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    gdtfile = sys.argv[1]
    print("Saving to %s" % (gdtfile))
    grabinfo = {
        3000: "id",
        3100: "nameprefix",
        3101: "name",
        3102: "surname",
        3104: "title",
        8402: "dowhat"
    }

    id = sys.argv[2]
    if(id.startswith("easpatient:")):
        id = id[11:]

    idlen = len(id)
    linelen = 3 + 4 + idlen + 2

    template = "%03d%04d%s\r\n"

    with codecs.open(gdtfile, encoding="iso-8859-15", mode="w") as f:
        f.write(template % (13, 8000, 6200))
        f.write(template % (linelen, 3000, id))
        f.write(template % (10, 8202, 3))
