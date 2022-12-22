etiketten
=========

Automagisierter Etikettendruck für Produkte aus dem [openERP](https://www.odoo.com/) - mit Website.

Installation
------------

- vgl. `Dockerfile`
- Wenn man tatsächlich ausdrucken und nicht nur die Vorschau zeigen will, dann muss im noch eine passende CUPS Config hinterlegt werden. Das ist hier im Repo nicht der Fall. (FAU Fablab intern: siehe https://github.com/fau-fablab/brain-docker-config/tree/master/etiketten )


[`Dockerfile`](Dockerfile)
--------------------------

 - `docker-compose down && docker-compose build && docker-compose up`
 - Webbrowser: http://localhost:8080/

Mitarbeiten
-----------

[Infos für Bastler](DEVELOPMENT.md)

Lizenz
------

[unilicense](LICENSE)
