#!/bin/bash

# cut
convert ToMaTo\ Logo\ Text\ Large.png +repage -crop 0x0-100+0 ../../web/tomato/img/logo_1.png
convert ToMaTo\ Logo\ Text\ Large.png -crop +637x0+50+0 /tmp/tomato_logo_tmp.png
convert /tmp/tomato_logo_tmp.png -crop 0x0-99%+0 ../../web/tomato/img/logo_2.png
convert ToMaTo\ Logo\ Text\ Large.png -crop +707x0+50+0 ../../web/tomato/img/logo_3.png
rm /tmp/tomato_logo_tmp.png

# scale
for i in 1 2 3; do
	convert ../../web/tomato/img/logo_${i}.png -scale x80 ../../web/tomato/img/logo_${i}.png
done

