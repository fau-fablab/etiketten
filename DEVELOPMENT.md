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
           |- zeige eine (schöne) Vorschau vom erstellten Etikett -> zum Drucken wird das Formular erneut abgeschickt (frickelig) ∎
           |- sonst: zeige Etiketten PDF (wird eig. nicht benutzt) ∎


```

`POST` Felder:
--------------

 - `action`: was soll mit der Eingabe getan werden:
    - `print`: Etikett erstellen und drucken
    - `select`: Anzahl der Etiketten auswählen
    - `preview`: Eine PDF Vorschau anzeigen
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
 - `#<id>_<property>`: Wenn `print-selection`, dann werden die Etiketten Daten über solche Felder übergeben. `<id>`: 4(!) stellige Produkt ID
    - `#<id>_count`: Anzahl des zu druckenden Etiketts. Eine Zahl zwischen 0 und 20
    - `#<id>_titel`: Name des Produkts
    - `#<id>_preis`: Preis des Produkts (z.B. `0,13+€`)
    - `#<id>_verkaufseinheit`: Verkaufseinheit des Produkts (z.B. `pro+Stück`)
    - `#<id>_ort`: Lagerort des Produkts

`JSON` Stuktur:
---------------

Die `json` Daten (zwischen [`PHP`](index.php) und [`Python`](svgtemplate.py)) haben folgende Struktur:

```
{
    "<Produkt ID als String>": {
        "COUNT": <Anzahl als int>,
        "ID": "<Produkt ID als String>",
        "ORT": "<Ort als String>",
        "PREIS": "<Preis als String>",
        "TITEL": "<Bezeichnung als String>",
        "VERKAUFSEINHEIT": "<Verkaufseinheit als String>"
    },
    "<nächste Produkt ID": {
        <Produkt Werte wie oben>
    }
}
```

Beispiel:

```json
{
    "0200": {
        "COUNT": 5,
        "ID": "0200",
        "ORT": "kein Ort eingetragen",
        "PREIS": "1,35 \u20ac",
        "TITEL": "USB-Kabel A-B mini, 1.5m   ",
        "VERKAUFSEINHEIT": "pro St\u00fcck"
    },
    "1337": {
        "COUNT": 7,
        "ID": "1337",
        "ORT": "kein Ort eingetragen",
        "PREIS": "0,13 \u20ac",
        "TITEL": "Trollololololol schwarz auf wei\u00df",
        "VERKAUFSEINHEIT": "pro St\u00fcck"
    }
}
```
