#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
#
#

from distutils.core import setup  

setup(name='multilist',
       version='0.3.0',
       scripts=['src/multilist'],
       packages=['multilistclasses'],
       package_dir={'multilistclasses': 'src/multilistclasses'},
       data_files = [
                    ('share/icons/hicolor/26x26/hildon', ['data/low/multilist.png']),
	      	    ('share/icons/hicolor/40x40/hildon', ['data/high/multilist.png']),
		    ('share/icons/hicolor/scalable/hildon', ['data/scale/multilist.png']),
                    #('share/pixmaps',             ['data/multilist.png']),                
                    ('share/applications/hildon', ['data/multilist.desktop']),           
                    ('share/dbus-1/services',     ['data/multilist.service']),      
                    # I18N
                    ('share/locale/de/LC_MESSAGES', ['locale/de/LC_MESSAGES/multilist.mo']),
                    ('share/locale/ru/LC_MESSAGES', ['locale/ru/LC_MESSAGES/multilist.mo']),
                    ]
      ) 
