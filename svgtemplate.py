#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

__author__ = 'Max Gaukler, sedrubal'
__license__ = 'unilicense'

"""
SVG Templating System (C) Max Gaukler 2013
with additions and redesigns by members of the FAU FabLab
unlimited usage allowed, see LICENSE file
"""


from lxml import etree
from copy import deepcopy
import inspect
import StringIO
import re
from ConfigParser import ConfigParser
import locale
import codecs
import oerplib
import argparse
import argcomplete
import sys
import os
from json import loads, dumps
from repoze.lru import lru_cache  # caching decorator for time-intensive read functions
from logging import error, warning


# <editor-fold desc="argparse">
parser = argparse.ArgumentParser(description='Automated generating of labels for products from the openERP')
parser.add_argument('ids', metavar='ids', type=str, nargs='*', default='',
                    help='the ids of the products (4 digits) or purchase orders (PO + 5 digits) to generate a label. '
                         'You can use expressions like 5x1337 to print 5 times the label for 1337. '
                         'And you can also use stdin for ids input. '
                         'Can\'t be used with \'json-input\'.')
parser.add_argument('-o', '--json-output', action='store_true', dest='json_output',
                    help='use this, if you only want to fetch the data for the labels from openERP '
                         'and if you want to read the data as json from stdout. '
                         'Can\'t be used with \'json-input\'.')
parser.add_argument('-i', '--json-input', action='store_true', dest='json_input',
                    help='use this, if the data for the labels should be provided through stdin as json '
                         'instead of fetching it from openERP. '
                         'Can\'t be used with \'ids\' and \'json-output\'.')

argcomplete.autocomplete(parser)
args = parser.parse_args()
# </editor-fold>


# <editor-fold desc="create svg label">
def clear_group_members(tree, group):
    """
    removes all groups (?) in a svg
    :param tree: the svg tree
    :param group: (?)
    """
    for e in tree.findall(".//{http://www.w3.org/2000/svg}g[@id='" + group + "']/*"):
        e.clear()


