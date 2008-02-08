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
                    ('share/pixmaps',             ['data/multilist.png']),                
                    ('share/applications/hildon', ['data/multilist.desktop']),           
                    ('share/dbus-1/services',     ['data/multilist.service']),      
                    ]
      ) 