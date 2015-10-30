var createComponentMenu = function(obj) {
	switch (obj.component_type) {
		case "element":
			return createElementMenu(obj);
		case "connection":
			return createConnectionMenu(obj);
	}
};
