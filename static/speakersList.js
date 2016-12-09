/**
 * speakersList.js
 * 
 * Pedro Luis Cunha Farias
 * pfarias@college.harvard.edu
 * 
 * Scripts for updating the speakers list & timer.
 */

var speakers = [];
var timing;
var firstSpeaker = true;
var alarm = new Audio("static/gentle-alarm.mp3");

/**
 * Called when the window loads
 */
window.onload = function() 
{
  getSpeakersList();
  writeSpeakersList();
};

/**
 * Starts & updates timer.
 * Function derived from: http://jsfiddle.net/wr1ua0db/17/
 */
function startTimer(duration, display) 
{
  var timer = duration, minutes, seconds;
  timing = setInterval(function () 
  {
    // calculate correct number of min & seconds
    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);

    // add extra "0" if single digits to maintain format
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    display.textContent = minutes + ":" + seconds;

    // once timer has expired
    if (timer-- <= 0)
    {
      // update speaker's list and start timer
      writeSpeakersList();
      alarm.play()
      clearInterval(timing);
    }
  }, 1000);
}

/**
 * Called when user presses "Start Timer".
 * Starts and displays timer and displays.
 */
function updateSpeakingTime()
{
  var time = document.getElementById("speakingTime").value,
  display = document.querySelector('#timer');
  
  // only do this if this isn't first speaker to be added to list
  if (!firstSpeaker)
  {
    clearInterval(timing);
    speakers.shift();
    writeSpeakersList();
  }
  else
  {
    firstSpeaker = false;
  }
  // update db by calling quickup() (backend: adds +1 speeches)
  $.ajax({
    method: "POST",
    url: '/quickup?name=' + speakers[0] + '&info=speeches&curVal=1&up=1'
  }).done(function() {
    console.log("Speaker added, speeches column updated by +1.")
  }).fail(function() {
    console.log("There was an error, speeches column NOT updated.")
  });
  startTimer(time, display);
}

/**
 * Called when user presses "Add".
 * Updates speakers list and database with added speech.
 */
function addSpeaker()
{
  // add to speakers array if there is one
  var delName = document.getElementById("speakerInput").value.toUpperCase();
  if (delName == "")
  {
    return false;
  }
  speakers.push(delName);
  writeSpeakersList();
  
   document.getElementById("speakerInput").value = "";
  // prevents form from submitting
  return false;
}

/**
 * Writes the speakers list to the webpage.
 */
function writeSpeakersList()
{
  var len = speakers.length;
  var speakersList = "";
  var csvSpeakers = "";
  
  // update the current speaker if any
  var currSpeaker = len == 0 ? "None" :
    '<p style="font-family:candara;margin:0; padding:0"><font size="4">'
    + speakers[0] + '</font></p>';
    
  document.getElementById("currSpeaker").innerHTML = currSpeaker;
  
  // iterate through each speaker & write its HTML
  for (var i = 1; i < len; i++)
  {
    speakersList += '<p style="font-family:candara;margin:0; padding:0"><font size="4">'
     + i + ') '  + speakers[i] + '</font></p>';
     csvSpeakers += speakers[i] + ",";
  }
  
  // display speakers list on page && save in storage
  var list = document.getElementById("speakersList");
  if (len != 0)
  {
    setSpeakersList(csvSpeakers);
  }
  list.innerHTML = speakersList;
}

/**
 * Clears speakers list & removes any speeches they didn't give.
 */
function clearSpeakersList()
{
  // clear list & memory
  speakers = [];
  setSpeakersList("");
  writeSpeakersList();
}

/**
 * Saves speakers list to local memory
 */
function setSpeakersList(str)
{
    localStorage.savedList = str;
}

/**
 * Gets speakers list from local memory
 */
function getSpeakersList()
{
  str = localStorage.savedList;
  cur = ""
  
  // parse string & add to delegation list
  for(var i = 0, len = str.length; i < len; i++)
  {
    // skip spaces outide words
    if (str.charAt(i) == " " && cur == "")
    {
      continue;
    }
    // new delegation found
    else if (str.charAt(i) == ",")
    {
      speakers.push(cur);
      cur = "";
    }
    else
    {
      cur += str.charAt(i);
    }
  }
}