# <editor-fold desc="barcode">
def make_barcode_xml_elements(string, barcode):
    """
    generates an EAN8 barcode and returns a lst of lxml-elements
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
    gewichtete Summe: die letzte Stelle (vor der Pruefziffer) mal 3, die vorletzte mal 1, ..., addiert
    Pruefziffer ist dann die Differenz dieser Summe zum naechsten Vielfachen von 10
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
    baue gueltige EAN8 aus Zahl: vorne Nullen auffuellen, ggf. Pruefziffer anhaengen wenn Zahl kleiner 10000,
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

    if len(data) is 0:
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


# <editor-fold desc="fetch data">
# <editor-fold desc="fetch data from oerp">
@lru_cache(1024)
def oerp_read_product(product_id, oerp):
    """
    Fetches the data for the requested product
    :param product_id: the openERP product ID of the requested product
    :param oerp: the openERP lib instance
    :return: a data dict or an empty dict if the product couldn't be found
    """
    # produktRef='0009'
    # adds leading 0
    product_id = "{:04}".format(int(product_id))
    # print(etikettId)
    prod_ids = oerp.search('product.product', [('default_code', '=', product_id)])
    if len(prod_ids) == 0:
        error("ID %d nicht gefunden!" % int(product_id))
        return {}
        # return {"TITEL": "__________", "ORT": "Fehler - nicht gefunden", "PREIS": "", "ID": product_id}
    # for 30% improved speed we only request certain properties and not all
    p = oerp.read('product.product', prod_ids[0],
                  ['property_stock_location', 'list_price', 'uom_id', 'name', 'categ_id', 'sale_ok'],
                  context=oerp.context)

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

    verkaufseinheit = p['uom_id'][1]
    if not p['sale_ok']:
        preis = u"unverkäuflich"
        verkaufseinheit = ""
    elif p['list_price'] == 0:
        preis = u"gegen Spende"
        verkaufseinheit = ""
    else:
        if p['list_price'] * 1000 % 10 >= 1:  # Preis mit drei Nachkomastellen
            formatstring = u"{:.3f} €"
        else:
            formatstring = u"{:.2f} €"
        preis = formatstring.format(p['list_price']).replace(".", ",")

    data = {"TITEL": p['name'], "ORT": ort, "ID": product_id,
            "PREIS": preis,
            "VERKAUFSEINHEIT": verkaufseinheit}  # p['description']

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
def oerp_get_ids_from_order(po_id, oerp):
    """
    Fetches the product IDs of a purchase order
    :param po_id: The openERP purchase order ID
    :param oerp: the openERP lib instance
    :return: an array containing the openERP product IDs of a purchase
    """
    po_id = int(po_id.lower().replace("po", ""))  # purchase order id (PO12345 -> 12345)
    try:
        po = oerp.browse('purchase.order', po_id)
    except oerplib.error.RPCError:
        return []
    # get all lines (= articles) of the purchase order
    default_code_regex = re.compile(r"^\d{4}$")  # default code must be four-digit number with leading zeroes

    # use of oerp.browse is avoided here because it is too slow for iteratively reading fields

    # get product id of each 'line' = article
    product_ids = []
    for po_line in oerp.read('purchase.order.line', po.order_line.ids, ['product_id']):
        product_ids.append(po_line['product_id'][0])

    # get default code for each product id
    po_prod_codes = []
    for product in oerp.read('product.product', product_ids, ['default_code']):
        code = product['default_code']
        # warning(code.__repr__())
        if code is not False and default_code_regex.match(code):
            po_prod_codes.append(int(code))
    return po_prod_codes
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
    if type(text) != unicode:
        text = codecs.decode(text, 'utf8')
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

    if not args.json_input:
        # <editor-fold desc="config, oerp login">
        # switching to german:
        locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
        if not os.path.isfile('config.ini'):
            error('Please copy the config.ini.example to config.ini and edit it.')
            sys.exit(1)
        cfg = ConfigParser({'foo': 'defaultvalue'})
        cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

        use_test = cfg.get('openerp', 'use_test').lower().strip() == 'true'
        if use_test:
            warning("use testing database.")
        database = cfg.get('openerp', 'database_test') if use_test else cfg.get('openerp', 'database')
        oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                            database=database, port=cfg.getint('openerp', 'port'),
                            version=cfg.get('openerp', 'version'))
        # user = ...
        oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))
        # </editor-fold>

        # <editor-fold desc="evaluate input, replace PO IDs with their product ids, fetch data from oerp">
        purchase_regex = re.compile(r"^(\d{1,2}x)?po\d{5}$")  # (a number and 'x' and) 'PO' or 'po' and 5 digits
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
            if purchase_regex.match(args_id) > 0:
                prod_ids = oerp_get_ids_from_order(args_id, oerp)
                for prod_id in prod_ids:
                    prod_id = int(prod_id)
                    if prod_id not in labels_data.keys():
                        prod_data = deepcopy(oerp_read_product(prod_id, oerp))
                        if len(prod_data):
                            labels_data[prod_id] = prod_data
                            labels_data[prod_id]['COUNT'] = number_of_labels
                    else:
                        labels_data[prod_id]['COUNT'] += number_of_labels
            elif product_regex.match(args_id) > 0:
                args_id = int(args_id)
                if args_id not in labels_data.keys():
                    prod_data = deepcopy(oerp_read_product(args_id, oerp))
                    if len(prod_data):
                        labels_data[args_id] = prod_data
                        labels_data[args_id]['COUNT'] = number_of_labels
                else:
                    labels_data[args_id]['COUNT'] += number_of_labels
            else:
                error("The ID '" + args_id + "' you entered is invalid.")
                exit(1)
        # </editor-fold>
    else:
        labels_data = read_products_from_stdin()
        label_count = 0
        for prod in labels_data.values():
            label_count += prod['COUNT']
        if label_count > 50:
            error("Too much labels!")
            exit(1)

    if args.json_output:
        print(dumps(labels_data, sort_keys=True, indent=4, separators=(',', ': ')))  # json.dumps in pretty
    else:
        # <editor-fold desc="import pyBarcode">
        script_path = os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe())))  # path of this script
        # adds the pyBarcode subdirectory
        sys.path.append(script_path + "/pyBarcode-0.6/")
        import barcode
        # </editor-fold>

        # <editor-fold desc="load page template (for labels) and empty is">
        template = etree.parse("./vorlage-etikettenpapier-60x30.svg")

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
        # p['list_price'] p['name'] p['description']

        # Fehler vermeiden: wenn leere Ausgabe gefordert, erzeuge eine leere Seite, statt garnix
        # if len(product_ids) == 0:
        # product_ids = [None]
        # </editor-fold>

        # <editor-fold desc="make temp dir">
        output_dir = './temp/'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # </editor-fold>

        page_count = 0
        pdftk_cmd = "pdftk "

        for label_data in labels_data.values():
            # <editor-fold desc="generate and save a svg->pdf for each label"
            page = deepcopy(template)
            for i in range(label_data['COUNT']):
                label_svg = make_label(label_data, 0, barcode, etikett_template)
                if label_svg is not None:
                    page.getroot().append(label_svg)
                    # <editor-fold desc="write svg and convert it to pdf">
                    output_file_base_name = "output-etikettenpapier-%d" % page_count
                    page.write(output_dir + output_file_base_name + ".svg")
                    # TODO: use subprocess.check_output instead of os.system
                    if os.system("inkscape " + output_dir + output_file_base_name + ".svg --export-pdf=" + output_dir +
                                 output_file_base_name + ".pdf") != 0:
                        raise Exception("Inkscape failed")
                    # </editor-fold>
                    pdftk_cmd += output_dir + ("output-etikettenpapier-%d.pdf " % page_count)
                    page_count += 1
            # <editor-fold>

        # <editor-fold desc="append pages (pdftk)"
        pdftk_cmd += " cat output " + output_dir + "output-etikettenpapier.pdf"
        if os.system(pdftk_cmd) != 0:
            raise Exception("pdftk failed")
        # </editor-fold>

        # <editor-fold desc="clean">
        for p in range(page_count):
            os.remove(output_dir + ("output-etikettenpapier-%d.pdf" % p))
            os.remove(output_dir + ("output-etikettenpapier-%d.svg" % p))
        # </editor-fold>

        # <editor-fold desc="deprecated">
        # while len(product_ids) > 0:
        #     # <editor-fold desc="generate a svg label for the id">
        #     page = deepcopy(template)
        #     page_num += 1
        #     pages.append(page_num)
        #     labels_per_page = 1
        #     for etikettNum in range(0, labels_per_page):
        #         if len(product_ids) == 0:
        #             # keine weiteren Etiketten drucken
        #             break
        #         etikett_id = product_ids.pop(0)  # hole erste zu druckende ID aus der Liste
        #         # data = dictInput.get(str(etikettId),{"KURZTITEL":"Error","TITEL":"Error","ID":"000"})
        #         # deepcopy is needed because the lru_cache decorator returns the same object on cached function calls,
        #         # even if it was modified
        #         data = deepcopy(oerp_read_product(etikett_id, oerp))
        #         etikett_svg = make_label(data, etikettNum, barcode, etikett_template)  # , dict_input
        #         if etikett_svg is not None:
        #             page.getroot().append(etikett_svg)
        #         else:
        #             pages.remove(page_num)  # hart reingefrickelt
        #             page_num -= 1
        #             continue
        #     # </editor-fold>
        #     # <editor-fold desc="write svg and convert it to pdf">
        #     output_file_base_name = "output-etikettenpapier-%d" % page_num
        #     page.write(output_dir + output_file_base_name + ".svg")
        #     if os.system("inkscape " + output_dir + output_file_base_name + ".svg --export-pdf=" + output_dir +
        #             output_file_base_name + ".pdf") != 0:
        #         raise Exception("Inkscape failed")
        #     # </editor-fold>
        #
        # # <editor-fold desc="append pages (pdftk)">
        # pdftk_cmd = "pdftk "
        # for page_num in pages:
        #     pdftk_cmd += output_dir + ("output-etikettenpapier-%d.pdf " % page_num)
        # pdftk_cmd += " cat output " + output_dir + "output-etikettenpapier.pdf"
        # if os.system(pdftk_cmd) != 0:
        #     raise Exception("pdftk failed")
        # # </editor-fold>
        #
        # # <editor-fold desc="clean">
        # for page_num in pages:
        #     os.remove(output_dir + ("output-etikettenpapier-%d.pdf" % page_num))
        #     os.remove(output_dir + ("output-etikettenpapier-%d.svg" % page_num))
        # # </editor-fold>
        # </editor-fold>

    exit(0)


if __name__ == "__main__":
    main()
