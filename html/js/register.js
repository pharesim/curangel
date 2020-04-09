document.getElementById('registerNav').onclick = function() {
  hideByClass('page');
  showById('register');
}

document.getElementById('registerNow').onclick = function() {
  let regUser = getValueById('registerUsername');
  let regKey  = getValueById('registerPostingKey');
  if(!steem.auth.isWif(regKey)) {
    regKey = steem.auth.toWif(regUser, regKey, 'posting');
  }

  let pub = steem.auth.wifToPublic(regKey);
  steem.api.setOptions({ url: 'https://api.pharesim.me' });
  steem.api.getAccounts([regUser], function(err, result) {
    let keys = result[0]['posting']['key_auths'];
    for (var i = 0; i < keys.length; i++) {
      if(keys[i][0] == pub) {
        username = result[0]['name'];
        userhash = Sha256.hash("username"+regKey+"curangel");
        register();
      }
    }

    if(username == '') {
      registerError('Registration failed, wrong key for the specified user!');
    }
  });
}

document.getElementById('loginFromRegister').onclick = function() {
  hideByClass('page');
  showById('loggedOut');
}

function register() {
  $.ajax({
    url: "api/register",
    data: {
      username: username,
      userhash: userhash
    },
    type: "POST"
  }).fail(function(){
    registerError('Registration failed, please try again');
  }).done(function( data ) {
    if(data['error']) {
      registerError(data['error']);
    } else {
      hideById('registerError');
      hideById('registerForm');
      showById('registerSuccess');
    }
  });

  userhash = '';
}

function registerError(message) {
  setContentById('registerError',message);
  showById('registerError');
}
