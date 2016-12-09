/**
 * forms.js
 * 
 * Pedro Luis Cunha Farias
 * pfarias@college.harvard.edu
 * 
 * Toogles delegate options on and off.
 */

/**
 * Shows input options for delegate's login and registration.
 */
function delOptions() {
  // retrieve necessary HTML
  var isChecked = document.getElementById("delCheck").checked;
  var div = document.getElementById('delOpts');

  console.log("called");
  // if checked, show del options
  changeVisibility(isChecked, div);
}

/**
 * Shows which fields are required
 */
function requiredInput(ref, toChange){
  // retrieve necessary HTML
  var input = document.getElementById(ref).value;
  var text = document.getElementById(toChange);

  // if blank, show "required input" message
  changeVisibility(input == "", text)
}

/**
 * Checks if input in both fields match.
 */
function checkMatch(passRef,confRef, toChange)
{
  var pass = document.getElementById(passRef).value;
  var conf = document.getElementById(confRef).value;
  var text = document.getElementById(toChange);

  // if don't match, show "required input" message
  changeVisibility(pass != conf, text)
}

/**
 * Changes visibility of a field dependent on a condition
 */
function changeVisibility(condition, field){
  // if condition, show visibility
  if (condition) {
    field.setAttribute('style','visibility:visible');
  }
  else {
    field.setAttribute('style','visibility:hidden');
  }
}