#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import environ

from autobahn.twisted.component import Component
from autobahn.twisted.component import run
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp import register
from peewee import SqliteDatabase, Model, CharField, ForeignKeyField, IntegerField, DoesNotExist, IntegrityError

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


@eascomp.register(u"com.eas.addRoom")
def addRoom(name):
    Room.create(name=name)
    Room.save()
    if mySession:
        mySession.publish(u"com.eas.room_added", name)
    return True


@eascomp.register(u"com.eas.deleteRoom")
def deleteRoom(name):
    room = Room.get_or_none(name=name)
    if room is not None:
        room.delete_instance()
        if mySession:
            mySession.publish(u"com.eas.room_deleted", name)
        return True
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)


@eascomp.register(u"com.eas.populateRoom")
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
            mySession.publish(u"com.eas.room_populated", name, {'patient_id': patId, 'patient_name': patName,
                                                                'patient_surname': patSurname, 'patient_title': patTitle})
    else:
        raise ApplicationError(u"com.eas.error.room_not_found", room=room)

    return True


@eascomp.register(u"com.eas.roomMessage")
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


@eascomp.register(u"com.eas.clearRoom")
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
    rooms = Room.select().join(Patient)
    return_list = []
    for room in rooms:
        ret_dict = {'room': room.name, 'message': room.message}
        if room.patient is None:
            ret_dict['empty'] = True
        else:
            ret_dict['patient_id'] = room.patient.patId
            ret_dict['patient_name'] = room.patient.name
            ret_dict['patient_surname'] = room.patient.surname
            ret_dict['patient_title'] = room.patient.title
            ret_dict['empty'] = False

        return_list.append(ret_dict)

    return return_list


def createTables():
    with db:
        db.create_tables([Patient, Room])

if __name__ == '__main__':
    db.connect()

    run([eascomp])