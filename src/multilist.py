#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2008 Christoph Würstle
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

import os
import sys
import logging
import gettext

_moduleLogger = logging.getLogger(__name__)
gettext.install('multilist', unicode = 1)
sys.path.append('/usr/lib/multilist')


import constants
import multilist_gtk


if __name__ == "__main__":
	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	logging.basicConfig(level = logging.DEBUG, filename = constants._user_logpath_)
	_moduleLogger.info("multilist %s-%s" % (constants.__version__, constants.__build__))
	_moduleLogger.info("OS: %s" % (os.uname()[0], ))
	_moduleLogger.info("Kernel: %s (%s) for %s" % os.uname()[2:])
	_moduleLogger.info("Hostname: %s" % os.uname()[1])

	multilist_gtk.run_multilist()
