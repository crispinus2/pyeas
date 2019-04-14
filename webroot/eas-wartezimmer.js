var session = null;
var bellElement = document.createElement("audio");
var idToRoom = {};
var roomNo = 0;
var urlParams = new URLSearchParams(location.search);

// Whether to call patients by name or by number
var usePatientIdForCalling = false;

// Maximum number of calls displayed at the same time
var numberOfCalls = 8;
var displayWcState = true;

if(urlParams.has("callby") && urlParams.get("callby") == "id") {
    usePatientIdForCalling = true;
}
if(urlParams.has("calls")) {
    try{
        numberOfCalls = Number.parseInt(urlParams.get("calls"));
    }
    catch(err)
    {
        console.log("Invalid value supplied for calls parameter: " + urlParams.get("calls")+", expect integer");
    }
}
if(urlParams.has("noWcState") && urlParams.get("noWcState") == "yes") {
    displayWcState = false;
}

bellElement.setAttribute('src', 'bell.mp3');

function populate_room(room_unescaped, patient) {
    if(!(room_unescaped in idToRoom)) {
        idToRoom[room_unescaped] = "room"+roomNo;
        roomNo++;
    }
    
    room = idToRoom[room_unescaped];
    $("#call_"+room).remove();
    
    if(patient!=null) {
        while($("#content .call").length >= numberOfCalls)
        {
            $("#content .call").first().remove();
        }
        
        var patstring;
        
        if(usePatientIdForCalling)
            patstring = patient["id"];
        else {
            var patstring = patient["name"]+", ";
            if(patient["title"]!="") patstring += patient["title"]+" ";
            patstring += patient["surname"];
        }
        
        $("#content").append(
            '<div class="call" id="call_'+room+'">' +
            '    <div class="patient" id="call_patient_'+room+'"/>' +
            '    <div class="room" id="call_room_'+room+'"/>' +
            '    <div style="clear:both"/>' +
            '</div>'
            );
        $("#call_patient_"+room).text(patstring);
        $("#call_room_"+room).text(room_unescaped);
        
        flash_call($("#call_"+room), 21, false);
        bellElement.pause();
        bellElement.currentTime = 0;
        bellElement.play();
    }
}

function wc_state_changed(wc_state) {
    if(wc_state) {
        $("#wcbar").addClass("occupied");
        $("#wcbar").html("WC besetzt");
    }
    else {
        $("#wcbar").removeClass("occupied");
        $("#wcbar").html("WC frei");
    }
}

function flash_call(call, times, flash) {
    if(flash) {
        call.removeClass("flashedcall");
    }
    else {
        call.addClass("flashedcall");
    }
    
    if(times > 0)
        window.setTimeout(function() { flash_call(call, times-1, !flash)}, 700);
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
        url: 'ws://'+window.location.hostname+':8080/ws',
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
        if(displayWcState) {
            function on_wc_state_changed(args, kwargs) {
                wc_state_changed(args[0]);
            }
            session.subscribe('com.eas.wc_state_changed', on_wc_state_changed);

            session.call('com.eas.get_wc_state').then(
                function(res) {
                    wc_state_changed(res);
                }
            );
        }
        else {
            $("#wcbar").hide();
        }
    };

    console.log("Opening connection");
    connection.open();
    
});