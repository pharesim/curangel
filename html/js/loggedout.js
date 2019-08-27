document.getElementById('loginNav').onclick = function() {
  hideByClass('page');
  showById('loggedOut');
}

document.getElementById('logoutNav').onclick = function() {
  localStorage.removeItem('username');
  localStorage.removeItem('userhash');
  window.location.href = '/';
}

document.getElementById('loginNow').onclick = function() {
  let loginUser = getValueById('loginUsername');
  let loginKey  = getValueById('loginPostingKey');
  if(steem.auth.isWif(loginKey)) {
    loginKey = loginKey;
  } else {
    loginKey = steem.auth.toWif(loginUser, loginKey, 'posting');
  }

  let pub = steem.auth.wifToPublic(loginKey);
  steem.api.getAccounts([loginUser], function(err, result) {
    let keys = result[0]['posting']['key_auths'];
    for (var i = 0; i < keys.length; i++) {
      if(keys[i][0] == pub) {
        username = result[0]['name'];
        userhash = Sha256.hash("username"+loginKey+"curangel");
        login();
      }
    }

    if(username == '') {
      loginError('Login failed, please check your credentials');
    }
  });
}

function login() {
  $.ajax({
     url: "api/login",
     data: {
       username: username,
       userhash: userhash
     },
     type: "POST"
   }).fail(function(){
     loginError('Login failed, please try again');
   }).done(function( data ) {
     if(data['error']) {
       username = '';
       userhash = '';
       loginError(data['error']);
     } else {
       localStorage.setItem("username", username);
       localStorage.setItem("userhash", userhash);
       hideById('loginError');
       hideByClass('page');
       hideByClass('loggedOut');
       showByClass('loggedIn');
       if(data['admin'] == 1) {
         showById('adminNav');
         loadAdmin();
         showById('admin');
       }
       if(data['curator'] == 1) {
         showById('upvoteNav');
         if(data['admin'] != 1) {
           showById('upvote');
         }
       }
       if(data['delegator'] == 1) {
         showById('downvoteNav');
         if(data['admin'] != 1 && data['curator'] != 1) {
           showById('downvote');
         }
       }
     }
   });
}

function loginError(message) {
  setContentById('loginError',message);
  showById('loginError');
}
