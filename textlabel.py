#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from __future__ import unicode_literals



"""
create and print labels with text, where the font is resized to maximum possible size

(C) Max Gaukler 2015
<development@maxgaukler.de>
unlimited usage allowed, see LICENSE file
"""

from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
import reportlab.lib.enums
import sys
import subprocess

# aaargh we should move to python3! then all codecs stuff would be unnecessary
import codecs


# the preferred solution would use KeepInFrame(method='shrink'), but at least with the code from https://stackoverflow.com/questions/12014573/reportlab-how-to-auto-resize-text-to-fit-block it did not work as expected when using splitLongWords=0 in the paragraph style.
# therefore we just use the basic methods and determine the font size by hand

# create a PDF label with centered text of the given fontsize
# raise reportlab.platypus.doctemplate.LayoutError if fontsize is too large to fit everything
def makeLabel(text, fontsize):
    # TODO correctly escape text - is this enough?
    text=text.replace("<", "&lt;");
    text=text.replace(">", "&gt;");
    text=text.replace("\n", "<br/>")
    width=5.9*cm
    height=2.9*cm
    margin=0.1*cm

    style = ParagraphStyle(name='')
    style.fontSize=fontsize
    style.leading=style.fontSize*1.2 # line spacing
    style.alignment=reportlab.lib.enums.TA_CENTER
    style.splitLongWords=0
    paragraph = Paragraph(text, style)
    # query how large the given text will be
    requiredWidth, requiredHeight=paragraph.wrap(width-2*margin, height-2*margin)
    if requiredHeight > height-2*margin or requiredWidth>width-2*margin:
        # oops, font too large
        raise reportlab.platypus.doctemplate.LayoutError
        
    c = Canvas('./temp/textlabel.pdf', pagesize=(width, height))
    paragraph.drawOn(c, margin, (height-requiredHeight)/2)
    c.save()

# generate a label with the largest possible fontsize to fit all text
def makeLabelAutosize(text):
    maxSize=100
    fontsize=0
    success=False
    # binary search for the right fontsize
    for n in range(9):
        largerSize=fontsize+maxSize*pow(2, -n)
        try:
            makeLabel(text, largerSize)
            success=True
        except reportlab.platypus.doctemplate.LayoutError:
            # fontsize was too large, do not increase
            continue
        fontsize=largerSize
    if not success:
        raise Exception("cannot create label, even with smallest fontsize")

""" print the label that was saved by the last successful call to makeLabel*() """
def printRecentLabel():
    subprocess.call("lpr -P Zebra-EPL2-Label ./temp/textlabel.pdf".split(" "))

""" read all data from stdin and return it as a unicode object """
def readStdin():
    text=sys.stdin.read()
    if type(text)!=unicode:
        text=codecs.decode(text,'utf8')
    return text

def main():
    if "--multiple-labels" in sys.argv:
        for line in readStdin().split("\n"):
            if line=="":
                continue
            makeLabelAutosize(line)
            if "--print" in sys.argv:
                printRecentLabel()
    elif "--one-label" in sys.argv:
        makeLabelAutosize(readStdin())
        if "--print" in sys.argv:
            printRecentLabel()
    else:
        print "usage: textlabel.py (--multiple-labels|--one-label) [--print]"
        print "input is read from stdin."
        print "and printed as one big label (for --one-label), or as separate labels - one per line - when --multiple-labels is given"
        print "if --print is not given, just create the PDF. (the last label overwrites the previous ones)"
        sys.exit(1)
    sys.exit(0)

    
    

if __name__=="__main__":
    main()
