// setup gauges
var potOpts = {
    angle: -0.2, // The span of the gauge arc
    lineWidth: 0.2, // The line thickness
    radiusScale: 0.97, // Relative radius
    pointer: {
        length: 0.41, // // Relative to gauge radius
        strokeWidth: 0.082, // The thickness
        color: '#000000' // Fill color
    },
    limitMax: true,     // If false, max value increases automatically if value > maxValue
    limitMin: true,     // If true, the min value of the gauge will be fixed
    highDpiSupport: true,     // High resolution support
    staticLabels: {
        font: "10px sans-serif",  // Specifies font
        labels: [0, 20, 40, 60, 80, 100],  // Print labels at these values
        color: "#000000",  // Optional: Label text color
        fractionDigits: 0  // Optional: Numerical precision. 0=round off.
    },
    staticZones: [
        {strokeStyle: "#30B32D", min: 00, max: 60, height: 1}, // Green
        {strokeStyle: "#FFDD00", min: 60, max: 80, height: 1.2}, // Yellow
        {strokeStyle: "#F03E3E", min: 80, max: 100, height: 1.4},  // Red
    ],
    renderTicks: {
        divisions: 10,
        divWidth: 1.1,
        divLength: 0.7,
        divColor: "#333333",
        subDivisions: 5,
        subLength: 0.5,
        subWidth: 0.6,
        subColor: "#666666"
    },

};
var target = document.getElementById('potGauge');
var gauge = new Gauge(target).setOptions(potOpts);
gauge.maxValue = 100;
gauge.minValue = 0;
gauge.animationSpeed = 60;
gauge.set(0);

var tempOpts = {
    angle: 0, // The span of the gauge arc
    lineWidth: 0.2, // The line thickness
    radiusScale: 0.97, // Relative radius
    pointer: {
        length: 0.41, // // Relative to gauge radius
        strokeWidth: 0.082, // The thickness
        color: '#000000' // Fill color
    },
    limitMax: true,     // If false, max value increases automatically if value > maxValue
    limitMin: true,     // If true, the min value of the gauge will be fixed
    highDpiSupport: true,     // High resolution support
    staticLabels: {
        font: "10px sans-serif",  // Specifies font
        labels: [0, 5, 10, 15, 20, 25, 30, 35, 40],  // Print labels at these values
        color: "#000000",  // Optional: Label text color
        fractionDigits: 0  // Optional: Numerical precision. 0=round off.
    },
    staticZones: [
        {strokeStyle: "#0000a0", min: 00, max: 15, height: 1}, // blue
        {strokeStyle: "#30B32D", min: 15, max: 25, height: 1.4}, // Green
        {strokeStyle: "#F03E3E", min: 25, max: 40, height: 1},  // Red
    ],
    renderTicks: {
        divisions: 8,
        divWidth: 1.1,
        divLength: 0.7,
        divColor: "#333333",
        subDivisions: 5,
        subLength: 0.5,
        subWidth: 0.6,
        subColor: "#666666"
    },

};
var tempTarget = document.getElementById('tempGauge');
var tempGauge = new Gauge(tempTarget).setOptions(tempOpts);
tempGauge.maxValue = 40;
tempGauge.minValue = 0;
tempGauge.animationSpeed = 60;
tempGauge.set(0);

gatherDataAjaxRunning = false;
function gatherData(){
    // stop overlapping requests
    if(gatherDataAjaxRunning) return;

    gatherDataAjaxRunning = true;
    let postData = {
        "action": "readData"
    };
    $.post( "/api", postData, function( data ) {
        // handle gauge
        potPercent = parseInt(parseInt(data.pot_value) * 100 / 65000);
        gauge.set(potPercent);
        $('#potValue').html(potPercent);
        $('#potValue').removeClass(["bg-success", "bg-warning", "bg-danger"]);
        if(potPercent <= 60) {
            $('#potValue').addClass("bg-success");
        }
        else if(potPercent <= 80) {
            $('#potValue').addClass("bg-warning");
        }
        else {
            $('#potValue').addClass("bg-danger");
        }

        // handle temp gauge
        temp = parseFloat(data.temp_value);
        tempGauge.set(temp);
        $('#tempValue').html(temp.toFixed(1));
        $('#tempValue').removeClass(["bg-success", "bg-warning", "bg-danger"]);
        if(temp <= 15) {
            $('#tempValue').addClass("bg-primary");
        }
        else if(temp <= 25) {
            $('#tempValue').addClass("bg-success");
        }
        else {
            $('#tempValue').addClass("bg-danger");
        }

        // handle rgb leds
        for(count = 0; count < 8; count ++){
            let colour = "rgb(" + (parseInt(data.rgb_leds[count][0])*2) + ", "
                    + (parseInt(data.rgb_leds[count][1])*2) + ", "
                    + (parseInt(data.rgb_leds[count][2])*2);
            $("#rgb_" + count).css("background-color", colour);
        }

        // allow next data gather call
        gatherDataAjaxRunning = false;

    });
}

function setLedColour(colour) {
    let postData = {
    "action": "setLedColour",
    "colour": colour
    };
    $.post( "/api", postData, function( data ) {
        console.log(data);
        if (data.status == "OK"){
            // set colour from json array
            if (data.cled_states.blue){
                $("#cled-state").css("background-color", "rgb(0,0,255)");
            }
            else if (data.cled_states.yellow){
                $("#cled-state").css("background-color", "rgb(255,255,0)");
            }
            else if (data.cled_states.green){
                $("#cled-state").css("background-color", "rgb(0,255,0)");
            }
            else {
                $("#cled-state").css("background-color", "rgb(0,0,0)");
            }
        }
        else {
            alert("Error setting led colour");
        }
    });
}

var rgb_ajax_in_progress = false;

function set_rgb_colour() {
    console.log("set_rgb_colour")
    // do not start new request until previous finished
    if(rgb_ajax_in_progress) return;

    let postData = {
        "action": "setRgbColour",
        "red": $("#rgb_red").val(),
        "green": $("#rgb_green").val(),
        "blue": $("#rgb_blue").val()
    };
    rgb_ajax_in_progress = true;
    $.post( "/api", postData, function( data ) {
        console.log(data);
        rgb_ajax_in_progress = false // allow next call
        if (data.status == "OK"){
            // set colour from json array
            let colour = "rgb(" + (parseInt(data.rgb_colours.red)*2) + ", "
                + (parseInt(data.rgb_colours.green)*2) + ", "
                + (parseInt(data.rgb_colours.blue)*2);
            for(count = 0; count < 4; count ++){
                $("#rgb_" + count).css("background-color", colour);
            }
        }
        else {
            alert("Error setting led colour");
        }

    });
}

var dataTimer;
$( document ).ready(function() {
    set_rgb_colour(); // initialise rgb display
    dataTimer = setInterval(window.gatherData,500); // call data every 0.5 seconds
});