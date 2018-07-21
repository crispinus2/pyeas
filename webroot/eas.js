var idToRoom = {};
var roomNo = 0;
var editMode = false;
var session = null;
var selected_room = null;

function set_edit_mode(mode)
{
    if(mode){
        editMode = true;
        $(".roomcontrol").show();
    }
    else {
        editMode = false;
        $(".roomcontrol").hide();
    }
}

function toggle_edit_mode() {
    if(editMode == false) {
        set_edit_mode(true);
    }
    else {
        set_edit_mode(false);
    }
}

function new_room() {
    $("#dialog-new-room").dialog("open");
}

function clear_room(room_unescaped) {
    session.call('com.eas.clear_room', [room_unescaped]);
}

function populate_room(room_unescaped, patient) {
    room = idToRoom[room_unescaped];
    if(patient!=null) {
        var patstring = patient["name"]+", ";
        if(patient["title"]!="") patstring += patient["title"]+" ";
        patstring += patient["surname"];
        $("#roompatient_"+room).append('<a href="easpatient:'+patient["id"]+'" title="Patient öffnen"></a>');
        $("#roompatient_"+room+" a").text(patstring);
        $("#roompatient_"+room).append('<a href="#" id="clear_'+room+'"><span class="ui-icon ui-icon-closethick"/></a>');
        $("#room_"+room).addClass("occupied");
        $("#clear_"+room).click(function() {
           clear_room(room_unescaped); 
        });
    }
    else {
        var field = "#roompatient_"+room;
        $(field).text("frei");
        $("#room_"+room).removeClass("occupied");
    }
}

function room_message_changed(room_unescaped, message) {
    room = idToRoom[room_unescaped];
    if(message!=null && message != "") {
        $("#roommessage_"+room).text(message);
        $("#room_"+room).addClass("hasmessage");
    }
    else {
        $("#roommessage_"+room).text('');
        $("#room_"+room).removeClass("hasmessage");
    }
}

function sort_rooms() {
    var $roomcontainer = $("#rooms");
    var $rooms = $roomcontainer.find(".room");
    [].sort.call($rooms, function(a,b) {
        return +$(a).attr('data-priority') - +$(b).attr('data-priority');
    });
    $roomcontainer.append($rooms);
}

function set_room_priority(room, priority)
{
    //set_edit_mode(false);
    session.call('com.eas.room_set_priority', [room, priority]);
}

function set_room_message(room, message) {
    session.call('com.eas.room_message', [room, message]);
}

function populate_roomcontrol(room_unescaped, priority) {
    room = idToRoom[room_unescaped];
    $("#roomcontrol_"+room).append(
        '<div class="priority_container">' +
        '<span class="label">Priorität:</span><input type="text" class="priority" id="priority_'+room+'" value="'+priority+'"/>' +
        '</div><div class="delete_button_container">' +
        '<a href="#" class="delete_button" id="delete_'+room+'">löschen</a>' +
        '</div>'
        );

    $("#priority_"+room).blur(function(event) {
        set_room_priority(room_unescaped, $(event.target).val());
    });

    $("#priority_"+room).keypress(function(event) {
        if(event.which == 13) {
            set_room_priority(room_unescaped, $(event.target).val());
            event.preventDefault();
        }
    });

    $("#delete_"+room).click(function() {
        selected_room = room_unescaped; 
        $("#dialog-confirm").dialog("open");
    });
}

function room_added(room_unescaped, priority, patient, message) {
    if(room_unescaped in idToRoom) {
        room_deleted(room_unescaped);
    }
    else {
        idToRoom[room_unescaped] = "room"+roomNo;
        roomNo++;
    }
    room = idToRoom[room_unescaped];
    $("#rooms").append(
        '<div class="room" id="room_'+ room +'" data-priority="'+priority+'">\
            <div class="roomname" id="roomname_'+room+'"></div>\
            <div class="roommessage"> \
                <span class="roommessage_text" id="roommessage_'+room+'"></span>\
                <a href="#" id="edit_message_'+room+'" title="Nachricht setzen"><span class="ui-icon ui-icon-pin-w"/></a> \
            </div> \
            <div class="roompatient" id="roompatient_'+room+'"></div>\
            <div class="roomcontrol" id="roomcontrol_'+room+'"></div>\
        </div>');
    $("#roomname_"+room).text(room_unescaped);
    $("#edit_message_"+room).click(function() {
        selected_room = room_unescaped;
        room = idToRoom[selected_room];
        preval = $("#roommessage_"+room).text();
        $("#room_message_text").val(preval);
        $("#dialog-message").dialog("open");
    });
    room_message_changed(room_unescaped, message);
    populate_room(room_unescaped, patient);
    populate_roomcontrol(room_unescaped, priority);
    if(editMode) {
        $("#roomcontrol_"+room).show();
    }
    sort_rooms();
}

function delete_room(room_unescaped) {
    session.call('com.eas.delete_room', [room_unescaped]);
}

function add_room(room_unescaped, priority) {
    session.call('com.eas.add_room', [room_unescaped, priority]);
}

function room_deleted(room_unescaped) {
    room = idToRoom[room_unescaped];
    $("#room_"+room).remove();
}

