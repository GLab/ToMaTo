
var RexTFV_status_updater = Class.extend({
	init: function(options) {
		this.options = options;
		this.elements = [];
	},
	updateFirst: function(t) { //Takes RexTFV_status_updater as argument.
	    entry = t.elements.shift();
        elExists = true;
        mustRemove = false;

        if (entry.element in editor.topology.elements) { //element exists
            editor.topology.elements[entry.element].update(undefined, undefined, true) //hide errors.
        } else {
            elExists = false;
        }

        if (elExists &&
            editor.topology.elements[entry.element].rextfvStatusSupport() &&
			editor.topology.elements[entry.element].data.rextfv_run_status.running) {
			    entry.tries = 1;
		} else {
    		entry.tries--;
    		mustRemove = (entry.tries < 0)
		}

		if (!mustRemove) t.elements.push(entry)
	},
	updateSome: function(t) { //this should be called by a timer. Takes RexTFV_status_updater as argument.
		                      //update only the first five elements of the array. This boundary is to avoid server overload.
		var count = 5;
        if (t.elements.length < count) count = t.elements.length; //do not update elements twice.
		while (count-- > 0) t.updateFirst(t);
	},
	updateAll: function(t) { //this should be called by a timer. Takes RexTFV_status_updater as argument.
		toRemove = [];
		//iterate through all entries, update them, and then update their retry-count according to the refreshed data.
		//do not remove elements while iterating. instead, put to-be-removed entries in the toRemove array.
		for (var i=0; i<t.elements.length; i++) {
			entry = t.elements[i];
			success = true;
			if (entry.element in editor.topology.elements) {
				editor.topology.elements[entry.element].update(undefined, undefined, true); //hide errors.
			} else {
				success = false;
			}
			if (success && 
				editor.topology.elements[entry.element].rextfvStatusSupport() &&
				editor.topology.elements[entry.element].data.rextfv_run_status.running) {
					entry.tries = 1;
			} else {
				entry.tries--;
				if (entry.tries < 0) {
					toRemove.push(entry)
				}
			}
		}
		//remove entries marked as to-remove.
		for (var i=0; i<toRemove.length; i++) {
			t.remove(toRemove[i]);
		}
	},
	add: function(el,tries) { //every entry has a number of retries and an element ID attached to it.
								// retries are decreased when the status is something else than "running" (i.e., done, no RexTFV support, etc.).
								// the idea is that the system might need some time to detect RexTFV activity after uploading the archive or starting a device.
								// retries are set to 1 if the status is "running".
								// retries == 1 is the default. if retries < 0, the entry is removed. This means, after the status is set to "not running",
								// the editor will update the element twice before removing it.
		

		//first, search whether this element is already monitored. If yes, update number of tries if necessary (keep the bigger one). exit funciton if found.
		for (var i=0; i<this.elements.length; i++) {
			if (this.elements[i].element == el.id) {
				if (this.elements[i].tries < tries)
					this.elements[i].tries = tries;
				return
			}
		}
		//if the search hasn't found anything, simply append this.
		this.elements.push({
			element: el.id,
			tries: tries
		})
	},
	// usually only called by this. removes an entry.
	remove: function(entry) {
		for (var i=0; i<this.elements.length; i++) {
			entry_found = this.elements[i];
			if (entry_found == entry) {
				this.elements.splice(i,1);
				return;
			}
		}
	}
});
