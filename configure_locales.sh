#!/bin/sh
echo "[!] run this only inside a docker container!"

dpkg-reconfigure locales
echo 'de_DE.UTF-8 UTF-8' > /etc/locale.gen
dpkg-reconfigure locales
