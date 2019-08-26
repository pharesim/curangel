function loadTemplate(template,container) {
  jQuery.ajaxSetup({ async: false });
  $.get('templates/'+template+'.html', '', function (data) {
    let elem = document.getElementById(container);
    elem.innerHTML = data+elem.innerHTML;
  });
  jQuery.ajaxSetup({ async: true });
}

loadTemplate('loggedout','content');
loadTemplate('register','content');
loadTemplate('admin','content');
loadTemplate('upvote','content');
loadTemplate('downvote','content');
loadTemplate('about','content');
loadTemplate('blacklist','content');
/* loadTemplate('index/loggedin','content');
loadTemplate('index/modals/freeclaim','body');
loadTemplate('index/modals/botclaim','body');
loadTemplate('index/modals/paidclaim','body');
loadTemplate('index/modals/invite','body');
loadTemplate('index/modals/create','body'); */
