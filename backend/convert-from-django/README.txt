Step 1: Export postgresql database
# sudo -u tomato pg_dump -c tomato > tomato.sql

Step 2: Import postgresql database into development system
# echo "drop schema public cascade;create schema public;" | psql tomato
# psql tomato < tomato.sql

Step 3: Dump the database
# git checkout django-backend
# ./manage dumpdata tomtato > tomato.json
# git checkout master

Step 4: Convert the database
# tomato-backend-shell
# pip install ujson
# /code/convert-from-django/convert.sh FILE