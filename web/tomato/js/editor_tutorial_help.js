/*
Check whether obj contains all properties of the same value as specified by mask

Example:

compareToMask ( {a:1,b:2} , {a:1} ) == true   (first object has property "a" of value 1)
compareToMask ( {a:1} , {a:1,b:2} ) == false  (first object does not have property "b") 
compareToMask ( {a:1} , {a:2} ) == false      (first object has property "a", but it is of wrong value)
compareToMask ( { x: {a:1, b:2} , y: 4 } , { x: {a:1} } ) == true      (check is done recursively)
*/

function getTutorialData() {
	if (editor != undefined) {
		return editor.workspace.tutorialWindow.getData();
	} else {
		return false;
	}
}

function setTutorialData(data) {
	if (editor != undefined) return editor.workspace.tutorialWindow.setData(data);
}

function compareToMask (obj,mask) {

	//check if both are no objects. If yes, return the result of comparing them
	if (!(obj instanceof Object) && !(mask instanceof Object))
		return obj==mask;
		
	//if one is an object and the other is not, the comparison returns false.
	//(at this point, there is definitely one of them which is an object)
	if (!(obj instanceof Object) || !(mask instanceof Object))
		return false;
	
	//now, for every property in mask, compare it to the same property in obj.
	//(check if the property exists in the object)
	var res = true;
	for (var key in mask) {
		if (!(key in obj))
			return false;
		res = res && compareToMask(obj[key],mask[key]);
    }
	return res;
}


//same as above, but does not check if values are equal:  compareToMask ( {a:1} , {a:2} ) == true
function maskExists (obj,mask) {

	//check if both are no objects. If yes, then it is fulfulled
	if (!(obj instanceof Object) && !(mask instanceof Object))
		return true;
		
	//if one is an object and the other is not, the comparison returns false.
	//(at this point, there is definitely one of them which is an object)
	if (!(obj instanceof Object) || !(mask instanceof Object))
		return false;
	
	//now, for every property in mask, compare it to the same property in obj.
	//(check if the property exists in the object)
	res = true;
	for (var key in mask) {
		if (!(key in obj))
			return false;
		res = res && maskExists(obj[key],mask[key]);
    }
	return res;
}