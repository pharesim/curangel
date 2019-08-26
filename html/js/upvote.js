document.getElementById('upvoteNav').onclick = function() {
  hideByClass('page');
  showById('upvote');
  loadUpvote();
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
   newcontent = document.createTextNode(value.reward_sp+' SP; '+value.reward_sbd+' SBD');
   newcolumn.appendChild(newcontent);
   newrow.appendChild(newcolumn);

   document.getElementById('upvotesTableBody').appendChild(newrow);
 });
 $('#upvotesTable').DataTable({'order':[]});
}
