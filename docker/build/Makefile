default: tomato_backend_core_image tomato_backend_users_image tomato_backend_api_image tomato_backend_debug_image tomato_web_image

tomato_service_image:
	./build.sh tomato_service

tomato_backend_api_image: tomato_service_image
	mkdir -p tomato_backend_api/code/service
	rsync -aL ../../backend_api/ tomato_backend_api/code/service/ --filter 'merge backend_api-files'
	./build.sh tomato_backend_api

tomato_backend_core_image: tomato_service_image
	mkdir -p tomato_backend_core/code/service
	rsync -aL ../../backend_core/ tomato_backend_core/code/service/ --filter 'merge backend_core-files'
	./build.sh tomato_backend_core

tomato_backend_users_image: tomato_service_image
	mkdir -p tomato_backend_users/code/service
	rsync -aL ../../backend_users/ tomato_backend_users/code/service/ --filter 'merge backend_users-files'
	./build.sh tomato_backend_users

tomato_backend_debug_image: tomato_service_image
	mkdir -p tomato_backend_debug/code/service
	rsync -aL ../../backend_debug/ tomato_backend_debug/code/service/ --filter 'merge backend_debug-files'
	./build.sh tomato_backend_debug

tomato_web_image:
	mkdir -p tomato_web/code/web
	rsync -aL ../../web/ tomato_web/code/web/ --filter 'merge web-files'
	./build.sh tomato_web
