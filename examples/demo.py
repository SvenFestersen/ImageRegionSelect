#!/usr/bin/env python
#
#       demo.py
#       
#       Copyright 2009 Sven Festersen <sven@sven-festersen.de>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
"""
This is a simple example application that lets you select a region in
an image.

Image file by alcomm (http://www.flickr.com/photos/alcomm/217097889/)
"""


import gtk
import pygtk

from image_region_select.region_select import ImageRegionSelect

def cb_selection_changed(widget, selection, label):
    if selection:
        label.set_text("Selection: %sx%s" % (selection.width, selection.height))
    else:
        label.set_text("Selection: None")

if __name__ == "__main__":
    
    w = gtk.Window()
    w.connect("destroy", gtk.main_quit)
    
    vbox = gtk.VBox()
    w.add(vbox)
    
    #irs = ImageRegionSelect("test.jpg")
    irs = ImageRegionSelect(pixbuf=gtk.gdk.pixbuf_new_from_file("test.jpg"))
    vbox.pack_start(irs)
    
    l = gtk.Label("Selection: None")
    l.set_alignment(0.0, 0.5)
    vbox.pack_start(l, False, False)
    
    irs.connect("selection-changed", cb_selection_changed, l)
    
    w.show_all()
    gtk.main()
