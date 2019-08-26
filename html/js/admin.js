document.getElementById('adminNav').onclick = function() {
  hideByClass('page');
  showById('admin');
  loadAdmin();
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
  $('#usersTable').DataTable({'paging':false,'info':false,'retrieve':true,'order':[[5, 'desc']]});
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

    // Status
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.status);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Delete
    newcolumn = document.createElement('td');
    newlink = document.createElement('a');
    newlink.setAttribute('href','#');
    newlink.setAttribute('id','deleteUpvote'+value.id);
    newimage = document.createElement('img');
    newimage.setAttribute('src','img/icons/trash.svg');
    newimage.setAttribute('height','24px');
    newlink.appendChild(newimage);
    newcolumn.appendChild(newlink);
    newrow.appendChild(newcolumn);

    document.getElementById('adminUpvotesTableBody').appendChild(newrow);

    document.getElementById("deleteUpvote"+value.id).onclick = function() {
      if(confirm('Delete upvote for '+value.title+'?') == true) {
        deleteUpvote(value.id);
      }
    }
  });
  $('#adminUpvotesTable').DataTable({'order':[[1, 'desc']]});
}

function deleteUpvote(id) {
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
