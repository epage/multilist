#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Multilist.

Multilist is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Multilist is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Multilist.  If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2008 Christoph Würstle
"""

import gtk
import gobject
import logging
import pango


try:
	_
except NameError:
	_ = lambda x: x


_moduleLogger = logging.getLogger(__name__)


class Columns_dialog(gtk.VBox):

	def __init__(self,db,liststorehandler):
		gtk.VBox.__init__(self,homogeneous=False, spacing=0)

		self.db=db
		self.liststorehandler=liststorehandler

		#serverbutton=gtk.ToggleButton("SyncServer starten")
		#serverbutton.connect("clicked",self.startServer,(None,))
		#self.pack_start(serverbutton, expand=False, fill=True, padding=1)
		#print "x1"

		frame=gtk.Frame(_("Columns"))
		self.framebox=gtk.VBox(homogeneous=False, spacing=0)

		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)

		self.scrolled_window.add_with_viewport(self.framebox)

		i=1 #uid can not be shown
		while self.liststorehandler.get_colname(i)!=None:
			name=str(self.liststorehandler.get_colname(i))
			checkbutton=gtk.CheckButton(name)
			if self.db.ladeDirekt("showcol_"+name)=="1":
				checkbutton.set_active(True)

			self.framebox.pack_start(checkbutton)
			i=i+1

		frame.add(self.scrolled_window)
		self.pack_start(frame, expand=True, fill=True, padding=1)

	def is_col_selected(self, icol):
		children=self.framebox.get_children()
		if icol<len(children):
			return children[icol].get_active()
		else:
			return None

	def save_column_setting(self):
		i=1 #uid can not be shown
		while self.liststorehandler.get_colname(i)!=None:
			name=str(self.liststorehandler.get_colname(i))
			if self.is_col_selected(i-1)==True:
				self.db.speichereDirekt("showcol_"+name,"1")
			else:
				self.db.speichereDirekt("showcol_"+name,"0")
			i=i+1


class CellRendererTriple(gtk.GenericCellRenderer):
	__gproperties__ = {
		"status": (gobject.TYPE_STRING, "Status",
		"Status", "", gobject.PARAM_READWRITE),
	}

	__gsignals__ = {
		'status_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_INT,gobject.TYPE_STRING)),
	}

	def __init__(self):
		#self.__gobject_init__()
		#gtk.GenericCellRenderer.__init__(self,*args,**kwargs)
		gtk.GenericCellRenderer.__init__(self)
		#self.__gobject_init__()
		self.status=-1
		self.xpad = 2
		self.ypad = 2
		self.mode = gtk.CELL_RENDERER_MODE_ACTIVATABLE
		self.xpad = -2; self.ypad = -2
		self.xalign = 0.5; self.yalign = 0.5
		self.active = 0
		self.widget=None
		self.last_cell=None
		self.connect('editing-started', self.on_clicked)

	def do_set_property(self,property,value):
		setattr(self, property.name, value)

	def do_get_property(self, property):
		return getattr(self, property.name)

	def get_layout(self, widget):
		'''Gets the Pango layout used in the cell in a TreeView widget.'''

		layout = pango.Layout(widget.get_pango_context())
		layout.set_width(-1)    # Do not wrap text.

		layout.set_text('  ')

		return layout

	def on_get_size(self, widget, cell_area=None):
		xpad = 2
		ypad = 2

		xalign = 0
		yalign = 0.5

		layout = self.get_layout(widget)
		width, height = layout.get_pixel_size()

		x_offset = xpad
		y_offset = ypad

		if cell_area:

			x_offset = xalign * (cell_area.width - width)
			x_offset = max(x_offset, xpad)
			x_offset = int(round(x_offset, 0))

			y_offset = yalign * (cell_area.height - height)
			y_offset = max(y_offset, ypad)
			y_offset = int(round(y_offset, 0))

		width  = width  + (xpad * 2)
		height = height + (ypad * 2)

		return x_offset, y_offset, width, height

	def on_clicked(self,  widget, data):
		print widget,data

	def clicked(self, widget, data1=None):
		x,y=widget.get_pointer()
		widget.realize()

		path=widget.get_path_at_pos(x,y)

		#print "a",widget.get_cursor()
		#print path

		path=widget.get_cursor()[0]

		if path!=None:
			irow=path[0]	#path[0][0]-1
			rect=widget.get_cell_area(irow, widget.get_column(0)) #FixME 0 is hardcoded
			if x<rect.x+rect.width:
				self.emit("status_changed",irow,self.status)
		else:
			return

			#workarround -1 means last item, because bug in treeview?!
			#print "not in list"
			rect=widget.get_visible_rect() #widget.get_cell_area(-1, widget.get_column(0))
			#print rect.x,rect.y,rect.width,rect.height,x,y
			irow=-1
			rect=widget.get_cell_area(0, widget.get_column(0)) #FixME 0 is hardcoded
			if x<rect.x+rect.width:
				self.emit("status_changed",irow,"-1")

	def on_render(self, window, widget, background_area, cell_area, expose_area, flags ):
		if (self.widget==None):
			#print widget
			self.widget=widget
			self.widget.connect("cursor-changed",self.clicked) #button-press-event

		self.last_cell=cell_area

		x=int(cell_area.x+(cell_area.width-2)/2-(cell_area.height-2)/2)
		y=int(cell_area.y+1)
		height=int(cell_area.height-2)
		width=int(height)

		if (self.status=="1"):
			widget.style.paint_check(window,gtk.STATE_NORMAL, gtk.SHADOW_IN,cell_area, widget, "cellradio",x,y,width,height)
		elif (self.status=="0"):
			#width=height
			height=height-3
			width=height

			widget.style.paint_flat_box(window, gtk.STATE_NORMAL, gtk.SHADOW_NONE, cell_area, widget, "cellunselected",x,y,width,height)

			widget.style.paint_hline(window, gtk.STATE_NORMAL,cell_area, widget, "cellunselected",x,x+width,y)
			widget.style.paint_hline(window, gtk.STATE_NORMAL,cell_area, widget, "cellunselected",x,x+width,y+height)
			widget.style.paint_vline(window, gtk.STATE_NORMAL,cell_area, widget, "cellunselected",y,y+height,x)
			widget.style.paint_vline(window, gtk.STATE_NORMAL,cell_area, widget, "cellunselected",y,y+height,x+width)

		else:
			widget.style.paint_diamond(window, gtk.STATE_NORMAL, gtk.SHADOW_IN, cell_area, widget, "cellunselected",x,y,width,height)

		#widget.show_all()
		#print "render"
		pass

	def on_start_editing(self, event, widget, path, background_area, cell_area, flags):
		print "on_start_editing",path
		return None

	def on_activate(self, event, widget, path, background_area, cell_area, flags):
		print "activate",path
		return False


class CellRendererCombo2(gtk.GenericCellRenderer):
	__gproperties__ = {
		"text": (gobject.TYPE_STRING, "text",
		"Text", "", gobject.PARAM_READWRITE),
	}

	__gsignals__ = {
		'status_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_INT,gobject.TYPE_STRING)),
	}

	def __init__(self):
		#self.__gobject_init__()
		#gtk.GenericCellRenderer.__init__(self,*args,**kwargs)
		gtk.GenericCellRenderer.__init__(self)
		#self.__gobject_init__()
		self.status=-1
		self.xpad = 2
		self.ypad = 2
		self.mode = gtk.CELL_RENDERER_MODE_ACTIVATABLE
		self.xpad = -2
		self.ypad = -2
		self.xalign = 0.5
		self.yalign = 0.5
		self.active = 0
		self.widget=None
		self.last_cell=None
		self.text="(none)"
		self.connect('editing-started', self.on_clicked)

	def do_set_property(self,property,value):
		#print property,value
		setattr(self, property.name, value)

	def do_get_property(self, property):
		return getattr(self, property.name)

	def get_layout(self, widget):
		'''Gets the Pango layout used in the cell in a TreeView widget.'''

		layout = pango.Layout(widget.get_pango_context())
		layout.set_width(-1)    # Do not wrap text.

		layout.set_text(self.text)

		return layout

	def on_get_size(self, widget, cell_area=None):
		xpad = 2
		ypad = 2

		xalign = 0
		yalign = 0.5

		layout = self.get_layout(widget)
		width, height = layout.get_pixel_size()

		x_offset = xpad
		y_offset = ypad

		if cell_area:

			x_offset = xalign * (cell_area.width - width)
			x_offset = max(x_offset, xpad)
			x_offset = int(round(x_offset, 0))

			y_offset = yalign * (cell_area.height - height)
			y_offset = max(y_offset, ypad)
			y_offset = int(round(y_offset, 0))

		width  = width  + (xpad * 2)
		height = height + (ypad * 2)

		return x_offset, y_offset, width, height

	def on_clicked(self,  widget, data):
		print widget,data

	def clicked(self, widget, data1=None):
		return
		x,y=widget.get_pointer()
		widget.realize()

		#path=widget.get_path_at_pos(x,y)

		path=widget.get_cursor()[0]

		if path!=None:
			irow=path[0]	#path[0][0]-1
			rect=widget.get_cell_area(irow, widget.get_column(0)) #FixME 0 is hardcoded
			if x<rect.x+rect.width:
				self.emit("status_changed",irow,self.status)
		else:
			return

			#workarround -1 means last item, because bug in treeview?!
			#print "not in list"
			rect=widget.get_visible_rect() #widget.get_cell_area(-1, widget.get_column(0))
			#print rect.x,rect.y,rect.width,rect.height,x,y
			irow=-1
			rect=widget.get_cell_area(0, widget.get_column(0)) #FixME 0 is hardcoded
			if x<rect.x+rect.width:
				self.emit("status_changed",irow,"-1")

	def on_render(self, window, widget, background_area, cell_area, expose_area, flags ):
		if (self.widget==None):
			self.widget=widget
			self.widget.connect("cursor-changed",self.clicked) #button-press-event

		self.last_cell=cell_area

		x=int(cell_area.x+(cell_area.width-2)/2-(cell_area.height-2)/2)
		y=int(cell_area.y+1)
		height=int(cell_area.height-2)
		width=int(height)

		widget.style.paint_layout(window,gtk.STATE_NORMAL, True, cell_area, widget, "cellradio",x,y,self.get_layout(widget))

		#widget.show_all()

	def on_start_editing(self, event, widget, path, background_area, cell_area, flags):
		print "on_start_editing",path
		return None

	def on_activate(self, event, widget, path, background_area, cell_area, flags):
		print "activate",path
		return False


gobject.type_register(CellRendererCombo2)
gobject.type_register(CellRendererTriple)


class View(gtk.VBox):

	def __init__(self,db,liststorehandler,parent_window):
		self.db=db
		self.parent_window=parent_window
		self.liststorehandler = liststorehandler

		gtk.VBox.__init__(self,homogeneous=False, spacing=0)

		logging.info("libview, init")

		self.scrolled_window = None
		self.reload_view()

		"""
		bearbeitenFrame=gtk.Frame("Verteilung kopieren nach")
		bearbeitenvBox=gtk.VBox(homogeneous=False, spacing=0)
		
		bearbeitenhBox=gtk.HBox(homogeneous=False, spacing=0)
		self.comboKlassen = gtk.combo_box_new_text()
		bearbeitenhBox.pack_start(self.comboKlassen, expand=False, fill=True, padding=0)
		button=gtk.Button("Kopieren")
		button.connect("clicked", self.kopiereStoffverteilung, None)
		bearbeitenhBox.pack_start(button, expand=False, fill=True, padding=0)
		
		label=gtk.Label("   ")
		bearbeitenhBox.pack_start(label, expand=False, fill=True, padding=0)
		
		button=gtk.Button("Export in CSV-Datei")
		button.connect("clicked", self.exportStoffverteilung, None)
		bearbeitenhBox.pack_start(button, expand=False, fill=True, padding=0)
		
		bearbeitenvBox.pack_start(bearbeitenhBox, expand=False, fill=True, padding=0)
		
	
		bearbeitenFrame.add(bearbeitenvBox)
		self.pack_start(bearbeitenFrame, expand=False, fill=True, padding=0)
		"""

		#self.connect("unmap", self.speichere) 
		#self.connect("map", self.ladeWirklich) 

		#self.show_all()

		#print "libstoffverteilung 9: ",time.clock()

	def loadList(self):
		ls=self.liststorehandler.get_liststore()
		self.treeview.set_model(ls)
		#self.tvcolumn[i].add_attribute( self.cell[i], "active", 1)
		#print "setup",ls

	def col_edited(self,cell, irow, new_text,icol=None):
		if (irow!=4):
			self.liststorehandler.update_row(irow,icol,new_text)
		else:
			print cell, irow, new_text,icol

	def col_toggled(self,widget,irow, status ):
		#print irow,ls[irow][1],status
		ls=self.treeview.get_model()

		if self.liststorehandler.selection.get_status()=="0":
			if ls[irow][1]=="0":
				self.liststorehandler.update_row(irow,1,"1")
			else:
				self.liststorehandler.update_row(irow,1,"0")
		else:
			if ls[irow][1]=="1":
				self.liststorehandler.update_row(irow,1,"-1")
			elif ls[irow][1]=="0":
				self.liststorehandler.update_row(irow,1,"1")
			else:
				self.liststorehandler.update_row(irow,1,"0")

		#self.tvcolumn[i].set_attributes( self.cell[i], active=i)

	def convert(self,s):
		#print s
		if (s=="1"):
			return 1
		else:
			return 0

	def del_active_row(self):
		path, col = self.treeview.get_cursor()
		#print path, col
		if path!=None:
			irow=path[0]
			row_iter=self.treeview.get_model().get_iter(path)
			self.liststorehandler.del_row(irow,row_iter)

		#treemodel.get_iter()

	def sort_func_function(self,model, iter1, iter2, data=None):
		print "sorting"

	def reload_view(self):
		# create the TreeView using liststore
		self.modelsort = gtk.TreeModelSort(self.liststorehandler.get_liststore())
		self.modelsort.set_sort_column_id(2, gtk.SORT_ASCENDING)

		self.treeview = gtk.TreeView(self.modelsort)
		self.treeview.set_headers_visible(True)

		self.cell=range(self.liststorehandler.get_colcount())
		self.tvcolumn=range(self.liststorehandler.get_colcount())

		m = self.liststorehandler.get_unitsstore()

		for i in range(self.liststorehandler.get_colcount()):
			if i>5:
				default="0"
			else:
				default="1"
			if self.db.ladeDirekt("showcol_"+str(self.liststorehandler.get_colname(i)),default)=="1":

				if (i==1):
					self.cell[i] = CellRendererTriple()
					self.tvcolumn[i] = 	gtk.TreeViewColumn(self.liststorehandler.get_colname(i),self.cell[i])
					self.cell[i].connect( 'status_changed', self.col_toggled)
					self.tvcolumn[i].set_attributes( self.cell[i], status=i)
				elif (i==3)or(i==4)or(i==6):
					self.cell[i] = gtk.CellRendererCombo()
					self.tvcolumn[i] = 	gtk.TreeViewColumn(self.liststorehandler.get_colname(i),self.cell[i])
					self.cell[i].set_property("model",m)
					self.cell[i].set_property('text-column', i)
					self.cell[i].set_property('editable',True)
					self.cell[i].connect("edited", self.col_edited,i) 
					self.tvcolumn[i].set_attributes( self.cell[i], text=i)
				else:
					self.cell[i] = gtk.CellRendererText()
					self.tvcolumn[i] = gtk.TreeViewColumn(self.liststorehandler.get_colname(i),self.cell[i])
					self.cell[i].set_property('editable',True)
					self.cell[i].set_property('editable-set',True)
					self.cell[i].connect("edited", self.col_edited,i)
					#self.cell[i].connect("editing-canceled", self.col_edited2,i) 
					self.tvcolumn[i].set_attributes(self.cell[i], text=i)

				self.cell[i].set_property('cell-background', 'lightgray')
				self.tvcolumn[i].set_sort_column_id(i)
				self.tvcolumn[i].set_resizable(True)

				if (i>0):
					self.treeview.append_column(self.tvcolumn[i])

		# Allow NOT drag and drop reordering of rows
		self.treeview.set_reorderable(False)

		if self.scrolled_window != None:
			self.scrolled_window.destroy()

		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)

		self.scrolled_window.add(self.treeview)
		self.pack_start(self.scrolled_window, expand=True, fill=True, padding=0)
		self.loadList()

		self.show_all()
