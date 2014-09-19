#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SVG Templating System (C) Max Gaukler 2013
# unlimited usage allowed, see LICENSE file

# Dependencies

from lxml import etree
from copy import deepcopy
import sys, os, inspect
import StringIO
import math
import urllib2
import re
from decimal import Decimal
from pprint import pprint
import oerplib
import locale
from ConfigParser import ConfigParser
import codecs


def str_to_int(s, fallback=None):
    try:
        return int(s)
    except ValueError:
        return fallback


class cache(object):
    def __init__(self, f):
        self.cache = {}
        self.f = f

    def __call__(self, *args, **kwargs):
        hash = str(args)+str(kwargs)
        
        if hash not in self.cache:
            ret = self.f(*args, **kwargs)
            self.cache[hash] = ret
        else:
            ret = self.cache[hash]
        
        return ret
    

# switching to german:
locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

cfg = ConfigParser({'foo':'defaultvalue'})
cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                    database=cfg.get('openerp', 'database'), port=cfg.getint('openerp', 'port'),
                    version=cfg.get('openerp', 'version'))
user = oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))


@cache
def categ_id_to_list_of_names(c_id):
    categ = oerp.read('product.category', c_id, ['parent_id', 'name'], context=oerp.context)
    
    if categ['parent_id'] == False or \
           categ['parent_id'][0] == cfg.getint('openerp', 'base_category_id'):
        return [categ['name']]
    else:
        return categ_id_to_list_of_names(categ['parent_id'][0])+[categ['name']]
        

def importProdukteOERP(data):
    prod_ids = oerp.search('product.product', [('default_code', '!=', False)])
    prods = oerp.read('product.product', prod_ids, ['code', 'name', 'uom_id', 'list_price', 'categ_id'],
        context=oerp.context)
    
    # Only consider things with numerical PLUs in code field
    prods = filter(lambda p: str_to_int(p['code']) is not None, prods)
    
    for p in prods:
        p['code'] = int(p['code'])
        p['categ'] = categ_id_to_list_of_names(p['categ_id'][0])
        
        if p['categ'][0] not in data:
            data[p['categ'][0]] = []
        
        data[p['categ'][0]].append(
            (p['code'], p['name'], p['uom_id'][1], p['list_price'], 'DECIMAL', p['categ'][1:], []))

    return data


def importProdukteNormal(data):
    # Tab-Newline-separated data aus googledoc
    url = urllib2.urlopen("https://docs.google.com/spreadsheet/pub?key=0AlfhdBG4Ni7BdFJtU2dGRDh2MFBfWHVoUEk5UlhLV3c&single=true&gid=0&output=txt")
    textInput = url.read().decode('utf-8')
    # nach Array wandeln
    listInput = []
    for line in textInput.split('\n'):
        listInput.append(line.split('\t'))
    # HARDCODED: die vierte Zeile enthält die Spaltennamen
    columnNames=listInput[3]
    # Umwandeln in dictionary: {"SPALTENNAME":"Inhalt",...}

    # 'first_catergory_name': ('group_name', remove_first_katergorie?)
    categroyToGroup = {'3D-Druck-Material': ('3D-Drucker', False),
                       '3D-Drucker': ('3D-Drucker', True),
                       'Arbeitsschutz': ('Sonstiges', False),
                       'Drucker': ('Sonstiges', False),
                       'Drehbank': ('CNC', False),
                       'Elektronikmaterial': ('Elektronik', False),
                       'Mechanik': ('Mechanik', True),
                       'Mechanikmaterial': ('Mechanik', True),
                       u'Fräse': ('CNC', False),
                       u'CNC': ('CNC', True),
                       'Inventar': ('Sonstiges', False),
                       'Kühlschmiermittel': ('Sonstiges', False),
                       'Lasercutter': ('Laser', True),
                       'Laserdrucker': ('Sonstiges', False),
                       'Lasermaterial': ('Laser', False),
                       'Laserzeit': ('Laser', False),
                       'Papier': ('Sonstiges', False),
                       'Platinenfertigung': ('Elektronik', False),
                       'Folienmaterial': ('Schneideplotter', False),
                       'Verbrauchsmaterial': ('Sonstiges', False),
                       'Transferpresse': ('Schneideplotter', False),
                       'Spenden': ('Sonstiges', True)}
                       

    dictInput = {}
    for line in listInput:
        n = 0
        d = {}
        for col in line:
            d[columnNames[n]] = col
            n += 1
        dictInput[d["ID"]] = d


    for id, p in dictInput.items():
        basiseinheit = p['VERKAUFSEINHEIT']
        if basiseinheit == u'':
            basiseinheit = u'Stück'
        
        input_mode = u'INTEGER'
        
        # Wir wollen auch halbe euros!
        if basiseinheit == u'Euro' or basiseinheit == u'Gramm':
            input_mode = u'DECIMAL'
        
        m = re.match('(\d+,\d{2})', p['PREIS'])
        if m:
            preis = Decimal(m.group(0).replace(',', ''))/Decimal(100.0)
            if not preis > 0:
               continue 
        else:
            continue
        
        name = p['TITEL']
        if not name:
            name = p['KATEGORIE']
        if p['BAUFORM'] or p['WERT']:
            name += ' ('+p['BAUFORM']+' '+p['WERT']+')'
        
        kategorie = map(lambda x: x.strip(), p['KATEGORIE'].split(','))
        kategorie = filter(None, kategorie)
        
        if kategorie and kategorie[0] in categroyToGroup:
            c2g = categroyToGroup[kategorie[0]]
            group = c2g[0]
            if c2g[1]:
                kategorie = kategorie[1:]
        else:
            group = 'Sonstiges'
        
        if group not in data:
            data[group] = []
        data[group].append((int(id), name, basiseinheit, preis, input_mode, kategorie, []))
    
    return data
    

