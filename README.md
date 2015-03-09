etiketten
=========

Automagisierter Etikettendruck für Produkte aus dem [openERP](https://www.odoo.com/) - mit Website.

Installation
------------

```
sudo apt-get install python-pip pdftk inkscape python-reportlab python-repoze.lru
sudo pip install oerplib
sudo pip install argcomplete
```

Und die [`config.ini.example`](config.ini.example) nach `config.ini` kopieren und bearbeiten.

Achtung
-------

`config.ini` soll nicht welt-lesbar sein, der Webserver muss also `htaccess` zulassen. Eine passende [`.htaccess`](.htaccess) liegt schon im Verzeichnis.

Lizenz
------

[unilicense](LICENSE)
