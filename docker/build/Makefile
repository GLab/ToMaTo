default: tomato-backend-image tomato-web-image

tomato-backend-image:
	rsync -aL ../../backend/ tomato-backend/code/ --filter 'merge backend-files'
	./build.sh tomato-backend

tomato-web-image:
	rsync -aL ../../web/ tomato-web/code/ --filter 'merge web-files'
	./build.sh tomato-web