def importLasermaterial(data):
    dictInput=googledocToDict("https://docs.google.com/spreadsheet/pub?key=0AmjH14OiJIA8dFh2NHRyVzFZV1NySXMwUzFlUE5NTXc&single=true&gid=4&output=txt")
    
    for id, p in dictInput.items():
        try:
           id = int(id.strip())
        except:
            # ungültige id
            continue
            
        
        input_mode = u'INTEGER'
        
        # Bestimme Flächenpreis
        flaechenpreis = None
        m = re.match('(\d+,\d+)', p[u'Flächenpreis'])
        if m:
            # Preis in Cent!
            flaechenpreis = Decimal(m.group(0).replace(',', '.'))/Decimal(100.0)
            if not flaechenpreis > 0:
               flaechenpreis = None
        # Bestimme Plattenpreis
        plattenpreis = None
        m = re.match('(\d+,\d+)', p[u'Plattenpreis'])
        if m:

            plattenpreis = Decimal(m.group(0).replace(',', '.'))
        dicke=""
        if len(p['Dicke']) > 0:
            dicke=p['Dicke'] + ' mm '
        name = p['Material'] + ' ' + dicke + p['Farbe']
        
        kategorie=p['Material']
        if (p['Material'] == 'Acryl') and p['Dicke'] != '':
            # bei Acryl extra Unterkategorien je nach Dicke
             kategorie = kategorie + ', ' +p['Dicke'].replace(',' , '.') + ' mm'
        kategorie = 'Lasermaterial, '+kategorie
        kategorie = kategorie.split(',')
        kategorie = map(lambda x: x.strip(), kategorie)
        group = 'Laser'
         
        if p['Lager'] in [u'–', u'○']:
            # garnicht oder nur auf Anfrage vorrätig, überspringen
            continue
        platte = u'Platte ' + p[u'Plattengröße']
        extraEinheiten = []
        if plattenpreis > 0 and flaechenpreis > 0:
            preis=flaechenpreis
            basiseinheit = u'cm²'
            faktorZuBasiseinheit = None         # TODO Faktor aus Länge*Breite ausrechnen
            extraInputMode = 'INTEGER'
            extraEinheit = platte
            extraEinheiten = [(extraEinheit, plattenpreis, faktorZuBasiseinheit, extraInputMode)]
        elif plattenpreis > 0:
            basiseinheit = platte
            preis = plattenpreis
        else:
            continue
        if group not in data:
            data[group] = []
        data[group].append((int(id), name, basiseinheit, preis, input_mode, kategorie, extraEinheiten))
    return data
    
