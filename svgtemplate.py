#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
SVG Templating System (C) Max Gaukler and other members of the FAU FabLab 2013-2022
unlimited usage allowed, see LICENSE file
"""

from lxml import etree
from copy import deepcopy
import inspect
from io import BytesIO
import re
import locale
import codecs
import argparse
import argcomplete
import sys
import os
import subprocess
from json import loads, dumps
from repoze.lru import lru_cache  # caching decorator for time-intensive read functions
from logging import error, warning
import requests


__author__ = 'Max Gaukler, sedrubal'
__license__ = 'unlicense'

# <editor-fold desc="argparse">
parser = argparse.ArgumentParser(description='Automated generating of labels for products from the ERP-web-API')
parser.add_argument('ids', metavar='ids', type=str, nargs='*', default='',
                    help='the ids of the products (4 digits) or purchase orders (PO + 5 digits) to generate a label. '
                         'You can use expressions like 5x1337 to print 5 times the label for 1337. '
                         'And you can also use stdin for ids input. '
                         'Can\'t be used with \'json-input\'.')
parser.add_argument('-o', '--json-output', action='store_true', dest='json_output',
                    help='use this, if you only want to fetch the data for the labels from the ERP-web-API '
                         'and if you want to read the data as json from stdout. '
                         'Can\'t be used with \'json-input\'.')
parser.add_argument('-i', '--json-input', action='store_true', dest='json_input',
                    help='use this, if the data for the labels should be provided through stdin as json '
                         'instead of fetching it from ERP-web-API. '
                         'Can\'t be used with \'ids\' and \'json-output\'.')

argcomplete.autocomplete(parser)
args = parser.parse_args()
# </editor-fold>


# <editor-fold desc="create svg label">
def clear_group_members(tree, group):
    """
    removes all content of a given group in a svg
    :param tree: the svg tree
    :param group: name of the group
    """
    for e in tree.findall(".//{http://www.w3.org/2000/svg}g[@id='" + group + "']/*"):
        e.clear()


# <editor-fold desc="barcode">
def make_barcode_xml_elements(string, barcode):
    """
    generates an EAN8 barcode and returns a lst of lxml-elements
    :param string: text to be encoded as a barcode
    :param barcode: (?)
    :return: a list of lxml elements
    """
    # Pseudo-Datei-Objekt
    s = BytesIO()
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
    
    gewichtete Summe: die letzte Stelle (vor der Pruefziffer) mal 3,
    die vorletzte mal 1, ..., addiert.
    
    Pruefziffer ist dann die Differenz
    dieser Summe zum naechsten Vielfachen von 10
    
    :param num: number to be encoded as EAN
    :return: checksum digit
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
    baue gueltige EAN8 aus Zahl:
    
    - vorne Nullen auffuellen
    - wenn Zahl kleiner 10000, mache eine EAN8 im privaten Bereich daraus: 200nnnn
    - add checksum digit
    
    :param num: number for the barcode
    :return: (?)
    """
    if len(str(num)) == 8:
        return str(num)
    num = int(num)
    if num < 10000:
        num += 2000000
    return '%07d%d' % (num, ean8_check_digit(num))
# </editor-fold>


def make_label(data, etikett_num, barcode, label_template):  # , dict_input
    """
    Generates a label with following information
    :param data: a dict containing the data for the label
    :param etikett_num: the number (?) of the label
    :param barcode: the barcode (generated from the product ID (?))
    :param label_template: the template for labels
    :return: a label in svg (?) or None, when the product couldn't be found
    """
    # :param dict_input: deprecated
    etikett = deepcopy(label_template)
    etikett.set("id", "etikettGeneriert" + str(etikett_num))

    if len(data) == 0:
        return None

    # replace all text
    for element in etikett.iter("*"):
        for [key, value] in data.items():
            if key not in ['ID', 'ORT', 'PREIS', 'TITEL', 'VERKAUFSEINHEIT']:
                continue  # skip empty keys
            if element.tail is not None:
                element.tail = element.tail.replace(key, value)
            if element.text is not None:
                element.text = element.text.replace(key, value)
    for e in make_barcode_xml_elements(create_ean8(data["ID"]), barcode):
        etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").append(e)
    etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").set("id", "barcode" + str(etikett_num))
    return etikett
# </editor-fold>


@lru_cache(1)
def read_product_db():
    r = requests.get('https://brain.fablab.fau.de/build/pricelist/price_list-Alle_Produkte.html.json')
    return r.json()

