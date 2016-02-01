default: tomato-backend-image tomato-web-image

tomato-backend-image:
	rsync -aL ../../backend/ tomato-backend/code/backend/ --filter 'merge backend-files'
	./build.sh tomato-backend

tomato-web-image:
	rsync -aL ../../web/ tomato-web/code/web/ --filter 'merge web-files'
	./build.sh tomato-web
