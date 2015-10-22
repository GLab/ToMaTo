var Profile = Class.extend({
	init: function(options) {
		this.type = options.tech;
		this.name = options.name;
		this.label = options.label || options.name;
		this.restricted = options.restricted;
		this.description = options.description;
		this.diskspace = options.diskspace;
		this.cpus = options.cpus;
		this.ram = options.ram;
	}
});
