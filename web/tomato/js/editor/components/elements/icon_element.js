var IconElement = Element.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:32};
		this.busy = false;
		editor.rextfv_status_updater.add(this, 1);
	},
	iconUrl: function() {
		return "img/" + this.data.type + "32.png";
	},
	isMovable: function() {
		return this._super() && !this.busy;
	},
	setBusy: function(busy) {
		this._super(busy);
		this.paintUpdate();
	},
	updateStateIcon: function() {
		
		//set 'host has problems' icon if host has problems
		if (this.data.host_info && this.data.host_info.problems && this.data.host_info.problems.length != 0) {
			this.errIcon.attr({'title':'The Host for this device has problems. Contact an Administrator.'});
			this.errIcon.attr({'src':'/img/error.png'});
		} else {
			this.errIcon.attr({'title':''});
			this.errIcon.attr({'src':'/img/pixel.png'})
		}
		
		if (this.busy) {
			this.stateIcon.attr({src: "img/loading.gif", opacity: 1.0});
			this.stateIcon.attr({title: "Action Running..."});
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
			return;			
		}

		//set state icon
		switch (this.data.state) {
			case "started":
				this.stateIcon.attr({src: "img/started.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Started"});
				break;
			case "prepared":
				this.stateIcon.attr({src: "img/prepared.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Prepared"});
				break;
			case "created":
			default:
				this.stateIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.stateIcon.attr({title: "State: Created"});
				break;
		}
		
		//set RexTFV icon
		if (this.rextfvStatusSupport() && this.data.state=="started") {
			rextfv_stat = this.data.rextfv_run_status;
			if (rextfv_stat.readable) {
				if (rextfv_stat.isAlive) {
					this.rextfvIcon.attr({src: "img/loading.gif", opacity: 1.0});
					this.rextfvIcon.attr({title: "Executable Archive: Running"});
				} else {
					if (rextfv_stat.done) {
						this.rextfvIcon.attr({src: "img/tick.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Done"});
					} else {
						this.rextfvIcon.attr({src: "img/cross.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Unknown. Probably crashed."});
					}
				}
			} else {
				this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.rextfvIcon.attr({title: ""});
			}
		} else {
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
		}
		
	},
	getRectObj: function() {
		return this.rect[0];
	},
	paint: function() {
		var pos = this.canvas.absPos(this.getPos());
		this.icon = this.canvas.image(this.iconUrl(), pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y);
		this.text = this.canvas.text(pos.x, pos.y+this.iconSize.y/2, this.data.name);
		this.stateIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2-10, pos.y+this.iconSize.y/2-15, 16, 16);
		this.errIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2-10, 16, 16);
		this.rextfvIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2+8, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.updateStateIcon();
		//hide icon below rect to disable special image actions on some browsers
		this.rect = this.canvas.rect(pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y + 10).attr({opacity: 0.0, fill:"#FFFFFF"});
		this.enableDragging(this.rect);
		this.enableClick(this.rect);
		this.rect.node.obj = this;
		this.rect.conditionalClass("tomato", true);
		this.rect.conditionalClass("element", true);
		this.rect.conditionalClass("selectable", true);
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	},
	paintRemove: function(){
		this.icon.remove();
		this.text.remove();
		this.stateIcon.remove();
		this.rect.remove();
	},
	paintUpdate: function() {
		if (! this.icon) return;
		var pos = this.getAbsPos();
		this.icon.attr({src: this.iconUrl(), x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.stateIcon.attr({x: pos.x+this.iconSize.x/2-10, y: pos.y+this.iconSize.y/2-15});
		this.errIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2-10});
		this.rextfvIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2+8});
		this.rect.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.text.attr({x: pos.x, y: pos.y+this.iconSize.y/2, text: this.data.name});
		this.updateStateIcon();
		$(this.rect.node).attr("class", "tomato element selectable");
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	}
});
