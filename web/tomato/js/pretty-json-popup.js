/* ToMaTo (Topology management software) 
# Copyright (C) 2015 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>. */


function pretty_json_popup(obj,title,filename) {
	var div = $('<div></div>');
	new PrettyJSON.view.Node({
		data: obj,
		el: div
	});
	div.dialog({autoOpen: true,
				draggable: false,
				resizable: false,
				position: { my: "center center", at: "center top", of: "#content"},
				width: "60%",
				title: title,
				modal: true,
				buttons: [
				           {
				        	text: 'Close', 
				        	click: function(){div.remove();}
				           },
				           {
				        	text: 'Download', 
				        	click: function(){
				        		window.open('data:text/plain,'+JSON.stringify(obj))
				        		}
				           }
					]
				});
}