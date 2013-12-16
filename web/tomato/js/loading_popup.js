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

function loadbusy() {
	var busyloader = $('\
			<div style="background:#c0c0c0;\
						filter:alpha(opacity=80); /* IE */ \
						-moz-opacity: 0.80; /* Mozilla */ \
						opacity: 0.80; /* Opera */ \
						position:absolute;\
						top:0;\
						left:0;\
						width:' + Math.max($(document).width(),$(window).width(),/* For opera: */document.documentElement.clientWidth) + 'px;\
						height:' + Math.max($(document).height(),$(window).height(),/* For opera: */document.documentElement.clientHeight) + 'px;\
						z-index:11;">\
						</div>\
				<div style="background:white;\
					border: 1px solid black;\
					padding: 1cm;\
					position:absolute;\
					top: 50%;\
					left: 50%;\
					width:400px;\
					height:150px;\
					margin-top:-75px;\
					margin-left: -200px;\
					font-size: 30px;\
					text-align:center;\
					z-index:12;">\
					<p>Loading Topology Editor...</p>\
					<img src="/img/loading_big.gif" alt="loading..."/>\
				</div>\
			');
	$('body').append(busyloader);
}