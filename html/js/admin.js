document.getElementById('adminNav').onclick = function() {
  hideByClass('page');
  showById('admin');
  loadAdmin();
}

document.getElementById('blacklistForm').onsubmit = function() {
  return false;
}

function loadAdmin() {
  username = localStorage.username;
  userhash = localStorage.userhash;

  $.ajax({
    url: "api/admin",
    data: {
      username: username,
      userhash: userhash
    },
    type: "POST"
  }).fail(function(){
    alert('Error loading admin data');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    } else {
      loadAdminUserTable(data['users']);
      loadAdminUpvotesTable(data['upvotes']);
      loadAdminBlacklistTable(data['blacklist']);
      loadAdminDownvotesTable(data['downvotes']);
    }
  });
}

function loadAdminUserTable(users) {
  if ($.fn.DataTable.isDataTable('#usersTable')) {
    $('#usersTable').DataTable().destroy();
  }
  setContentById('usersTableBody','');
  $.each(users,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','user'+value.id);

    // Account
    let newcolumn = document.createElement('td');
    let newcontent = document.createTextNode(value.account);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Curator
    newcolumn = document.createElement('td');
    newcolumn.setAttribute('data-sort',value.curator);
    let icon = '';
    let modicon = '';
    if(value.curator == 1) {
      icon = 'check';
      modicon = 'chevron-bottom';
    } else {
      icon = 'x';
      modicon = 'chevron-top';
    }
    let newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/'+icon+'.svg');
    newimage.setAttribute('height','24px');
    newcolumn.appendChild(newimage);
    newlink = document.createElement('a');
    newlink.setAttribute('href','#');
    newlink.setAttribute('id','switchCuratorStatus'+value.id);
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/'+modicon+'.svg');
    newimage.setAttribute('height','16px');
    newlink.appendChild(newimage);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Delegator
    newcolumn = document.createElement('td');
    newcolumn.setAttribute('data-sort',value.delegator);
    if(value.delegator == 1) {
      icon = 'check';
    } else {
      icon = 'x';
    }
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/'+icon+'.svg');
    newimage.setAttribute('height','24px');
    newcolumn.appendChild(newimage);
    newrow.appendChild(newcolumn);

    // Admin
    newcolumn = document.createElement('td');
    newcolumn.setAttribute('data-sort',value.admin);
    if(value.admin == 1) {
      icon = 'check';
      modicon = 'chevron-bottom';
    } else {
      icon = 'x';
      modicon = 'chevron-top';
    }
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/'+icon+'.svg');
    newimage.setAttribute('height','24px');
    newcolumn.appendChild(newimage);
    newlink = document.createElement('a');
    newlink.setAttribute('href','#');
    newlink.setAttribute('id','switchAdminStatus'+value.id);
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/'+modicon+'.svg');
    newimage.setAttribute('height','16px');
    newlink.appendChild(newimage);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Created
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.created.substring(0,10));
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    newlink = document.createElement('a');
    newlink.setAttribute('href','#');
    newlink.setAttribute('id','deleteUser'+value.id);
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/trash.svg');
    newimage.setAttribute('height','24px');
    newlink.appendChild(newimage);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    document.getElementById('usersTableBody').appendChild(newrow);

    // events
    document.getElementById("switchCuratorStatus"+value.id).onclick = function() {
      if(confirm('Switch curator status of user '+value.account+'?') == true) {
        switchUserStatus('curator',value.id);
      }
    }
    document.getElementById("switchAdminStatus"+value.id).onclick = function() {
      if(confirm('Switch admin status of user '+value.account+'?') == true) {
        switchUserStatus('admin',value.id);
      }
    }
    document.getElementById("deleteUser"+value.id).onclick = function() {
      if(confirm('Delete user '+value.account+'?') == true) {
        switchUserStatus('delete',value.id);
      }
    }
  });
  $('#usersTable').DataTable({'paging':false,'info':false,'order':[]});
}

function switchUserStatus(status,id) {
  $.ajax({
    url: "api/admin",
    data: {
      username: username,
      userhash: userhash,
      switch: status,
      account: id
    },
    type: "POST"
  }).fail(function(){
    alert('Failed switching status');
    loadAdmin();
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    }
    loadAdmin();
  });
}

