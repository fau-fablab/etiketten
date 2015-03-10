DEVELOPMENT INFORMATION
=======================

Ein paar Infos, die es leichter machen sollen, sich in das Projekt hinein zu denken.

Funktionsweise:
---------------

 - PHP / HTML Frontend (CSS kommt vom [macgyver](https://macgyver.fablab.fau.de/~ev80uhys/web/faufablab-light.css),
 ist ein [Git](https://github.com/fau-fablab/website-style) und darf bearbeitet werden)
   - [`index.php`](index.php)
   - [`.htaccess`](.htaccess): damits sicher ist
   - Daten werden über `POST` herum geschaufelt.
 - Python Backend:
   - [`svgtemplate.py`](svgtemplate.py): Holt Daten aus dem OpenERP und erstellt daraus Etiketten
     - [`vorlage-etikettenpapier`](vorlage-etikettenpapier.svg): Template für ein Etikett
     - [`config.ini`](config.ini): OpenERP Einstellungen
   - [`textlabel.py`](textlabel.py): Erstellt Freitext Etiketten mit maximaler Schriftgröße
 - Daten gelangen über `system commands` vom PHP zum Python

Schema:
-------

```
-> index.php
   |-wurden Daten hingeposted / soll was getan werden? ($_POST["action"])
     |- nein: Zeige Eingabe Formular ∎
     |- ja:
        |- muss der Etiketten-Eingabe-String verarbeitet werden? ($_POST["etiketten"] && ...) -> verarbeiten
        |- was muss getan werden? ($action)
           |- 'select': Zeige eine Tabelle, bei der man die Anzahl pro Label auswählen kann (Schritt davor war das Zeigen des Eingabeformulars)
           |  |- Daten kommen als json per stdout von svgtemplate.py --no-label ∎
           |- 'print-selection': Drucke die Etiketten mit der ausgewählten Anzahl aus (Schritt davor war 'select')
           |  |- Daten könnte man als json per stdin an svgtemplate.py weiterreichen, dass man diese nicht mehr vom ERP holen muss ∎
           |- generiere Etiketten (SVG->PDF)
           |  |- generiert wird mit svgtemplate.py
           |- 'print': Etiketten wurden entweder im php oder in 'textlabel.py' gedruckt -> Meldung ∎
           |- sonst: zeige Etiketten PDF ∎


```

`POST` Felder:
--------------

 - `action`: was soll mit der Eingabe getan werden:
    - `print`: Etikett erstellen und drucken
    - `select`: Anzahl der Etiketten auswählen
    - `print-selection`: Etiketten mit ihrer Anzahl erstellen und drucken
 - `etiketten`: Wert des Produkt ID / Purchase Order ID Eingabe Feldes ODER Wert des Freitext Eingabe Feldes
 - `type`: Art der zu druckenden Etiketten:
    - `small`: kleine Etiketten (standard und fix für ERP Etiketten)
    - `large`: große Etiketten (deaktiviert)
    - `text`: Freitext
 - `startposition`: Wurde früher gebraucht, um das erste Etikett auf einem Bogen festzulegen, heute fest auf 0
 - `number`: Anzahl der Freitext Etiketten
 - `textlabel_type`: Einstellungen für Freitext Etiketten:
    - `multiple`: Mehrere Etiketten - eins pro Zeile im Freitext Eingabefeld
