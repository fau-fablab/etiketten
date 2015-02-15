#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SVG Templating System (C) Max Gaukler 2013
with additions and redesigns by members of the FAU FabLab
unlimited usage allowed, see LICENSE file
"""

from lxml import etree
from copy import deepcopy
import sys
import os
import inspect
import StringIO
import re
from ConfigParser import ConfigParser
import locale
import codecs
import oerplib
import argparse
import argcomplete


# <editor-fold desc="argparse">
parser = argparse.ArgumentParser(description='Automated generating of labels for products from the openERP')

parser.add_argument('ids', metavar='ids', type=int, help='the id(s) of the product(s) to generate a label.', nargs='+')

argcomplete.autocomplete(parser)

args = parser.parse_args()

# </editor-fold>


def clear_group_members(tree, group):
    """
    removes all groups (?) in a svg
    :param tree: the svg tree
    :param group: (?)
    """
    for e in tree.findall(".//{http://www.w3.org/2000/svg}g[@id='" + group + "']/*"):
        e.clear()


def make_barcode_xml_elements(string, barcode):
    """
    erzeugt einen EAN8 barcode und gibt eine Liste von lxml-Elementen zurück
    :param string: (?)
    :param barcode: (?)
    :return: a list of lxml elements
    """
    # Pseudo-Datei-Objekt
    s = StringIO.StringIO()
    ean8 = barcode.get_barcode_class('ean8')
    b = ean8(string)
    b.write(s)
    # oder zu Debugzwecken: barcode.save('barcode') speichert in barcode.svg
    barcode_elements = etree.fromstring(s.getvalue())
    s.close()
    return barcode_elements.findall(".//{http://www.w3.org/2000/svg}rect")


def ean8_check_digit(num):
    """
    EAN checksum
    gewichtete Summe: die letzte Stelle (vor der Prüfziffer) mal 3, die vorletzte mal 1, ..., addiert
    Prüfziffer ist dann die Differenz dieser Summe zum nächsten Vielfachen von 10
    :param num: (?)
    :return: (?)
    """
    s = str(num)[::-1]  # in string wandeln, umkehren
    checksum = 0
    even = True
    for char in s:
        n = int(char)
        if even:
            n *= 3
        checksum += n
        even = not even
    return (10 - (checksum % 10)) % 10


def create_ean8(num):
    """
    baue gültige EAN8 aus Zahl: vorne Nullen auffüllen, ggf. Prüfziffer anhängen wenn Zahl kleiner 10000,
    mache eine EAN8 im privaten Bereich daraus: 200nnnn
    :param num: number for the barcode
    :return: (?)
    """
    if len(str(num)) == 8:
        return str(num)
    num = int(num)
    if num < 10000:
        num += 2000000
    return '%07d%d' % (num, ean8_check_digit(num))


def oerp_read_product(product_id, oerp):
    """
    Fetches the data for the requested product
    :param product_id: the openERP product ID of the requested product
    :param oerp: the openERP lib instance
    :return: a data dict
    """
    # produktRef='0009'
    # ergänze führende Nullen
    product_id = "{:04}".format(int(product_id))
    # print etikettId
    prod_ids = oerp.search('product.product', [('default_code', '=', product_id)])
    if len(prod_ids) == 0:
        return {"TITEL": "__________", "ORT": "Fehler - nicht gefunden", "PREIS": "", "ID": product_id}
    p = oerp.read('product.product', prod_ids[0], [], context=oerp.context)

    ort = p['property_stock_location']
    if not ort:
        # kein Ort direkt im Produkt festgelegt. versuche Ort aus Kategorie abzurufen
        c = oerp.read('product.category', p['categ_id'][0], [], context=oerp.context)
        ort = c['property_stock_location']
    if not ort:
        # keinerlei Ort festgelegt :(
        ort = "kein Ort eingetragen"
    else:
        ort = ort[1]
        for removePrefix in [u"tats\xe4chliche Lagerorte  / FAU FabLab / ", u"tats\xe4chliche Lagerorte  / "]:
            if ort.startswith(removePrefix):
                ort = ort[len(removePrefix):]

    if abs(0.1 % 0.01) > 0.0005:  # drei Nachkomastellen
        formatstring = u"{:.3f} €"
    else:
        formatstring = u"{:.2f} €"

    data = {"TITEL": p['name'], "ORT": ort, "ID": product_id,
            "PREIS": formatstring.format(p['list_price']).replace(".", ","),
            "VERKAUFSEINHEIT": p['uom_id'][1]}  # p['description']

    return data


def make_etikett(product_id, etikett_num, barcode, etikett_template, dict_input, oerp):
    """
    Generates a label with following information
    :param product_id: the openERP product ID
    :param etikett_num: the number (?) of the label
    :param barcode: the barcode (generated from the product ID (?))
    :param etikett_template: the template for labels
    :param dict_input: deprecated
    :param oerp: the openERP lib instance
    :return: a label in svg (?)
    """
    etikett = deepcopy(etikett_template)
    etikett.set("id", "etikettGeneriert" + str(etikett_num))

    data = oerp_read_product(product_id, oerp)
    # data = dictInput.get(str(etikettId),{"KURZTITEL":"Error","TITEL":"Error","ID":"000"})
    # data = deepcopy(data) # nötig damit bei mehrmaligem Ausdrucken eines Etiketts keine lustigen Effekte auftreten

    # TODO Hardcoded Business logic
    # - eigentlich sollte diese Verarbeitung anderswo erfolgen und dieses Skript nur die template engine sein
    # erzeuge String für Verkaufseinheit: "123€ pro Stück"
    if len(data.get("PREIS", "")) > 1:
        # wenn der Preis numerisch ist, standardmäßig Verkaufseinheit = Stück
        if len(data.get("VERKAUFSEINHEIT", "")) < 1 and re.match("[0-9]", data.get("PREIS", "")):
            data["VERKAUFSEINHEIT"] = u"Stück"

        # Wenn Verkaufseinheit gesetzt, "pro ..." ergänzen
        # außer wenn es mit "bei" anfängt, denn "pro bei" ist Schmarrn.
        if len(data.get("VERKAUFSEINHEIT", "")) > 0 and not data["VERKAUFSEINHEIT"].startswith("bei"):
            data["VERKAUFSEINHEIT"] = "pro " + data["VERKAUFSEINHEIT"]
    else:
        # keine Einheit anzeigen, wenn Preis leer oder "-"
        data["VERKAUFSEINHEIT"] = ""

    # Alle Texte ersetzen
    for element in etikett.iter("*"):
        for [key, value] in data.items():
            if len(key) == 0:
                continue  # überspringe leere keys
            if element.tail is not None:
                element.tail = element.tail.replace(key, value)
            if element.text is not None:
                element.text = element.text.replace(key, value)
    for e in make_barcode_xml_elements(create_ean8(data["ID"]), barcode):
        etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").append(e)
    etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").set("id", "barcode" + str(etikett_num))
    return etikett


def main():
    """
    The main class of the script: generate labels for products and produces a pdf file
    :raise Exception:
    """
    # in welchem path liegt die svgtemplate.py Datei?
    script_path = os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe())))
    # füge das pyBarcode Unterverzeichnis dem path hinzu
    sys.path.append(script_path + "/pyBarcode-0.6/")
    import barcode

    # switching to german:
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    # <editor-fold desc="config">
    if not os.path.isfile('config.ini'):
        print '[!] Please copy the config.ini.example to config.ini and edit it'
        sys.exit(1)
    cfg = ConfigParser({'foo': 'defaultvalue'})
    cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

    oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                        database=cfg.get('openerp', 'database'), port=cfg.getint('openerp', 'port'),
                        version=cfg.get('openerp', 'version'))
    # user =
    oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))
    # </editor-fold>

    # Load page template
    template = etree.parse("./vorlage-etikettenpapier-60x30.svg")

    # <editor-fold desc="Vernichte alles, dessen id mit ignore endet">
    for e in template.findall("*"):
        if e.get("id", "").endswith("ignore"):
            e.clear()
    # </editor-fold>

    # pick out items
    # they need to be directly on the root level in the file
    # (or at least not inside a group with an applied transformation), so that position and size is correct
    etikett_template = deepcopy(template.find(".//{http://www.w3.org/2000/svg}g[@id='etikett']"))
    clear_group_members(etikett_template, 'barcode')
    clear_group_members(template, 'etikett')

    # template is now an empty page

    ## Tab-Newline-separated data aus googledoc
    # url=urllib2.urlopen("https://docs.google.com/spreadsheet/pub?key=0AlfhdBG4Ni7BdFJtU2dGRDh2MFBfWHVoUEk5UlhLV3c&single=true&gid=0&output=txt")
    # textInput=url.read().decode('utf-8')
    ## nach Array wandeln
    # listInput=[]
    # for line in textInput.split('\n'):
    # listInput.append(line.split('\t'))
    ## HARDCODED: die vierte Zeile enthält die Spaltennamen
    # columnNames=listInput[3]
    ## Umwandeln in dictionary: {"SPALTENNAME":"Inhalt",...}

    dict_input = {}
    # for line in listInput:
    # n=0
    # d={}
    # for col in line:
    # d[columnNames[n]]=col
    # n=n+1
    # dict_input[d["ID"]]=d

    # print p
    # p['list_price'] p['name'] p['description']

    # Etiketten-IDs werden auf der Kommandozeile angegeben
    etikett_ids = deepcopy(sys.argv)
    etikett_ids.pop(0)  # Argumente beginnen erst bei sys.argv[1]

    if len(etikett_ids) == 0:  # Fehler vermeiden: wenn leere Ausgabe gefordert, erzeuge eine leere Seite, statt garnix
        etikett_ids = [None]

    # Einzelseiten erzeugen
    page_num = 0
    pages = []

    output_dir = './temp/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    while len(etikett_ids) > 0:
        page = deepcopy(template)
        page_num += 1
        pages.append(page_num)
        for etikettNum in range(0, 1):
            if len(etikett_ids) == 0:
                # keine weiteren Etiketten zu drucken
                break
            etikett_id = etikett_ids.pop(0)  # hole erste zu druckende ID aus der Liste
            page.getroot().append(make_etikett(etikett_id, etikettNum, barcode, etikett_template, dict_input, oerp))
        page.write(output_dir + ("output-etikettenpapier-%d.svg" % page_num))
        output_file_base_name = "output-etikettenpapier-%d" % page_num
        if os.system("inkscape " + output_dir + output_file_base_name + ".svg --export-pdf=" + output_dir +
                output_file_base_name + ".pdf") != 0:
            raise Exception("[!] Inkscape failed")
    # append pages
    pdftk_cmd = "pdftk "
    for page_num in pages:
        pdftk_cmd += output_dir + ("output-etikettenpapier-%d.pdf " % page_num)
    pdftk_cmd += " cat output " + output_dir + "output-etikettenpapier.pdf"
    if os.system(pdftk_cmd) != 0:
        raise Exception("[!] pdftk failed")
    # clean
    for page_num in pages:
        os.remove(output_dir + ("output-etikettenpapier-%d.pdf" % page_num))
        os.remove(output_dir + ("output-etikettenpapier-%d.svg" % page_num))


if __name__ == "__main__":
    main()