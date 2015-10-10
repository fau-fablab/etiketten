etiketten
=========

Automagisierter Etikettendruck für Produkte aus dem [openERP](https://www.odoo.com/) - mit Website.

Installation
------------

```
sudo apt-get install pdftk inkscape php5-json locales
sudo apt-get install python2.7 python-pip python-reportlab python-repoze.lru python-lxml python-pil
sudo pip install oerplib
sudo pip install argcomplete
```

Und die [`config.ini.example`](config.ini.example) nach `config.ini` kopieren und bearbeiten.

[`Dockerfile`](Dockerfile)
--------------------------

 - [`config.ini.example`](config.ini.example) nach `config.ini` kopieren und bearbeiten.
 - `sudo docker build -t php-fablab-etiketten .`
 - `sudo docker run -it --rm --name php-fablab-etiketten-devbox php-fablab-etiketten`
 - `sudo docker inspect php-etiketten-dev | grep `PAddress`
 - Im Browser die IP eintippern und glücklich sein

Achtung
-------

`config.ini` soll nicht welt-lesbar sein, der Webserver muss also sein Webroot im Ordner `public` haben, oder zumindest `htaccess` zulassen. Eine passende [`.htaccess`](.htaccess) liegt schon im Verzeichnis.

Bitte die Funktionsfähigkeit davon ausprobieren, d.h. `config.ini` soll nicht lesbar sein.

Mitarbeiten
-----------

[Infos für Bastler](DEVELOPMENT.md)

Lizenz
------

[unilicense](LICENSE)