# <editor-fold desc="fetch data">
# <editor-fold desc="fetch data from oerp">
@lru_cache(1024)
def read_product(product_id):
    """
    Fetches the data for the requested product
    :param product_id: the openERP product ID of the requested product
    :param oerp: the openERP lib instance
    :return: a data dict or an empty dict if the product couldn't be found
    """
    # produktRef='0009'
    # adds leading 0
    
    product_id = int(product_id)
    product_id_zeroes = "{:04}".format(product_id)
    products = read_product_db()
    
    if product_id_zeroes not in products:
        error("ID %d nicht gefunden!" % product_id)
        return {}
    p = products[product_id_zeroes]
    location_string = p["_location_str"]
    verkaufseinheit = p['_uom_str']
    price = p['_price_str']

    data = {"TITEL": p['name'], "ORT": location_string, "ID": product_id_zeroes,
            "PREIS": price,
            "VERKAUFSEINHEIT": verkaufseinheit}

    # TODO Hardcoded Business logic
    # - eigentlich sollte diese Verarbeitung anderswo erfolgen und dieses Skript nur die template engine sein
    # erzeuge String fuer Verkaufseinheit: "123€ pro Stueck"
    if len(data.get("PREIS", "")) > 1:
        # wenn der Preis numerisch ist, standardmaeßig Verkaufseinheit = Stueck
        if len(data.get("VERKAUFSEINHEIT", "")) < 1 and re.match("[0-9]", data.get("PREIS", "")):
            data["VERKAUFSEINHEIT"] = u"Stück"

        # Wenn Verkaufseinheit gesetzt, "pro ..." ergaenzen
        # außer wenn es mit "bei" anfaengt, denn "pro bei" ist Schmarrn.
        if len(data.get("VERKAUFSEINHEIT", "")) > 0 and not data["VERKAUFSEINHEIT"].startswith("bei"):
            data["VERKAUFSEINHEIT"] = "pro " + data["VERKAUFSEINHEIT"]
    else:
        # keine Einheit anzeigen, wenn Preis leer oder "-"
        data["VERKAUFSEINHEIT"] = ""

    return data


@lru_cache(128)
def get_ids_from_order(po_id):
    """
    Fetches the product IDs of a purchase order
    :param po_id: The openERP purchase order ID
    :param oerp: the openERP lib instance
    :return: an array containing the openERP product IDs of a purchase
    """
    error("purchase orders (PO1234) are currently not supported. We first need to create a JSON exporter for that to have an API that works with Py3")
    # return [1, 42, 2937]
# </editor-fold>


def read_products_from_stdin():
    """
    Reads the json label description from stdin
    :return: a dict containing the information for the labels
    """
    labels_data = loads(read_stdin())
    return labels_data
# </editor-fold>


def read_stdin():
    """
    Reads text from stdin
    :return: the text given through stdin
    """
    text = sys.stdin.read()
    return text


