document.getElementById('downvoteNav').onclick = function() {
  hideByClass('page');
  showById('downvote');
}

document.getElementById('sendNewDownvote').onclick = function() {
  $.ajax({
    url: "api/downvote",
    data: {
      username: localStorage.username,
      userhash: localStorage.userhash,
      postlink: getValueById('newDownvote')
    },
    type: "POST"
  }).fail(function(){
    alert('Error submitting post');
  }).done(function( data ) {
    if(data['error']) {
      alert(data['error']);
      setValueById('newDownvote','');
    } else {
      alert('Post will be downvoted soon!');
      setValueById('newDownvote','');
      setContentById('downvotesTableBody','');
      loadDownvotesTable(data['downvotes']);
    }
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
       loadUpvotesTable(data['downvotes']);
     }
  });
}

function loadDownvotesTable(downvotes) {
  if ($.fn.DataTable.isDataTable('#downvotesTable')) {
    $('#downvotesTable').DataTable().destroy();
  }
  setContentById('downvotesTableBody','');
  $.each(upvotes,function(index,value) {
   let newrow = document.createElement('tr');
   newrow.setAttribute('id','downvote'+value.id);

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

   // Reward
   newcolumn = document.createElement('td');
   newcontent = document.createTextNode(value.reward_sp);
   newcolumn.appendChild(newcontent);
   newrow.appendChild(newcolumn);

   // Status
   newcolumn = document.createElement('td');
   newcontent = document.createTextNode(value.status);
   newcolumn.appendChild(newcontent);
   newrow.appendChild(newcolumn);

   // Reward
   newcolumn = document.createElement('td');
   newcontent = document.createTextNode(value.reward_sp);
   newcolumn.appendChild(newcontent);
   newrow.appendChild(newcolumn);

   // Delete
   newcolumn = document.createElement('td');
   newlink = document.createElement('a');
   newlink.setAttribute('href','#');
   newlink.setAttribute('id','deleteDownvote'+value.id);
   newimage = document.createElement('img');
   newimage.setAttribute('src','img/icons/trash.svg');
   newimage.setAttribute('height','24px');
   newlink.appendChild(newimage);
   newcolumn.appendChild(newlink);
   newrow.appendChild(newcolumn);

   document.getElementById('downvotesTableBody').appendChild(newrow);
 });
 $('#downvotesTable').DataTable({'order':[]});
}
