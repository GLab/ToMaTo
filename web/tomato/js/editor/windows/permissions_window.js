var PermissionsWindow = Window.extend({
	init: function(options) {
		options.modal = true;
		options.close_keep = true;
		
		var t = this;
		this.options = options;
		this.topology = options.topology;
		this.permissions = options.permissions;
		
		this.options.allowChange = this.options.isGlobalOwner;
		
		
		var closebutton = {
		                    	text: "Close",
		                    	id: "permwindow-close-button",
		                    	click: function() {
		                			t.hide();
		                		}
		         
		                    };
		var addbutton = {
		                    	text: "Add User",
		                    	id: "permwindow-add-button",
		                    	click: function() {
		                    		t.addNewUser();
		                    	}
		                    };

		this.options.buttons=[closebutton,addbutton];
		
		
		this._super(this.options);

		
		this.editingList = {};
		
		this.userList = $('<div />');
		this.userListFinder = {};
		this.div.append(this.userList);
		
		this.buttons = $('<div />');
		this.div.append(this.buttons);
		
		this.closeButton = $("#permwindow-close-button");
		this.addButton = $("#permwindow-add-button");
		
	},
	
	disableClose: function() {
		this.closeButton.attr("disabled",true);
		$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).hide();
	},
	enableClose: function() {
		this.closeButton.attr("disabled",false);
		$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).show();
	},
	checkEnableDisableClose: function() {
		var disable = false;
		for (i in this.editingList) {
			disable = disable || this.editingList[i];
		}
		if (disable) {
			this.disableClose();
		} else {
			this.enableClose();
		}
	},
	
	createUserPermList: function() {
		var t = this;
		
		
		if (!this.options.allowChange) {
			this.options.allowChange = (this.topology.data.permissions[this.options.ownUserId] == "owner");
		}
		if (!this.options.allowChange) {
			this.addButton.attr("disabled",true);
		}
		
		
		this.userTable = $('<div />');
		var tableHeader = $('<div class="row"><div class="col-sm-1" /><div class="col-sm-5"><h4>User</h4></div><div class="col-sm-3"><h4>Permission</h4></div><div class="col-sm-3" /></div>');
		this.userTable.append(tableHeader); 
		this.userList.empty();
		this.userList.append(this.userTable);
		var perm = this.topology.data.permissions;
		for (u in perm) {
			if (perm[u] != null)
				this.addUserToList(u);
		}
	},
	
	addUserToList: function(username) {
		var t = this;
		var tr = $('<div class="row" />');
		var td_name = $('<div class="col-sm-5" />');
		var td_perm = $('<div class="col-sm-3" />');
		var td_buttons = $('<div class="col-sm-3" />');
		var td_icon = $('<div class="col-sm-1" />');
	
		
		ajax({
			url:	'account/'+username+'/info',
			successFn: function(data) {
				td_name.append(''+data.realname+' (<a href="/account/info/'+data.id+'" target="_blank" style="font-size:10pt;">'+data.id+'</a>)');
				
				if (data.id == t.options.ownUserId) td_icon.append($('<img src="/img/user.png" title="This is you!" />'));
			}
		});

		tr.append(td_icon);
		tr.append(td_name);
		tr.append(td_perm);
		if (this.options.allowChange) tr.append(td_buttons);
		this.userListFinder[username] = {
				td_icon: td_icon,
				td_name: td_name,
				td_perm: td_perm,
				td_buttons: td_buttons,
				tr: tr
		};
		this.userTable.append(tr);
		
		this.drawView(username);
	},
	
	addNewUser: function() {
		var t = this;
		this.username = new InputWindow({
			title: "New User",
			width: 550,
			height: 200,
			zIndex: 1000,
			inputname: "newuser",
			inputlabel: "Username:",
			infotext: "Please enter the user's username:",
			inputvalue: "",
			buttons: [
						{ 
							text: "Add User",
							click: function() {
								t.username.hide();
								if (t.username.element.getValue() != '') ajax({
									url:	'account/'+t.username.element.getValue()+'/info',
									successFn: function(data) {
										if (!(data.id in t.userListFinder)) {
											if (window.confirm("Found the user "+ data.realname + ' (' + data.id +")\nIs this correct?")) {
												t.addUserToList(data.id);
												t.makePermissionEditable(data.id);
											}
										} else
											showError("This user is already in the list.");
									},
									errorFn: function(error) {
								 		new errorWindow({error:error});
									},
								});
								t.username = null;
							}
						},
						{
							text: "Cancel",
							click: function() {
								t.username.hide();
								t.username = null;
							}
						}
			],
		});
		this.username.show();
	},
	
	removeUserFromList: function(username) {
		this.userListFinder[username].tr.remove();
		this.editingList[username] = false;
		this.checkEnableDisableClose();
		delete this.userListFinder[username];
	},
	
	makePermissionEditable: function(username) {
		if (!this.options.allowChange || this.username == this.options.ownUserId) return;
		
		var t = this;
		td_perm = this.userListFinder[username].td_perm;
		td_buttons = this.userListFinder[username].td_buttons;
		permission = this.topology.data.permissions[username];
		td_perm.empty();
		td_buttons.empty();
		var sel_id='permissions_'+username;
		
		var div = $('<div class="col-sm-10"/>');
		var sel=$('<select name="sel" id="'+sel_id+'"></select>');
		div.append(sel);
		for (perm in this.permissions) {
			if (perm != "null")
				sel.append($('<option value="'+perm+'" title="'+this.permissions[perm].description+'">'+this.permissions[perm].title+'</option>'));
		}
		
		if ((permission == undefined) || (permission == null))
			permission = 'null';
		sel.val(permission);
		sel.change();
		td_perm.append(sel);
		
		var saveButton = $('<img src="/img/tick.png" title="save" style="cursor:pointer;" />');
		saveButton.click(function() {
			var sel = document.getElementById(sel_id);
			var perm = sel.options[sel.selectedIndex].value;
			t.setPermission(username, perm);
		});
		td_buttons.append(saveButton);
		
		var cancelButton = $('<img src="/img/eraser16.png" title="cancel" style="cursor:pointer;" />');
		cancelButton.click(function(){
			t.backToView(username);
		});
		td_buttons.append(cancelButton);
		
		this.editingList[username] = true;
		this.checkEnableDisableClose();
	},
	
	setPermission: function(username, permission) {
		if (!this.options.allowChange || this.username == this.options.ownUserId) return;
		
		var t = this;
		
		var perm_send = null;
		if (permission != 'null')
			perm_send = permission;
		
		ajax({
			url: 'topology/'+this.topology.id+'/permission',
			data: {user: username, permission: perm_send},
			successFn: function(){ 
				if (permission != null) {
					t.topology.data.permissions[username]=permission;
				} else {
					delete t.topology.data.permissions[username];
				}		
				if (perm_send == null) {
					t.removeUserFromList(username)
				} else {
					t.backToView(username);
				}
			},
			errorFn: function(error){
		 		new errorWindow({error:error});
				t.backToView(username);
			}
		})
	},
	
	backToView: function(username) {
		if (username in this.topology.data.permissions && this.topology.data.permissions != null) {
			this.drawView(username);
		} else {
			this.removeUserFromList(username);
		}
	},
	drawView: function(username) {
		var t = this;
		
		var permission = '<div class="hoverdescription">'+this.permissions['null'].title+'</div>';
		if (username in this.topology.data.permissions) {
			permission_var = this.topology.data.permissions[username];
			permission = $('<span title="'+this.permissions[permission_var].description+'">'+this.permissions[permission_var].title+'</span>');
			//permission = $('<div class="hoverdescription">'+this.permissions[permission_var].title+'<div class="hiddenbox"><p>'+ this.permissions[permission_var].description +'</p></div></div>')
		}
		
		var td_perm = this.userListFinder[username].td_perm;
		var td_buttons = this.userListFinder[username].td_buttons;
		td_perm.empty();
		td_buttons.empty();
		
		td_perm.append(permission);
		
		if (username != this.options.ownUserId) {
			var editButton = $('<img src="/img/pencil.png" title="edit permissions" style="cursor:pointer;" />');
			editButton.click(function(){
				t.makePermissionEditable(username);
			});
			td_buttons.append(editButton);
			
			var removeButton = $('<img src="/img/cross.png" title="remove from list" style="cursor:pointer;" />');
			removeButton.click(function(){
				t.setPermission(username,null);
			})
			td_buttons.append(removeButton);
			this.editingList[username] = false;
			this.checkEnableDisableClose();
		}
		
	}
	
	
});
