/*
# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

function loadbusy(evt,message) {
	if (evt && evt.button == 1) return;
	var busyloader = $('\
			<div style="background:#c0c0c0;\
						filter:alpha(opacity=75); /* IE */ \
						-moz-opacity: 0.75; /* Mozilla */ \
						opacity: 0.75; /* Opera */ \
						position:absolute;\
						top:0;\
						left:0;\
						width:' + Math.max($(document).width(),$(window).width(),/* For opera: */document.documentElement.clientWidth) + 'px;\
						height:' + Math.max($(document).height(),$(window).height(),/* For opera: */document.documentElement.clientHeight) + 'px;\
						z-index:11;">\
						</div>\
				<div class="panel panel-default" style="background:white;\
					position:absolute;\
					top: 35%;\
					left: 35%;\
					font-size: 30px;\
					text-align:center;\
					z-index:12;">\
					<div class="panel-body"><h1>'+message+'</h1><img src="/img/loading_big.gif" alt="loading..."/>\</div>\
				</div>\
			');
	$('body').append(busyloader);
	window.scrollTo(0,0);
}


//preload the loading gif image
$(document).ready(
		function() {
			$('body').append($('<img src="/img/loading_big.gif" class="preload"/>'));
		}
	);