//does a blocking ajax call to get the contents of the img directory
function dynimg_getlsfromajax() {
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.open("GET","/img_ls",false);
	xmlhttp.send();
	return JSON.parse(xmlhttp.responseText);
}

var dynimg_ls = null;
//proxy pattern. get the contents of the img directory, and keep it in memory.
function dynimg_getls() {
	if (dynimg_ls==null) {
		dynimg_ls=dynimg_getlsfromajax();
	}
	return dynimg_ls;
}

//check whether a file with a certain name exists inside the server's img directory
function dynimg_imgExists(filename) {
	ls=dynimg_getls();
	for(var i=0; i<ls.length; i++) {
		if (ls[i] == filename) {
			return true;
		}
	}
	return false;
}

//get the url for an image
function dynimg(size,objtype,arg1,arg2) {
	/*
	Uses 2 arguments to build a path to an image file for a specific object type. It then checks whether this image file exists. On success, it redirects to this file. If it does not exist, it redirects to a generic image file for this object type.
	for templates: objtype==openvz|kvmqm|repy  arg1:subtype  arg2:templatename|null  
	for networks:  objtype==network  arg1:kind  arg2:null   
	for vpns:	   objtype==vpn  arg1:kind  arg2:null
	*/
	
	var special_templates = ['floodlight'];
	var special_networks = ["openflow"];
	
	
	
	
	//templates
	if (objtype=="openvz" || objtype=="kvmqm" || objtype=="repy") {
		var subtype=arg1;
		var template_name=arg2;
		
		//non-(repy-network) templates
		if (objtype!="repy" || subtype=="device") {
			var found_templ = false;
			if (template_name!=null) {
				for(var i=0; i<special_templates.length; i++) {
					if (template_name.indexOf(special_templates[i])>-1) {
						found_templ = true;
						template_name=special_templates[i];
					}
				}
			}
			if (found_templ) { //if this is a known template, check whether a fitting file exists and return it if yes.
				var filename=objtype+"_"+template_name+size+".png";
				if (dynimg_imgExists(filename)) {
					return "/img/"+filename;
				}
			}
			//if no file exists for the template, or it hasn't been found, look for a generic file for the subtype.
			var filename = objtype+"_"+subtype+size+".png";
			if (dynimg_imgExists(filename)) {
				return "/img/"+filename;
			}
			//if this also didn't work, return a file for the tech
			return "/img/"+subtype+size+".png";			
		}
		
		//repy-network templates
		else {
			var filename="switch_repy"+size+".png";
			if (dynimg_imgExists(filename)) {
				return "/img/"+filename;
			}
			return "/img/network"+32+".png";
		}
	}
	
	
	
	
	//networks or vpns
	if (objtype=="network" || objtype=="vpn") {
		var kind=arg1;
		var found_kind = false;
		for(var i=0; i<special_networks.length; i++) {
			if (kind.indexOf(special_networks[i])>0) {
				fount_templ = true;
				template_name=special_networks[i];
			}
		}
		if (found_kind) {
			var filename=kind+size+".png"
			if (dynimg_imgExists(filename)) {
				return "/img/"+filename;
			}
		}
		var filename = objtype+size+".png";
		if (dynimg_imgExists(filename)) {
			return "/img/"+filename;
		}
		return "/img/network"+size+".png";
	}
	
	return null;
}
