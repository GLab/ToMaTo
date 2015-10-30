var ConnectionAttributeWindow = AttributeWindow.extend({
	init: function(options, con) {
		options.helpTarget = help_baseUrl+"/editor:configwindow_connection";
		this._super(options);

		var panels = $('<ul class="nav nav-tabs" style="margin-bottom: 1pt;"></ul>');
		this.table.append($('<div class="form-group" />').append(panels));

		var tab_content = $('<div class="tab-content" />');
		if (con.attrEnabled("emulation")) {
			this.emulation_elements = [];
			var t = this;
			var el = new CheckboxElement({
				name: "emulation",
				value: con.data.emulation == undefined ? con.caps.attributes.emulation['default'] : con.data.emulation,
				callback: function(el, value) {
					t.updateEmulationStatus(value);
				}
			});
			this.elements.push(el);
			var link_emulation = $('<div class="tab-pane active" id="Link_Emulation" />');
			link_emulation.append($('<div class="form-group" />')
						.append($('<label class="col-sm-4 control-label">Enabled</label>'))
						.append($('<div class="col-sm-8" style="padding: 0px" />')
						.append(el.getElement())));
			
			//direction arrows
			var size = 30;
			var _div = '<div style="width: '+size+'px; height: '+size+'px;"/>';
			var dir1 = $(_div); var dir2 = $(_div);
			var canvas1 = Raphael(dir1[0], size, size);
			var canvas2 = Raphael(dir2[0], size, size);
			var _path1 = "M 0.1 0.5 L 0.9 0.5";
			var _path2 = "M 0.7 0.5 L 0.4 0.3 M 0.7 0.5 L 0.4 0.7";
			var _transform1 = "R"+con.getAngle()+",0.5,0.5S"+size+","+size+",0,0";
			var _transform2 = "R"+(con.getAngle()+180)+",0.5,0.5S"+size+","+size+",0,0";
			var _attrs = {"stroke-width": 2, stroke: "red", "stroke-linecap": "round", "stroke-linejoin": "round"};
			canvas1.path(_path1).transform(_transform1);
			canvas1.path(_path2).transform(_transform1).attr(_attrs);
			canvas2.path(_path1).transform(_transform2);
			canvas2.path(_path2).transform(_transform2).attr(_attrs);
			var name1 = con.elements[0].name();
			var name2 = con.elements[1].name();
			if (con.elements[0].id > con.elements[1].id) {
				var t = name1;
				name1 = name2;
				name2 = t;
			}
			var fromDir = $("<div>From " + name1 + "<br/>to " + name2 + "</div>");
			var toDir = $("<div>From " + name2 + " <br/>to " + name1 + "</div>");
			link_emulation.append($('<div class="form-group" />')
				.append($('<label class="col-sm-4 control-label">Direction</label>'))
				.append($('<div class="col-sm-4" />').append(fromDir).append(dir1))
				.append($('<div class="col-sm-4" />').append(toDir).append(dir2))
			);
			//simple fields
			var order = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "duplicate", "corrupt"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var info_from = con.caps.attributes[name+"_from"];
				info_from.name = name + "_from";
				var el_from = this.autoElement(info_from, con.data[name+"_from"], true)
				this.elements.push(el_from);
				this.emulation_elements.push(el_from);
				var info_to = con.caps.attributes[name+"_to"];
				info_to.name = name + "_to";
				var el_to = this.autoElement(info_to, con.data[name+"_to"], true)
				this.elements.push(el_to);
				this.emulation_elements.push(el_to);
				link_emulation.append($('<div class="form-group" />')
					.append($('<label class="col-sm-4 control-label" style="padding: 0;" />').append(con.caps.attributes[name+"_to"].label))
					.append($('<div class="col-sm-3" style="padding: 0;"/>').append(el_from.getElement()))
					.append($('<div class="col-sm-3" style="padding: 0;" />').append(el_to.getElement()))
					.append($('<div class="col-sm-2" style="padding: 0;" />').append(con.caps.attributes[name+"_to"].value_schema.unit))
				);
			}
			this.updateEmulationStatus(con.data.emulation);
			
			tab_content.append(link_emulation);
			this.table.append(tab_content);
			panels.append($('<li class="active"><a href="#Link_Emulation" data-toggle="tab">Link Emulation</a></li>'));
		}
		if (con.attrEnabled("capturing")) {
			var t = this;
			var packet_capturing = $('<div class="tab-pane" id="Packet_capturing" />');
			
			this.capturing_elements = [];
			var el = new CheckboxElement({
				name: "capturing",
				value: con.data.capturing,
				callback: function(el, value) {
					t.updateCapturingStatus(value);
				}
			});
			this.elements.push(el);
			packet_capturing.append($('<div class="form-group" />')
					.append($('<label class="col-sm-6 control-label">Enabled</label>'))
					.append($('<div class="col-sm-6" />')
					.append(el.getElement())));

			var order = ["capture_mode", "capture_filter"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var info = con.caps.attributes[name];
				info.name = name;
				var el = this.autoElement(info, con.data[name], con.attrEnabled(name));
				this.capturing_elements.push(el);
				this.elements.push(el);
				packet_capturing.append($('<div class="form-group" />')
					.append($('<label class="col-sm-6 control-label">').append(con.caps.attributes[name].label))
					.append($('<div class="col-sm-6" />').append(el.getElement()))
				);
			}
			this.updateCapturingStatus(con.data.capturing);

			tab_content.append(packet_capturing);
			this.table.append(tab_content);
			panels.append($('<li><a href="#Packet_capturing" data-toggle="tab">Packet capturing</a></li>'));
		}
	},
	updateEmulationStatus: function(enabled) {
		for (var i=0; i<this.emulation_elements.length; i++)
			 this.emulation_elements[i].setEnabled(enabled);
	},
	updateCapturingStatus: function(enabled) {
		for (var i=0; i<this.capturing_elements.length; i++)
			 this.capturing_elements[i].setEnabled(enabled);
	}
});