function loadAdminUpvotesTable(upvotes) {
  if ($.fn.DataTable.isDataTable('#adminUpvotesTable')) {
    $('#adminUpvotesTable').DataTable().destroy();
  }
  setContentById('adminUpvotesTableBody','');
  $.each(upvotes,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','adminupvote'+value.id);

    // Created
    let newcolumn = document.createElement('td');
    let newcontent = document.createTextNode(value.created);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Account
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.account);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // User
    newcolumn = document.createElement('td');
    let newlink = document.createElement('a');
    newlink.setAttribute('href','https://peakd.com/@'+value.user);
    newlink.setAttribute('target','_blank');
    newcontent = document.createTextNode(value.user);
    newlink.appendChild(newcontent);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Title
    newcolumn = document.createElement('td');
    newlink = document.createElement('a');
    newlink.setAttribute('href','https://peakd.com'+value.link);
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

    // Status
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.status);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    if(value.status == 'in queue') {
      newlink = document.createElement('a');
      newlink.setAttribute('href','#');
      newlink.setAttribute('id','adminDeleteUpvote'+value.id);
      newimage = document.createElement('img');
      newimage.setAttribute('src','img/icons/trash.svg');
      newimage.setAttribute('height','24px');
      newlink.appendChild(newimage);
      newcolumn.appendChild(newlink);
    }
    newrow.appendChild(newcolumn);

    document.getElementById('adminUpvotesTableBody').appendChild(newrow);

    if(value.status == 'in queue') {
      document.getElementById("adminDeleteUpvote"+value.id).onclick = function() {
        if(confirm('Delete upvote for '+value.title+'?') == true) {
          adminDeleteUpvote(value.id);
        }
      }
    }
  });
  $('#adminUpvotesTable').DataTable({'order':[]});
}

function adminDeleteUpvote(id) {
  $.ajax({
    url: "api/admin",
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
    loadAdmin();
  });
}

document.getElementById('sendNewBlacklist').onclick = function() {
  $.ajax({
    url: "api/admin",
    data: {
      username: username,
      userhash: userhash,
      blacklist: getValueById('newBlacklist'),
      reason: getValueById('newBlacklistReason')
    },
    type: "POST"
  }).fail(function(){
    alert('Failed adding to blacklist');
    loadAdmin();
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    } else {
      alert('User added to blacklist')
    }
    setValueById('newBlacklist','');
    setValueById('newBlacklistReason','');
    loadAdmin();
  });
}

function loadAdminBlacklistTable(blacklist) {
  if ($.fn.DataTable.isDataTable('#adminBlacklistTable')) {
    $('#adminBlacklistTable').DataTable().destroy();
  }
  setContentById('adminBlacklistTableBody','');
  $.each(blacklist,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','adminblacklist'+value.id);

    // User
    let newcolumn = document.createElement('td');
    let newlink = document.createElement('a');
    newlink.setAttribute('href','https://peakd.com/@'+value.user);
    newlink.setAttribute('target','_blank');
    let newcontent = document.createTextNode(value.user);
    newlink.appendChild(newcontent);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    // Created
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.created);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Reason
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.reason);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Added by
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.account);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    newlink = document.createElement('a');
    newlink.setAttribute('href','#');
    newlink.setAttribute('id','deleteBlacklist'+value.id);
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/trash.svg');
    newimage.setAttribute('height','24px');
    newlink.appendChild(newimage);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    document.getElementById('adminBlacklistTableBody').appendChild(newrow);

    document.getElementById("deleteBlacklist"+value.id).onclick = function() {
      if(confirm('Delete blacklist entry '+value.user+'?') == true) {
        deleteBlacklist(value.id);
      }
    }
  });
  $('#adminBlacklistTable').DataTable({'order':[]});
}

function deleteBlacklist(id) {
  $.ajax({
    url: "api/admin",
    data: {
      username: username,
      userhash: userhash,
      deleteblacklist: id
    },
    type: "POST"
  }).fail(function(){
    alert('Failed deleting blacklist entry');
    loadAdmin();
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    }
    loadAdmin();
  });
}

function loadAdminDownvotesTable(downvotes) {
  if ($.fn.DataTable.isDataTable('#adminDownvotesTable')) {
    $('#adminDownvotesTable').DataTable().destroy();
  }
  setContentById('adminDownvotesTableBody','');
  $.each(downvotes,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','admindownvote'+value.id);

    // Created
    let newcolumn = document.createElement('td');
    let newcontent = document.createTextNode(value.created);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Account
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.account);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Reason
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.reason);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // User
    newcolumn = document.createElement('td');
    let newlink = document.createElement('a');
    newlink.setAttribute('href','https://peakd.com/@'+value.user);
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

    // Limit
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.maxi+' HBD');
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Status
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.status);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    if(value.status == 'wait') {
      newlink = document.createElement('a');
      newlink.setAttribute('href','#');
      newlink.setAttribute('id','adminDeleteDownvote'+value.id);
      newimage = document.createElement('img');
      newimage.setAttribute('src','img/icons/trash.svg');
      newimage.setAttribute('height','24px');
      newlink.appendChild(newimage);
      newcolumn.appendChild(newlink);
    }
    newrow.appendChild(newcolumn);

    document.getElementById('adminDownvotesTableBody').appendChild(newrow);

    if(value.status == 'wait') {
      document.getElementById("adminDeleteDownvote"+value.id).onclick = function() {
        if(confirm('Delete downvote for '+value.title+'?') == true) {
          adminDeleteDownvote(value.id);
        }
      }
    }
  });
  $('#adminDownvotesTable').DataTable({'order':[]});
}

function adminDeleteDownvote(id) {
  $.ajax({
    url: "api/admin",
    data: {
      username: username,
      userhash: userhash,
      deletedownvote: id
    },
    type: "POST"
  }).fail(function(){
    alert('Failed deleting downvote');
    loadAdmin();
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    }
    loadAdmin();
  });
}
