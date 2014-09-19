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
from ConfigParser import ConfigParser
import oerplib
import locale
import codecs

# in welchem path liegt die svgtemplate.py Datei?
scriptPath=os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe())))
# füge das pyBarcode Unterverzeichnis dem path hinzu
sys.path.append(scriptPath + "/pyBarcode-0.6/")
import barcode


# switching to german:
locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

cfg = ConfigParser({'foo':'defaultvalue'})
cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                    database=cfg.get('openerp', 'database'), port=cfg.getint('openerp', 'port'),
                    version=cfg.get('openerp', 'version'))
user = oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))


def clearGroupMembers(tree,group):
	for e in tree.findall(".//{http://www.w3.org/2000/svg}g[@id='"+group+"']/*"):
		e.clear()

# Load page template
template = etree.parse("./vorlage-etikettenpapier-schubladenmagazin.svg")
# Vernichte alles, dessen id mit ignore endet
for e in template.findall("*"):
	if (e.get("id","").endswith("ignore")):
		e.clear()

# pick out items
# they need to be directly on the root level in the file (or at least not inside a group with an applied transformation), so that position and size is correct
etikettVorlage=deepcopy(template.find(".//{http://www.w3.org/2000/svg}g[@id='etikett']"))
clearGroupMembers(etikettVorlage,'barcode')
clearGroupMembers(template,'etikett')

# template is now an empty page

# erzeugt einen EAN8 barcode und gibt eine Liste von lxml-Elementen zurück
def makeBarcodeXMLElements(string):
	# Pseudo-Datei-Objekt
	s=StringIO.StringIO()
	EAN8 = barcode.get_barcode_class('ean8')
	b = EAN8(string)
	b.write(s)
	# oder zu Debugzwecken: barcode.save('barcode') speichert in barcode.svg
	barcodeElements=etree.fromstring(s.getvalue())
	s.close()
	return barcodeElements.findall(".//{http://www.w3.org/2000/svg}rect")


def EAN8Checkdigit(num):
	# EAN Prüfsumme
	# gewichtete Summe: die letzte Stelle (vor der Prüfziffer) mal 3, die vorletzte mal 1, ..., addiert
	# Prüfziffer ist dann die Differenz dieser Summe zum nächsten Vielfachen von 10
	
	s=str(num)[::-1] # in string wandeln, umkehren
	checksum=0
	even=True
	for char in s:
		n=int(char)
		if even:
			n=n*3
		checksum = checksum + n
		even=not even
	return (10 - (checksum%10))%10

# baue gültige EAN8 aus Zahl: vorne Nullen auffüllen, ggf. Prüfziffer anhängen
# wenn Zahl kleiner 10000, mache eine EAN8 im privaten Bereich daraus: 200nnnn
def createEAN8(num):
	if (len(str(num))==8):
		return str(num)
	num=int(num)
	if num<10000:
		num=num+2000000
	return '%07d%d' % (num, EAN8Checkdigit(num))


## Tab-Newline-separated data aus googledoc
#url=urllib2.urlopen("https://docs.google.com/spreadsheet/pub?key=0AlfhdBG4Ni7BdFJtU2dGRDh2MFBfWHVoUEk5UlhLV3c&single=true&gid=0&output=txt")
#textInput=url.read().decode('utf-8')
## nach Array wandeln
#listInput=[]
#for line in textInput.split('\n'):
	#listInput.append(line.split('\t'))
## HARDCODED: die vierte Zeile enthält die Spaltennamen
#columnNames=listInput[3]
## Umwandeln in dictionary: {"SPALTENNAME":"Inhalt",...}

#dictInput={}
#for line in listInput:
	#n=0
	#d={}
	#for col in line:
		#d[columnNames[n]]=col
		#n=n+1
	#dictInput[d["ID"]]=d


def oerpReadProduct(etikettId):
	#produktRef='0009'
	# ergänze führende Nullen
	etikettId="{:04}".format(int(etikettId))
	print etikettId
	prod_ids = oerp.search('product.product', [('default_code', '=', etikettId)])
	if len(prod_ids)==0:
		return {"TITEL":"__________","ORT":"Fehler - nicht gefunden","PREIS":"","ID":etikettId}
	p=oerp.read('product.product',prod_ids[0],[],context=oerp.context)
	#print p
	if abs(0.1%0.01)>0.0005: # drei Nachkomastellen
		formatstring=u"{:.3f} €"
	else:
		formatstring=u"{:.2f} €"
	# TODO Ort
	data={"TITEL":p['name'], "ORT":"","ID":etikettId} # p['description']
	data["PREIS"]=formatstring.format(p['list_price']).replace(".",",")
	return data
	#print p
	#p['list_price'] p['name'] p['description']
	