def main():
    """
    The main class of the script: generate labels for products and produces a pdf file
    :raise Exception:
    """
    # <editor-fold desc="check arguments">
    if args.json_input and args.json_output:
        error("Invalid arguments. If you don't want to create a PDF-label you can't provide data through stdin.")
        parser.print_help()
        exit(1)
    elif args.json_input and args.ids:
        error("Invalid arguments. If you want to use the stdin for json data input, you mustn't provide ids.")
        parser.print_help()
        exit(1)
    # </editor-fold>

    script_path = os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe())))  # path of this script

    if not args.json_input:
        # <editor-fold desc="evaluate input, replace PO IDs with their product ids, fetch data from oerp">
        purchase_regex = re.compile(r"^(\d{1,2}x)?po\d{1,5}$")  # (a number and 'x' and) 'PO' or 'po' and 1-5 digits
        product_regex = re.compile(r"^(\d{1,2}x)?\d{1,4}$")  # (a number and 'x' and) 1 to 4 digits
        labels_data = dict()
        if len(args.ids):
            input_ids = args.ids
        else:
            input_ids = read_stdin().strip().split(' ')
        for args_id in input_ids:
            number_of_labels = 1
            args_id = args_id.lower()
            if 'x' in args_id:
                number_of_labels_str = args_id[:3].split('x', 2)[0]
                assert number_of_labels_str.isdigit(), "invalid input"
                # multiple labels requested: (1-25)x(product_id)
                number_of_labels = max(0, min(int(number_of_labels_str), 25))
                x_position = args_id.find('x')
                args_id = args_id[x_position + 1:]
            if purchase_regex.match(args_id):
                prod_ids = get_ids_from_order(args_id)
                for prod_id in prod_ids:
                    prod_id = int(prod_id)
                    if prod_id not in labels_data.keys():
                        prod_data = deepcopy(read_product(prod_id))
                        if len(prod_data):
                            labels_data[prod_id] = prod_data
                            labels_data[prod_id]['COUNT'] = number_of_labels
                    else:
                        labels_data[prod_id]['COUNT'] += number_of_labels
            elif product_regex.match(args_id):
                args_id = int(args_id)
                if args_id not in labels_data.keys():
                    prod_data = deepcopy(read_product(args_id))
                    if len(prod_data):
                        labels_data[args_id] = prod_data
                        labels_data[args_id]['COUNT'] = number_of_labels
                else:
                    labels_data[args_id]['COUNT'] += number_of_labels
            else:
                error("The ID '" + args_id + "' you entered is invalid.")
                exit(1)
            if not labels_data:
                error("No valid products found. Products must have a valid 'internal ID' like 0123.")
                exit(1)
        # </editor-fold>
    else:
        labels_data = read_products_from_stdin()
        label_count = 0
        for prod in labels_data.values():
            label_count += prod['COUNT']
        if label_count > 50:
            error("Too many labels!")
            exit(1)

    if args.json_output:
        print(dumps(labels_data, sort_keys=True, indent=4, separators=(',', ': ')))  # json.dumps in pretty
    else:
        import barcode

        # <editor-fold desc="load page template (for labels) and empty is">
        template = etree.parse(script_path + "/vorlage-etikettenpapier-60x30.svg")

        # remove everything with an id starting with 'ignore'
        for e in template.findall("*"):
            if e.get("id", "").endswith("ignore"):
                e.clear()
        # pick out items
        # they need to be directly on the root level in the file
        # (or at least not inside a group with an applied transformation), so that position and size is correct
        etikett_template = deepcopy(template.find(".//{http://www.w3.org/2000/svg}g[@id='etikett']"))
        clear_group_members(etikett_template, 'barcode')
        clear_group_members(template, 'etikett')
        # </editor-fold>

        # <editor-fold desc="deprecated things">
        # <editor-fold desc="tab-newline-separated data aus google doc">
        # url=urllib2.urlopen("https://docs.google.com/spreadsheet/pub?key=0AlfhdBG4Ni7BdFJtU2dGRDh2MFBfWHVoUEk5UlhLV3c&single=true&gid=0&output=txt")
        # textInput=url.read().decode('utf-8')
        # # convert to array
        # listInput=[]
        # for line in textInput.split('\n'):
        # listInput.append(line.split('\t'))
        # # HARDCODED: the fourth column contains the column name
        # columnNames=listInput[3]
        # # convert to dictionary: {"SPALTENNAME":"Inhalt",...}
        # </editor-fold>
        # dict_input = {}
        # for line in listInput:
        # n=0
        # d={}
        # for col in line:
        # d[columnNames[n]]=col
        # n=n+1
        # dict_input[d["ID"]]=d
        # print(p)
        # p['lst_price'] p['name'] p['description']

        # Fehler vermeiden: wenn leere Ausgabe gefordert, erzeuge eine leere Seite, statt garnix
        # if len(product_ids) == 0:
        # product_ids = [None]
        # </editor-fold>

        # <editor-fold desc="make temp dir">
        output_dir = script_path + '/public/temp/'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # </editor-fold>

        page_count = 0
        pdfs_to_merge = []

        for label_data in labels_data.values():
            # <editor-fold desc="generate and save a svg->pdf for each label"
            page = deepcopy(template)
            for i in range(label_data['COUNT']):
                label_svg = make_label(label_data, 0, barcode, etikett_template)
                if label_svg is not None:
                    page.getroot().append(label_svg)
                    # <editor-fold desc="write svg and convert it to pdf">
                    output_file_base_name = "output-etikettenpapier-%d" % page_count
                    svg_file = output_dir + output_file_base_name + ".svg"
                    pdf_file = output_dir + output_file_base_name + ".pdf"
                    page.write(svg_file)
                    subprocess.call("inkscape {in_file} --export-filename={out_file} 2>&1 | egrep -v '(^$|dbus|Failed to get connection)'".format(
                        in_file=svg_file,
                        out_file=pdf_file
                    ), shell=True)
                    # </editor-fold>
                    pdfs_to_merge.append(pdf_file)
                    page_count += 1
            # <editor-fold>

        # <editor-fold desc="append pages (pdftk)"
        
        pdf_output = output_dir + "output-etikettenpapier.pdf"
        subprocess.check_call(["qpdf", "--empty", "--pages"]  + pdfs_to_merge + ["--", pdf_output])
        # </editor-fold>
        # <editor-fold desc="clean">
        for p in range(page_count):
            try:
                os.remove(output_dir + ("output-etikettenpapier-%d.pdf" % p))
            except OSError:
                    pass
            try:
                os.remove(output_dir + ("output-etikettenpapier-%d.svg" % p))
            except OSError:
                pass
        # </editor-fold>

    exit(0)


if __name__ == "__main__":
    main()
