default: tomato_backend_core_image tomato_web_image

tomato_backend_core_image:
	rsync -aL ../../backend_core/ tomato_backend_core/code/backend_core/ --filter 'merge backend_core-files'
	./build.sh tomato_backend_core

tomato_web_image:
	rsync -aL ../../web/ tomato_web/code/web/ --filter 'merge web-files'
	./build.sh tomato_web
	./build.sh tomato_web
