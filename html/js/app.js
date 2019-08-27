var username = '';
var userhash = '';

function appstart() {
  if (localStorage.username) {
    username = localStorage.username;
    userhash = localStorage.userhash;
    login();
  } else {
    showById('about');
    hideByClass('loggedIn');
  }
}

// localStorage.removeItem("username");
appstart();
