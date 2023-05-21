// var get_reading = setInterval(getReadingFromPico, 5000);

function getReadingFromPico() {
    const formData = new FormData();
    formData.append("action", "readPot");
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        document.getElementById("reading").innerHTML = this.responseText;
    }
    xhttp.open("POST", "/api", true);
    xhttp.send(formData);
}


function setLedColour(colour) {
    const jsonData = {
        "action": "setLedColour",
        "colour": colour
    };
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        var json_response = JSON.parse(this.responseText);
        console.log(json_response);

        if (json_response.status == "OK"){
            // reset led indicator to none
            document.getElementById("cled_state").classList.remove("led-on-blue");
            document.getElementById("cled_state").classList.remove("led-on-yellow");
            document.getElementById("cled_state").classList.remove("led-on-green");
            document.getElementById("cled_state").classList.add("led-off");
            // set colour from json array
            if (json_response.cled_states.blue){
                document.getElementById("cled_state").classList.remove("led-off");
                document.getElementById("cled_state").classList.add("led-on-blue");
            }
            if (json_response.cled_states.yellow){
                document.getElementById("cled_state").classList.remove("led-off");
                document.getElementById("cled_state").classList.add("led-on-yellow");
            }
            if (json_response.cled_states.green){
                document.getElementById("cled_state").classList.remove("led-off");
                document.getElementById("cled_state").classList.add("led-on-green");
            }
        }
        else {
            alert("Error setting led colour");
        }

    }
    xhttp.open("POST", "/api", true);
    xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhttp.send(JSON.stringify(jsonData));
}