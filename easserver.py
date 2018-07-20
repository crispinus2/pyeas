#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import environ

from autobahn.twisted.component import Component
from autobahn.twisted.component import run
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import CallResult
from autobahn.wamp import register
from peewee import SqliteDatabase, Model, CharField, ForeignKeyField, IntegerField, DoesNotExist, IntegrityError, JOIN

eascomp = Component(
    transports=u"ws://localhost:8080/ws",
    realm=u"eas",
)

db = SqliteDatabase("eas.db", pragmas={'foreign_keys': 1})
mySession = None

@eascomp.on_join
def onJoin(session, details):
    global mySession
    print("Session attached")
    if mySession is None:
        mySession = session


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

        room.patient = patient
        room.save()

        if mySession:
            mySession.publish(u"com.eas.room_populated", name, {'id': patId, 'name': patName,
                                                                'surname': patSurname, 'title': patTitle})
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)

    return True


@eascomp.register(u"com.eas.room_message")
def setRoomMessage(name, message):
    room = Room.get_or_none(name = name)
    if room is not None:
        room.message = message
        room.save()
        return True

        if mySession:
            mySession.publish(u"com.eas.room_message_set", name, message)
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)


@eascomp.register(u"com.eas.clear_room")
def clearRoom(name):
    room = Room.get_or_none(name = name)
    if room is not None:
        room.patient = None
        room.save()
        if mySession:
            mySession.publish(u"com.eas.room_cleared", name)
        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)


@eascomp.register(u"com.eas.list_rooms")
def listRooms():
    rooms = Room.select() #.join(Patient, JOIN.LEFT_OUTER)
    return_list = []
    for room in rooms:
        ret_dict = {u'room': room.name, u'priority': room.priority, u'message': room.message}
        if room.patient is None:
            ret_dict[u'empty'] = True
            ret_dict[u'patient'] = None
        else:
            patient = {
                'id': room.patient.patId,
                'name': room.patient.name,
                'surname': room.patient.surname,
                'title': room.patient.title
            }
            ret_dict[u'patient'] = patient
            ret_dict[u'empty'] = False

        return_list.append(ret_dict)

    return CallResult(return_list)


def createTables():
    with db:
        db.create_tables([Patient, Room])

if __name__ == '__main__':
    db.connect()

    run([eascomp])