#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__author__ = 'Max Gaukler'
__license__ = 'unlicense'

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
from xml.sax.saxutils import escape
import reportlab.lib.enums
import sys
import subprocess
import os
import codecs  # aaargh we should move to python3! then all codecs stuff would be unnecessary - why not? :D


# the preferred solution would use KeepInFrame(method='shrink'), but at least with the code from
# https://stackoverflow.com/questions/12014573/reportlab-how-to-auto-resize-text-to-fit-block
# it did not work as expected when using splitLongWords=0 in the paragraph style.
# therefore we just use the basic methods and determine the font size by hand


def make_label(text, fontsize):
    """
    create a PDF label with centered text of the given font size
    
    raises reportlab.platypus.doctemplate.LayoutError if font size is too large to fit everything

    CAUTION: BUG: broken in newer ReportLab versions, works in reportlab==3.0.
    Test case: For input "asdfasdfsdafasdfasdf", the output should not be cut off.
    """
    # correctly escape text - is this enough?
    text = escape(text)
    text = text.replace("\n", "<br/>")
    width = 5.9 * cm
    height = 2.9 * cm
    margin = 0.1 * cm

    style = ParagraphStyle(name='')
    style.fontSize = fontsize
    style.leading = style.fontSize * 1.2  # line spacing
    style.alignment = reportlab.lib.enums.TA_CENTER
    style.splitLongWords = 0
    paragraph = Paragraph(text, style)
    # query how large the given text will be
    required_width, required_height = paragraph.wrap(width - 2 * margin, height - 2 * margin)
    if required_height > height - 2 * margin or required_width > width - 2 * margin:
        # oops, font too large
        raise reportlab.platypus.doctemplate.LayoutError

    c = Canvas(output_dir + 'textlabel.pdf', pagesize=(width, height))
    paragraph.drawOn(c, margin, (height - required_height) / 2)
    c.save()


def make_label_auto_size(text):
    """
    generate a label with the largest possible fontsize to fit all text
    :type text: str
    :param text: the text to print on the label
    """
    max_size = 100
    fontsize = 0
    success = False
    # binary search for the right fontsize
    for n in range(9):
        larger_size = fontsize + max_size * pow(2, -n)
        try:
            make_label(text, larger_size)
            success = True
        except reportlab.platypus.doctemplate.LayoutError:
            # fontsize was too large, do not increase
            continue
        fontsize = larger_size
    if not success:
        raise Exception("cannot create label, even with smallest fontsize")


""" print the label that was saved by the last successful call to make_label*() """


def print_recent_label():
    subprocess.call(("lpr -P Zebra-EPL2-Label " + output_dir + "textlabel.pdf").split(" "))


""" read all data from stdin and return it as a unicode object """


def read_stdin():
    text = sys.stdin.read()
    if type(text) != unicode:
        text = codecs.decode(text, 'utf8')
    return text


def main():
    if "--multiple-labels" in sys.argv:
        for line in read_stdin().split("\n"):
            if line == "":
                continue
            make_label_auto_size(line)
            if "--print" in sys.argv:
                print_recent_label()
    elif "--one-label" in sys.argv:
        make_label_auto_size(read_stdin())
        if "--print" in sys.argv:
            print_recent_label()
    else:
        print "usage: textlabel.py (--multiple-labels|--one-label) [--print]"
        print "input is read from stdin."
        print "and printed as one big label (for --one-label), " \
              "or as separate labels - one per line - when --multiple-labels is given"
        print "if --print is not given, just create the PDF. (the last label overwrites the previous ones)"
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    # <editor-fold desc="make temp dir">
    output_dir = './temp/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # </editor-fold>
    main()
