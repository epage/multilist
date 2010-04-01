#!/usr/bin/python2.5

import os
import sys

try:
	import py2deb
except ImportError:
	import fake_py2deb as py2deb

import constants


__appname__ = constants.__app_name__
__description__ = """Simple list management application
.
Homepage: http://multilist.garage.maemo.org/
"""
__author__ = "Christoph Wurstle"
__email__ = "n800@axique.net"
__version__ = constants.__version__
__build__ = constants.__build__
__changelog__ = """
0.3.7
* Corrected the bug tracker link

0.3.6
* Adding filtering for new and complete in addition to all and active

0.3.5
* Bugfix: Fixing the application launcher

0.3.4
* Making rotation configurable in the Settings window
* Persisting full-screen / rotation settings

0.3.3
* Rotation support
* Turned the settings dialog into a window

0.3.2
* Massive code cleanup
* Re-arrangement of GTK Menus
* Added Maemo 5 Menu
* Moved Active/All filter to menu
* Moved Checkout All to menu
* Improved Search bar
* Removed unnesary UI elements
* Switched to real inconsistent check boxes for tasks
* Switching the settings dialog to be more Maemo 5 like

0.3.1
* I18N, extract de.po, add ru.po.

0.3.0
* Initial Release.
"""


__postinstall__ = """#!/bin/sh -e

gtk-update-icon-cache -f /usr/share/icons/hicolor
rm -f ~/.multilist/multilist.log
"""


def find_files(path, root):
	print path, root
	for unusedRoot, dirs, files in os.walk(path):
		for file in files:
			if file.startswith(root+"-"):
				print "\t", root, file
				fileParts = file.split("-")
				unused, relPathParts, newName = fileParts[0], fileParts[1:-1], fileParts[-1]
				assert unused == root
				relPath = os.sep.join(relPathParts)
				yield relPath, file, newName


def unflatten_files(files):
	d = {}
	for relPath, oldName, newName in files:
		if relPath not in d:
			d[relPath] = []
		d[relPath].append((oldName, newName))
	return d


def build_package(distribution):
	try:
		os.chdir(os.path.dirname(sys.argv[0]))
	except:
		pass

	py2deb.Py2deb.SECTIONS = py2deb.SECTIONS_BY_POLICY[distribution]
	p = py2deb.Py2deb(__appname__)
	p.prettyName = constants.__pretty_app_name__
	p.description = __description__
	p.bugTracker = "https://bugs.maemo.org/enter_bug.cgi?product=Multilist"
	p.upgradeDescription = __changelog__.split("\n\n", 1)[0]
	p.author = __author__
	p.mail = __email__
	p.license = "gpl"
	p.depends = ", ".join([
		"python2.6 | python2.5",
		"python-gtk2 | python2.5-gtk2",
		"python-xml | python2.5-xml",
		"python-dbus | python2.5-dbus",
	])
	maemoSpecificDepends = ", python-osso | python2.5-osso, python-hildon | python2.5-hildon"
	p.depends += {
		"debian": ", python-glade2",
		"diablo": maemoSpecificDepends,
		"fremantle": maemoSpecificDepends + ", python-glade2",
	}[distribution]
	p.section = {
		"debian": "editors",
		"diablo": "user/office",
		"fremantle": "user/office",
	}[distribution]
	p.arch = "all"
	p.urgency = "low"
	p.distribution = "diablo fremantle debian"
	p.repository = "extras"
	p.changelog = __changelog__
	p.postinstall = __postinstall__
	p.icon = {
		"debian": "26x26-multilist.png",
		"diablo": "26x26-multilist.png",
		"fremantle": "40x40-multilist.png", # Fremantle natively uses 48x48
	}[distribution]
	p["/usr/bin"] = [ "multilist.py" ]
	for relPath, files in unflatten_files(find_files(".", "locale")).iteritems():
		fullPath = "/usr/share/locale"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	for relPath, files in unflatten_files(find_files(".", "src")).iteritems():
		fullPath = "/usr/lib/multilist"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	p["/usr/share/applications/hildon"] = ["multilist.desktop"]
	p["/usr/share/icons/hicolor/26x26/hildon"] = ["26x26-multilist.png|multilist.png"]
	p["/usr/share/icons/hicolor/40x40/hildon"] = ["40x40-multilist.png|multilist.png"]
	p["/usr/share/icons/hicolor/scalable/hildon"] = ["scale-multilist.png|multilist.png"]

	if distribution == "debian":
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=True,
			tar=False,
			changes=False,
			dsc=False,
		)
		print "Building for %s finished" % distribution
	else:
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=False,
			tar=True,
			changes=True,
			dsc=True,
		)
		print "Building for %s finished" % distribution


if __name__ == "__main__":
	if len(sys.argv) > 1:
		try:
			import optparse
		except ImportError:
			optparse = None

		if optparse is not None:
			parser = optparse.OptionParser()
			(commandOptions, commandArgs) = parser.parse_args()
	else:
		commandArgs = None
		commandArgs = ["diablo"]
	build_package(commandArgs[0])