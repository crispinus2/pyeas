#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    easserver.py - core server of the Elektronisches Aufruf System
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

from os import environ

from autobahn.twisted.component import Component
from autobahn.twisted.component import run
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import CallResult
from peewee import SqliteDatabase, Model, CharField, ForeignKeyField, IntegerField, DoesNotExist, IntegrityError, JOIN

eascomp = Component(
    transports=u"ws://localhost:8080/ws",
    realm=u"eas",
)

db = SqliteDatabase("eas.db", pragmas={'foreign_keys': 1})
mySession = None

wcOccupied = False

class BaseModel(Model):
    class Meta:
        database = db


"""
Implementation of a patient
"""
class Patient(BaseModel):
    patId = IntegerField(unique=True, null=False)
    surname = CharField(default="", null=False)
    name = CharField(default="", null=False)
    title = CharField(default="", null=False)

    """
    Renders a complete patient's name suitable for display e.g. on the monitor
    in the form Title Surname Name (separated by spaces)
    """
    def fullName(self):
        return " ".join((self.title, self.surname, self.name))


"""
Implementation of a room
"""
class Room(BaseModel):
    name = CharField(null=False, unique=True)
    message = CharField(null=True)
    patient = ForeignKeyField(Patient, backref="patients", null=True, on_delete="SET NULL", on_update="CASCADE")
    priority = IntegerField(null=False, default=0)

    """
    Return this room's state text
    If the room is occupied by a patient, invoke his/her fullName() method
    If a message is set, return the message
    If nothing is set, return "frei"
    """
    def stateText(self):
        if self.patient is not None:
            return self.patient.fullName()
        elif self.message is not None:
            return self.message
        else:
            return "frei"

    """
    Return true if no patient is in the room and no message is set
    """
    def isFree(self):
        return self.patient is None and self.message is None

    """
    Clear the current message
    """
    def clearMessage(self):
        self.message = None

    """
    Clear the current patient
    """
    def clearPatient(self):
        self.patient = None

    """
    Clear the room (remove patient and/or message)
    """
    def clearRoom(self):
        self.clearMessage()
        self.clearPatient()


@eascomp.register(u"com.eas.add_room")
def addRoom(name, priority):
    try:
        Room.create(name=name, priority=priority)
        if mySession:
            mySession.publish(u"com.eas.room_added", name=name, priority=priority)
    except IntegrityError:
        raise ApplicationError(u"com.eas.room_exists", name)
    return True


@eascomp.register(u"com.eas.delete_room")
def deleteRoom(name):
    room = Room.get_or_none(name=name)
    if room is not None:
        room.delete_instance()
        if mySession:
            mySession.publish(u"com.eas.room_deleted", name)
        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)


@eascomp.register(u"com.eas.room_set_priority")
def setRoomPriority(name, priority):
    room = Room.get_or_none(name=name)
    if room is not None:
        room.priority = priority
        room.save()
        if mySession:
            mySession.publish(u"com.eas.room_priority_changed", room=name, priority=priority)
        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)

@eascomp.register(u"com.eas.clear_room")
def clearRoom(name):
    room = None
    if name is Room:
        room = name
    else:
        room = Room.get_or_none(name = name)
    if room is not None:
        room.patient = None
        room.save()
        if mySession:
            mySession.publish(u"com.eas.room_populated", unicode(name), None)
        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=unicode(room))


@eascomp.register(u"com.eas.populate_room")
def populateRoom(name, patId, patName, patSurname, patTitle):
    room = Room.get_or_none(name=name)
    if room is not None:
        patient, created = Patient.get_or_create(patId=patId,
                                                 defaults={'name': patName, 'surname': patSurname, 'title': patTitle})
        if not created:
            patient.name = patName
            patient.surname = patSurname
            patient.title = patTitle
            patient.save()

        oldroom = None
        with db.atomic() as transaction:
            oldroom = Room.get_or_none(patient=patient)
            if oldroom is not None:
                oldroom.patient = None
                oldroom.save()

            room.patient = patient
            room.save()

            if mySession:
                if oldroom is not None:
                    mySession.publish(u"com.eas.room_populated", unicode(oldroom.name), None)
                mySession.publish(u"com.eas.room_populated", unicode(name), { u"id": unicode(patId), u"name": unicode(patName),
                                                                u"surname": unicode(patSurname), u"title": unicode(patTitle)})
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=name)

    return True


@eascomp.register(u"com.eas.room_message")
def setRoomMessage(name, message):
    room = Room.get_or_none(name = name)
    if room is not None:
        room.message = message
        room.save()

        resmsg = unicode(message)
        if message is None:
            resmsg = None
        if mySession:
            mySession.publish(u"com.eas.room_message_set", unicode(name), resmsg)

        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)


@eascomp.register(u"com.eas.list_rooms")
def listRooms():
    rooms = Room.select().join(Patient, JOIN.LEFT_OUTER)
    return_list = []
    for room in rooms:
        ret_dict = {u'room': room.name, u'priority': room.priority, u'message': room.message}
        if room.patient is None:
            ret_dict[u'empty'] = True
            ret_dict[u'patient'] = None
        else:
            patient = {
                u'id': room.patient.patId,
                u'name': room.patient.name,
                u'surname': room.patient.surname,
                u'title': room.patient.title
            }
            ret_dict[u'patient'] = patient
            ret_dict[u'empty'] = False

        return_list.append(ret_dict)

    return CallResult(return_list)

@eascomp.register(u"com.eas.set_wc_state")
def setWcState(occupied):
    global wcOccupied
    wcOccupied = occupied

    print("Setting WC state to %s" % wcOccupied)

    if mySession:
        mySession.publish(u"com.eas.wc_state_changed", wcOccupied)

    return True

@eascomp.register(u"com.eas.get_wc_state")
def getWcState():
    global wcOccupied

    return wcOccupied

@eascomp.on_join
def onJoin(session, details):
    global mySession
    print("Session attached")
    if mySession is None:
        mySession = session

    rooms = Room.select().join(Patient, JOIN.LEFT_OUTER)

    for room in rooms:
        mySession.publish(u"com.eas.room_added", name=room.name, priority=room.priority)
        if room.patient is not None:
            mySession.publish(u"com.eas.room_populated", unicode(room.name),
                              {u"id": unicode(room.patient.patId), u"name": unicode(room.patient.name),
                               u"surname": unicode(room.patient.surname), u"title": unicode(room.patient.title)})

def createTables():
    with db:
        db.create_tables([Patient, Room])

if __name__ == '__main__':
    db.connect()
    createTables()

    run([eascomp])