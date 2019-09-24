document.getElementById('upvoteNav').onclick = function() {
  hideByClass('page');
  showById('upvote');
  loadUpvote();
}

document.getElementById('upvoteForm').onsubmit = function() {
  return false;
}

document.getElementById('checkMana').onclick = function() {
  $.ajax({
    url: "api/mana",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash,
      account: localStorage.username
    },
    type: "POST"
  }).fail(function(){
    alert('Error checking mana');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    } else {
      var mana = parseInt(data['mana']);
      var stamina_bar = parseFloat(data['stamina']['value']);
      var stamina_step = parseInt(data['stamina']['step']);
      var max_mana = 43200000000;
      var mana_pct = (mana / max_mana) * 100;
      var to_recharge_full = (stamina_step + 1) - stamina_bar;
      var to_recharge_bar = 1 - stamina_bar;
      var current_pct = 100 - (15 * stamina_step);
      var hours_per_bar = 3;
      var output = "";
      output += "Mana: " + mana_pct.toString() + "%\n";
      output += "Stamina: -" + to_recharge_full.toString() + "\n";
      output += "Current max vote weight: " + current_pct.toString() + "%\n";
      if (current_pct < 100) {
        var bar_recharge_minutes = to_recharge_bar * hours_per_bar * 60;
        output += "Max vote weight increases in: " + bar_recharge_minutes.toString() + " minutes";
      }
      alert(output);
    }
  });
}

document.getElementById('sendNewUpvote').onclick = function() {
  $.ajax({
    url: "api/upvote",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash,
      postlink: getValueById('newUpvote')
    },
    type: "POST"
  }).fail(function(){
    alert('Error submitting post');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
      setValueById('newUpvote','');
    } else {
      alert('Post successfully added to upvote queue');
      setValueById('newUpvote','');
      setContentById('upvotesTableBody','');
      loadUpvotesTable(data['upvotes']);
    }
  });
}

function loadUpvote() {
  $.ajax({
    url: "api/upvote",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash
    },
    type: "POST"
  }).fail(function(){
    alert('Error loading upvote data');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    } else {
      loadUpvotesTable(data['upvotes']);
    }
  });
}

function loadUpvotesTable(upvotes) {
  if ($.fn.DataTable.isDataTable('#upvotesTable')) {
    $('#upvotesTable').DataTable().destroy();
  }
  setContentById('upvotesTableBody','');
  $.each(upvotes,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','upvote'+value.id);

    // Created
    let newcolumn = document.createElement('td');
    let newcontent = document.createTextNode(value.created);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // User
    newcolumn = document.createElement('td');
    let newlink = document.createElement('a');
    newlink.setAttribute('href','https://steemit.com/@'+value.user);
    newlink.setAttribute('target','_blank');
    newcontent = document.createTextNode(value.user);
    newlink.appendChild(newcontent);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Title
    newcolumn = document.createElement('td');
    newlink = document.createElement('a');
    newlink.setAttribute('href','https://steemit.com'+value.link);
    newlink.setAttribute('target','_blank');
    if(value.title == '') {
      value.title = 'None';
    }
    newcontent = document.createTextNode(value.title);
    newlink.appendChild(newcontent);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Type
    newcolumn = document.createElement('td');
    let type = 'comment'
    if(value.type == 1) {
      type = 'post';
    }
    newcontent = document.createTextNode(type);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Payout
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.payout);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Status
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.status);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Reward
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.reward_sp+' SP');
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    if(value.status == 'in queue') {
      newlink = document.createElement('a');
      newlink.setAttribute('href','#');
      newlink.setAttribute('id','deleteUpvote'+value.id);
      newimage = document.createElement('img');
      newimage.setAttribute('src','img/icons/trash.svg');
      newimage.setAttribute('height','24px');
      newlink.appendChild(newimage);
      newcolumn.appendChild(newlink);
    }
    newrow.appendChild(newcolumn);

    document.getElementById('upvotesTableBody').appendChild(newrow);

    if(value.status == 'in queue') {
      document.getElementById("deleteUpvote"+value.id).onclick = function() {
        if(confirm('Delete upvote for '+value.title+'?') == true) {
          deleteUpvote(value.id);
        }
      }
    }
  });
  $('#upvotesTable').DataTable({'order':[]});
}

function deleteUpvote(id) {
  $.ajax({
    url: "api/upvote",
    data: {
      username: username,
      userhash: userhash,
      deleteupvote: id
    },
    type: "POST"
  }).fail(function(){
    alert('Failed deleting upvote');
    loadAdmin();
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    }
    loadUpvote();
  });
}
