jQuery(function ($) {
	$('.ui-button').button({ useSlidingDoors: true });
});
$("#menu div>button").addClass("ui-ribbon-large-button").addClass("ui-ribbon-element").addClass("ui-ribbon-control").addClass("ui-button");
$("#menu li>button").addClass("ui-ribbon-simple-button").addClass("ui-ribbon-element").addClass("ui-ribbon-control").addClass("ui-button");
$("#menu").ribbon();
$("#menuBtnUsage").click(function(){
  window.open('/topology/'+top_id+'/usage', '_blank', 'innerHeight=450,innerWidth=600,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
});
function setMode(mode) {
  $("#menuTabHomeGroupModes button").button("option", "checked", false);
  switch (mode) {
  	case "select": $("#menuBtnSelect").button("option", "checked", true); break;
  	case "move": $("#menuBtnMove").button("option", "checked", true); break;
  	case "connect": $("#menuBtnConnect").button("option", "checked", true); break;
  	case "delete": $("#menuBtnDelete").button("option", "checked", true); break;
  }
}
$("#menuBtnSelect").click(function(){
  setMode("select");
});
$("#menuBtnMove").click(function(){
  setMode("move");
});
$("#menuBtnConnect").click(function(){
  setMode("connect");
});
$("#menuBtnDelete").click(function(){
  setMode("delete");
});