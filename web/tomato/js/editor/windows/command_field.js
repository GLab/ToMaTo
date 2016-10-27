/*
commandfield: returns a string that wraps the command into a div consisting
 of a read-only input displaying the string, and a copy button.
*/
function commandField(cmd) {
	var id_cmd = "commandfield"+cmd.split(" ")[0]; //fixme: only supports one commandfield per command. better conversion
	return '<div class="input-group" style="width:100%;">'+
	'<input type="text" class="form-control" id="'+id_cmd+'" readonly style="background-color: white; width:100%; cursor:initial; font-family:monospace;" value="'+cmd+'" />'+
	'<span class="input-group-btn">'+
	'<button class="btn btn-secondary" onclick="'+"$('#"+id_cmd+"').select(); document.execCommand('copy'); this.innerHTML='copied!'"+'">'+
	'copy'+
	'</button>'+
	'</span>'+
	'</div>';
}