def makeEtikett(etikettId,etikettNum):
	global etikettVorlage, dictInput
	etikett=deepcopy(etikettVorlage)
	etikett.set("id","etikettGeneriert"+str(etikettNum))
	# Zeilen- und Spaltenabstände in komischen svg-Maßeinheiten (aus Inkscape-Datei abgelesen)
	yOffset=(165.98325-45.865125)*math.floor(etikettNum/3)
	xOffset=(268.54725-34.54725)*(etikettNum%3)
	etikett.set("transform","translate("+str(xOffset)+","+str(yOffset)+")")
	
	data=oerpReadProduct(etikettId)
	#data=dictInput.get(str(etikettId),{"KURZTITEL":"Error","TITEL":"Error","ID":"000"})
	#data=deepcopy(data) # nötig damit bei mehrmaligem Ausdrucken eines Etiketts keine lustigen Effekte auftreten
	
	# TODO Hardcoded Business logic - eigentlich sollte diese Verarbeitung anderswo erfolgen und dieses Skript nur die template engine sein
	# erzeuge String für Verkaufseinheit: "123€ pro Stück"
	if len(data.get("PREIS","")) > 1:
		# wenn der Preis numerisch ist, standardmäßig Verkaufseinheit = Stück
		if len(data.get("VERKAUFSEINHEIT","")) < 1 and re.match("[0-9]",data.get("PREIS","")):
			data["VERKAUFSEINHEIT"]=u"Stück"
		
		# Wenn Verkaufseinheit gesetzt, "pro ..." ergänzen
		# außer wenn es mit "bei" anfängt, denn "pro bei" ist Schmarrn.
		if len(data.get("VERKAUFSEINHEIT","")) > 0 and not data["VERKAUFSEINHEIT"].startswith("bei") :
			data["VERKAUFSEINHEIT"] = "pro " + data["VERKAUFSEINHEIT"]
	else:
		# keine Einheit anzeigen, wenn Preis leer oder "-"
		data["VERKAUFSEINHEIT"]=""
	
	# Alle Texte ersetzen
	for element in etikett.iter("*"):
		for [key,value] in data.items():
			if len(key)==0:
				continue # überspringe leere keys
			if element.tail is not None:
				element.tail=element.tail.replace(key,value)
			if element.text is not None:
				element.text=element.text.replace(key,value)
	for e in makeBarcodeXMLElements(createEAN8(data["ID"])):
		etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").append(e)
	etikett.find(".//{http://www.w3.org/2000/svg}g[@id='barcode']").set("id","barcode"+str(etikettNum))
	return etikett

# Etiketten-IDs werden auf der Kommandozeile angegeben
etikettIds=deepcopy(sys.argv)
etikettIds.pop(0) # Argumente beginnen erst bei sys.argv[1]

if (len(etikettIds)==0): # Fehler vermeiden: wenn leere Ausgabe gefordert, erzeuge eine leere Seite, statt garnix
	etikettIds=[None]

# Einzelseiten erzeugen
pageNum=0
pages=[]
while len(etikettIds)>0:
	page=deepcopy(template)
	pageNum=pageNum+1
	pages.append(pageNum)
	for etikettNum in range(0,24):
		if len(etikettIds)==0:
			# keine weiteren Etiketten zu drucken
			break
		etikettId=etikettIds.pop(0) # hole erste zu druckende ID aus der Liste
		if (etikettId == None or etikettId == "None"):
			continue # Lücke lassen, z.B. wenn ein Teil des Etikettenbogens schon verbraucht ist
		page.getroot().append(makeEtikett(etikettId,etikettNum))
	page.write("./temp/output-etikettenpapier-%d.svg" % pageNum)
	if os.system("inkscape ./temp/output-etikettenpapier-%d.svg --export-pdf=./temp/output-etikettenpapier-%d.pdf" % (pageNum,pageNum)) != 0:
		raise Exception("inkscape failed")
# Seiten aneinanderhängen
pdftkCmd = "pdftk "
for pageNum in pages:
	pdftkCmd = pdftkCmd + "./temp/output-etikettenpapier-%d.pdf " % pageNum
pdftkCmd = pdftkCmd + " cat output ./temp/output-etikettenpapier.pdf"
if os.system(pdftkCmd) != 0:
	raise Exception("pdftk failed")
# Aufräumen
for pageNum in pages:
	os.remove("./temp/output-etikettenpapier-%d.pdf" % pageNum)
	os.remove("./temp/output-etikettenpapier-%d.svg" % pageNum)
