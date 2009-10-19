#!/usr/bin/env python
#
#       region_select.py
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
import cairo
import gobject
import gtk
import os
import pygtk

SELECTION_MODE_NORMAL = 0
SELECTION_MODE_FIXED = 1


def limit_point_to_rect(p, rect):
    x, y = p
    x = max(rect.x, min(rect.width, x))
    y = max(rect.y, min(rect.height, y))
    return x, y
    
def color_gdk_to_cairo(color):
    """
    Convert a gtk.gdk.Color to cairo color.
    
    @type color: gtk.gdk.Color
    @param color: the color to convert
    @return: a color in cairo format.
    """
    return (color.red / 65535.0, color.green / 65535.0, color.blue / 65535.0)
    
    
class ImageArea:
    
    def __init__(self, original, x, y, width, height):
        self.original = original
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
        original.copy_area(x, y, width, height, self.pixbuf, 0, 0)


class ImageRegionSelect(gtk.DrawingArea):
    
    __gsignals__ = {"selection-changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))}
    
    __gproperties__ = {"filename": (gobject.TYPE_STRING,
                                    "image file path",
                                    "Path to the image file.",
                                    "", gobject.PARAM_READWRITE),
                        "pixbuf": (gobject.TYPE_PYOBJECT, "pixbuf",
                                    "The pixbuf holding the current image.",
                                    gobject.PARAM_READWRITE)}
    
    def __init__(self, filename="", pixbuf=None):
        gtk.DrawingArea.__init__(self)
        self._filename = filename
        self._pixbuf = pixbuf
        self._mode = SELECTION_MODE_NORMAL
        
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.BUTTON_RELEASE_MASK|gtk.gdk.POINTER_MOTION_MASK)
        self.connect("expose-event", self._cb_expose_event)
        self.connect("button-press-event", self._cb_button_press_event)
        self.connect("button-release-event", self._cb_button_release_event)
        self.connect("motion-notify-event", self._cb_motion_notify_event)
        
        self._selecting = False
        
        self._selection_point_a = (0, 0)
        self._selection_point_b = (0, 0)
        self._selection_dimensions = (50, 40)
        
        self._load_image(filename)
        self._load_pixbuf(pixbuf)
        
    def do_get_property(self, property):
        if property.name == "filename":
            return self._filename
        elif property.name == "pixbuf":
            return self._pixbuf

    def do_set_property(self, property, value):
        if property.name == "filename" and value != self._filename:
            self._load_image(value)
        elif property.name == "pixbuf":
            self._load_pixbuf(value)
        
    def _cb_expose_event(self, widget, event):
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, \
                                event.area.width, event.area.height)
        context.clip()
        self.draw(context)
        
    def _cb_button_press_event(self, widget, event):
        rect = self._get_image_rect()
        self._selecting = True
        if self._mode == SELECTION_MODE_NORMAL:
            self._selection_point_a = limit_point_to_rect((event.x, event.y), rect,)
        elif self._mode == SELECTION_MODE_FIXED:
            w, h = self._selection_dimensions
            rect_small = gtk.gdk.Rectangle(rect.x + w / 2, rect.y + h / 2, rect.width - 2 * w, rect.height - 2 * h)
            self._selection_point_a = limit_point_to_rect((event.x, event.y), rect_small)
        
    def _cb_button_release_event(self, widget, event):
        self._selecting = False
        
        x0, y0 = self._selection_point_a
        x1, y1 = self._selection_point_b
        
        if self._mode == SELECTION_MODE_NORMAL:
            width = int(abs(x0 - x1))
            height = int(abs(y0 - y1))
            x = int(min(x0, x1))
            y = int(min(y0, y1))
        elif self._mode == SELECTION_MODE_FIXED:
            width, height = self._selection_dimensions
            x = int(self._selection_point_a[0] - width / 2)
            y = int(self._selection_point_a[1] - height / 2)
        
        if width > 0 and height > 0:
            selection = ImageArea(self._pixbuf, x, y, width, height)
            self.emit("selection-changed", selection)
        else:
            self.emit("selection-changed", None)
            
        self.queue_draw()

    def _cb_motion_notify_event(self, widget, event):
        rect = self._get_image_rect()
        if self._selecting and self._mode == SELECTION_MODE_NORMAL:
            self._selection_point_b = limit_point_to_rect((event.x, event.y), rect)
            self.queue_draw()
        elif self._selecting and self._mode == SELECTION_MODE_FIXED:
            w, h= self._selection_dimensions
            rect_small = gtk.gdk.Rectangle(rect.x + w / 2, rect.y + h / 2, rect.width - w / 2, rect.height - h / 2)
            self._selection_point_a = limit_point_to_rect((event.x, event.y), rect_small)
            self.queue_draw()
            
    def _get_image_rect(self):
        if not self._pixbuf:
            return self.get_allocation()
        else:
            return gtk.gdk.Rectangle(0, 0, self._pixbuf.get_width(), self._pixbuf.get_height())
        
    def draw(self, context):
        context.set_line_width(1)
        rect = self.get_allocation()
        
        c = color_gdk_to_cairo(self.get_style().bg[gtk.STATE_SELECTED])
        
        if self._pixbuf:
            context.set_source_pixbuf(self._pixbuf, 0, 0)
            context.rectangle(0, 0, self._pixbuf.get_width(), self._pixbuf.get_height())
            context.fill()
        
        x0, y0 = self._selection_point_a
        x1, y1 = self._selection_point_b
        
        if abs(x0 - x1) > 0 and abs(y0 - y1) > 0:
            context.set_source_rgba(c[0], c[1], c[2], 0.2)
            if self._mode == SELECTION_MODE_NORMAL:
                context.rectangle(x0 - 0.5, y0 - 0.5, x1 - x0, y1 - y0)
            else:
                w, h= self._selection_dimensions
                context.rectangle(x0 - w / 2 - 0.5, y0 - h / 2 - 0.5, w, h)
            context.fill_preserve()
            context.set_source_rgb(*c)
            context.stroke()
            
    def _load_image(self, filename):
        if filename and os.path.exists(filename):
            self._filename = filename
            self._pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
            
            width = self._pixbuf.get_width()
            height = self._pixbuf.get_height()
            
            self.set_size_request(width, height)
    
    def _load_pixbuf(self, pixbuf):
        if pixbuf:
            self._pixbuf = pixbuf
            
            width = self._pixbuf.get_width()
            height = self._pixbuf.get_height()
            
            self.set_size_request(width, height)
