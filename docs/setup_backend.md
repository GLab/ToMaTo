# Backend setup instructions


## Requirements

* docker
* make


## Setup steps

* ``make -C docker/build``
* ```
mkdir -p ~/.tomato; cat > ~/.tomato/tomato-ctl.conf <<EOF
{ 
  "tomato_dir": "$PWD" 
}
EOF
```
* ``alias tomato $PWD/docker/run/tomato-ctl.py``
* ``tomato gencerts``
* ``tomato start``