def importFraesenmaterial(data):
    dictInput=googledocToDict("https://docs.google.com/spreadsheet/pub?key=0AmjH14OiJIA8dFh2NHRyVzFZV1NySXMwUzFlUE5NTXc&single=true&gid=5&output=txt")
    
    for id, p in dictInput.items():
        try:
           id = int(id.strip())
        except:
            # ungültige id
            continue
            
        
        input_mode = u'INTEGER'
        
        # Bestimme Preis
        preis = None
        # 12,34 €
        # 12,34 € / m
        # 7,245 € / kg
        m = re.match(ur'(\d+,\d+) €( */ *)?([^/ ].*)?', p[u'VK'])
        basiseinheit=u"Stück"
        if not m:
            continue
        preis = Decimal(m.group(1).replace(',', '.'))
        if preis <= 0:
            continue
        if m.group(3):
            basiseinheit=m.group(3)
            input_mode=u'DECIMAL'
        
        name=p['Material']
        if p['H']:
            name += u' {} x '.format(p['H'])
        if p['L'] or p['B']:
            name += u' {} x {} ' .format (p['L'], p['B'])
        kategorie=[u"Material"]
            
        group='CNC'
        if group not in data:
            data[group] = []
        data[group].append((int(id), name, basiseinheit, preis, input_mode, kategorie, []))
    return data

def importFraeser(data):
    dictInput=googledocToDict("https://docs.google.com/spreadsheet/pub?key=0AmjH14OiJIA8dFh2NHRyVzFZV1NySXMwUzFlUE5NTXc&single=true&gid=6&output=txt")
    
    for id, p in dictInput.items():
        try:
           id = int(id.strip())
        except:
            # ungültige id
            continue
            
        
        input_mode = u'INTEGER'
        basiseinheit=u"Minute"
        
        # Bestimme Preis
        preis = None
        # 12,34 €
        m = re.match(ur'(\d+,\d+)', p[u'Minutenpreis'])
        if not m:
            continue
        preis = Decimal(m.group(1).replace(',', '.'))
        if preis <= 0:
            continue
        
        # Bezeichnung zusammenstückeln
        name=u" ".join([p["Form"], p["D"]+"mm", p["z"]+"S",  p["Hersteller"], p["Bezeichnung"]])
        kategorie=[u"Fräse", u"Fräser"]
        
        m = re.match(ur'(\d+,\d+)', p[u'Bruchpreis'])
        if not m:
            continue
        extraPreis = Decimal(m.group(1).replace(',', '.'))
        if extraPreis <= 0:
            continue
        extraEinheit=u"Stück bei Fräserbruch"
        extraInputMode="INTEGER"
        faktorZuBasiseinheit=None
        extraEinheiten = [(extraEinheit, extraPreis, faktorZuBasiseinheit, extraInputMode)]
        group='CNC'
        if group not in data:
            data[group] = []
        data[group].append((int(id), name, basiseinheit, preis, input_mode, kategorie, extraEinheiten))
    return data


def saveToDir(data, outputdir):
    for g in data.keys():
        print outputdir+g+'.txt'
        f = open(outputdir+g+'.txt', 'w')
    
        # vorsortieren nach Kategorie+Name
        def namensSortierung(x):
            kategorieString=' '.join(x[5])
            return kategorieString+x[1];
        data[g].sort(key=lambda x: namensSortierung(x))
    
        # Spezial-PLUs >8999 werden ganz vorne hingestellt, sortiert nach PLU
        def pluSortierung(plu):
            if (plu>9000):
                return plu-9999999; # ganz nach vorne stellen
            else:
                return 0
        data[g].sort(key=lambda x: pluSortierung(x[0]))
    
        # In Datei schreiben
        def formatiereOutput(d):
            s='%04d;%s;%s;%s;%s;%s\n' % (d[0],  d[1],  d[2],  d[3], d[4], d[5])
            if d[6]:
                # weitere Verkaufseinheiten
                for einheit in d[6]:
                    s += '\t%s;%s;%s;%s\n' % einheit;
            return s
        for l in map(lambda d: formatiereOutput(d), data[g]):
            f.write(l.encode('utf-8'))
    
        f.close()

def main():

	
    #data = {}
    #data = importProdukteOERP(data)
    ##data = importProdukteNormal(data)
    #data = importLasermaterial(data)
    #data = importFraesenmaterial(data)
    #data = importFraeser(data)
    ##outputdir = os.path.dirname(os.path.realpath(__file__))+'/produkte/'
    ##saveToDir(data, outputdir)
    

if __name__ == '__main__':
    main()
