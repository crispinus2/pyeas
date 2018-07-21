var session = null;

function populate_room(room_unescaped, patient) {
    room = idToRoom[room_unescaped];
    if(patient!=null) {
        var patstring = patient["name"]+", ";
        if(patient["title"]!="") patstring += patient["title"]+" ";
        patstring += patient["surname"];
        $("#roompatient_"+room).text(patstring);
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

    $("#dialog-no-connection-error").dialog({
        resizable: false,
        dialogClass: "no-close",
        height: "auto",
        width: 400,
        autoOpen: true,
        modal: true
    });

    var connection = new autobahn.Connection({
        url: 'ws://127.0.0.1:8080/ws',
        realm: 'eas'});

    connection.onclose = function(reason, details) {
        $("#dialog-no-connection-error").dialog("open");
    };

    connection.onopen = function(mySession) {
        session = mySession;

        $("#dialog-no-connection-error").dialog("close");

        function on_room_populated(args, kwargs) {
            populate_room(args[0], args[1]);
        }

        session.subscribe('com.eas.room_populated', on_room_populated);
    };

    console.log("Opening connection");
    connection.open();

});