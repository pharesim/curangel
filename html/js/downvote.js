//document.getElementById('downvoteNav').onclick = function() {
//  hideByClass('page');
//  showById('downvote');
//  loadDownvote();
//}

document.getElementById('downvoteForm').onsubmit = function() {
  return false;
}

document.getElementById('sendNewDownvote').onclick = function() {
  hideById('sendNewDownvote');
  showById('sendingDownvote',1);
  $.ajax({
    url: "api/downvote",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash,
      postlink: getValueById('newDownvote'),
      limit: getValueById('newDownvoteLimit'),
      reason: getValueById('newDownvoteReason')
    },
    type: "POST"
  }).fail(function(){
    alert('Error submitting post, please try again');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
      setValueById('newDownvote','');
      setValueById('newDownvoteReason','');
    } else {
      alert('Post will be downvoted soon!');
      setValueById('newDownvote','');
      setValueById('newDownvoteReason','');
      setContentById('downvotesTableBody','');
      loadDownvotesTable(data['downvotes']);
    }
  }).always(function() {
    hideById('sendingDownvote');
    showById('sendNewDownvote',1);
  });
}

function loadDownvote() {
  $.ajax({
    url: "api/downvote",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash
    },
    type: "POST"
  }).fail(function(){
    alert('Error loading downvote data');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
    } else {
      loadDownvotesTable(data['downvotes']);
    }
  });
}

function loadDownvotesTable(downvotes) {
  if ($.fn.DataTable.isDataTable('#downvotesTable')) {
    $('#downvotesTable').DataTable().destroy();
  }
  setContentById('downvotesTableBody','');
  $.each(downvotes,function(index,value) {
    let newrow = document.createElement('tr');
    newrow.setAttribute('id','downvote'+value.id);

    // Created
    let newcolumn = document.createElement('td');
    let newcontent = document.createTextNode(value.created);
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

    // Payout
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.payout);
    newcolumn.appendChild(newcontent);
    newrow.appendChild(newcolumn);

    // Limit
    newcolumn = document.createElement('td');
    newcontent = document.createTextNode(value.maxi + ' HBD');
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
      newlink.setAttribute('id','deleteDownvote'+value.id);
      newimage = document.createElement('img');
      newimage.setAttribute('src','img/icons/trash.svg');
      newimage.setAttribute('height','24px');
      newlink.appendChild(newimage);
      newcolumn.appendChild(newlink);
    }
    newrow.appendChild(newcolumn);

    document.getElementById('downvotesTableBody').appendChild(newrow);

    if(value.status == 'wait') {
      document.getElementById("deleteDownvote"+value.id).onclick = function() {
        if(confirm('Delete downvote for '+value.title+'?') == true) {
          deleteDownvote(value.id);
        }
      }
    }
  });
  $('#downvotesTable').DataTable({'order':[]});
}

function deleteDownvote(id) {
  $.ajax({
    url: "api/downvote",
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
    loadDownvote();
  });
}