function room_priority_changed(room_unescaped, priority) {
    room = idToRoom[room_unescaped];
    $("#room_"+room).attr('data-priority', priority);
    sort_rooms();
}


var clock_timeout = 0;
var interval_msec = 500;

function update_clock() {
    var dt_now = new Date();
    var hh	= dt_now.getHours();
    var mm	= dt_now.getMinutes();
    var ss	= dt_now.getSeconds();
    var wd = dt_now.getDay();
    var day = dt_now.getDate();
    var month = dt_now.getMonth();
    var year = dt_now.getFullYear();
    var weekday = "";

    if(hh < 10){
        hh = "0" + hh;
    }
    if(mm < 10){
        mm = "0" + mm;
    }
    if(ss < 10){
        ss = "0" + ss;
    }
    if(day < 10){
        day = "0" + day;
    }
    if(month < 10){
        month = "0" + month;
    }

    switch(wd) {
        case 0:
            weekday = "So.";
            break;
        case 1:
            weekday = "Mo.";
            break;
        case 2:
            weekday = "Di.";
            break;
        case 3:
            weekday = "Mi.";
            break;
        case 4:
            weekday = "Do.";
            break;
        case 5:
            weekday = "Fr.";
            break;
        case 6:
            weekday = "Sa.";
            break;
    }

    $("#clock").html( weekday + ", " + day + "." + month + "." + year + " " + hh + ":" + mm + ":" + ss);

    clock = setTimeout("update_clock()", interval_msec);
}

$(document).ready(function() {
    clock = setTimeout("update_clock()", interval_msec);

    $("#dialog-confirm").dialog({
       resizable: false,
        height: "auto",
        width: 400,
        autoOpen: false,
        modal: true,
        buttons: {
            "Löschen": function() {
                delete_room(selected_room);
                $(this).dialog("close");
            },
            "Abbrechen": function() {
                $(this).dialog("close");
            }
        }
    });

    $("#dialog-new-room").dialog({
        resizable: false,
        dialogClass: "no-close",
        height: "auto",
        width: 400,
        autoOpen: false,
        modal: true,
        buttons: {
            "Erstellen": function() {
                var priority = parseInt($("#new_room_priority").val());
                if(!Number.isInteger(priority)) {
                    $("#dialog-error").dialog("open");
                }
                else {    
                    add_room($("#new_room_name").val(), $("#new_room_priority").val());
                    $("#new_room_name").val("");
                    $("#new_room_priority").val("0");
                    $(this).dialog("close");
                }
            },
            "Abbrechen": function() {
                $("#new_room_name").val("");
                $("#new_room_priority").val("0");
                $(this).dialog("close");
            }
        }
    });

    $("#dialog-message").dialog({
        resizable: false,
        dialogClass: "no-close",
        height: "auto",
        width: 400,
        autoOpen: false,
        modal: true,
        buttons: {
            "Speichern": function() {
                msg = $("#room_message_text").val();
                if(msg == "")
                    msg = null;
                set_room_message(selected_room, msg);
                $("#room_message_text").val("");
                $(this).dialog("close");
            },
            "Abbrechen": function() {
                $("#room_message_text").val("");
                $(this).dialog("close");
            }
        }
    });

    $("#dialog-error").dialog({
        resizable: false,
        height: "auto",
        width: 400,
        autoOpen: false,
        modal: true,
        buttons: {
            "Ok": function() {
                $(this).dialog("close");
            }
        }
    });

    $("#dialog-no-connection-error").dialog({
        resizable: false,
        dialogClass: "no-close",
        height: "auto",
        width: 400,
        autoOpen: true,
        modal: true
    });

    var connection = new autobahn.Connection({
        url: 'ws://'+window.location.hostname+':8080/ws',
        realm: 'eas'});

    connection.onclose = function(reason, details) {
        $("#dialog-no-connection-error").dialog("open");
    };

    connection.onopen = function(mySession) {
        session = mySession;

        $("#dialog-no-connection-error").dialog("close");

        function on_room_priority_changed(args, kwargs) {
            room_priority_changed(kwargs.room, kwargs.priority);
        }

        session.subscribe('com.eas.room_priority_changed', on_room_priority_changed);

        function on_room_deleted(args, kwargs) {
            room_deleted(args[0]);
        }

        session.subscribe('com.eas.room_deleted', on_room_deleted);

        function on_room_added(args, kwargs) {
            room_added(kwargs.name, kwargs.priority, null, null);
        }

        session.subscribe('com.eas.room_added', on_room_added);

        function on_room_populated(args, kwargs) {
            populate_room(args[0], args[1]);
        }

        session.subscribe('com.eas.room_populated', on_room_populated);

        function on_room_message_set(args, kwargs) {
            room_message_changed(args[0], args[1]);
        }

        session.subscribe('com.eas.room_message_set', on_room_message_set);

        session.call('com.eas.list_rooms').then(
            function(res) {
                console.log("Room result:", res);
                for(var i=0; i < res.length; i++) {
                    room_added(res[i]["room"], res[i]["priority"], res[i]["patient"], res[i]["message"]);
                }
            }
        );
    };

    console.log("Opening connection");
    connection.open();

});