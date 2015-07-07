default: tomato-backend-image

tomato-backend-image:
	rsync -aL ../../backend/ tomato-backend/code/ --filter 'merge backend-files'
	./build.sh tomato-backend
