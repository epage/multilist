import os

__pretty_app_name__ = "Multilist"
__app_name__ = "multilist"
__version__ = "0.3.11"
__build__ = 2
_data_path_ = os.path.join(os.path.expanduser("~"), ".multilist")
__app_magic__ = 0xdeadbeef
_user_settings_ = "%s/settings.ini" % _data_path_
_user_logpath_ = "%s/multilist.log" % _data_path_
