from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

from boxbranding import getImageDistro
import six

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, \
	ConfigNumber, ConfigSelection, ConfigYesNo, ConfigText

PluginLanguageDomain = "AutoTimer"
PluginLanguagePath = "Extensions/AutoTimer/locale"


def removeBad(val):
	if six.PY3:
		return val.replace('\x86', '').replace('\x87', '')
	else:
		return val.replace('\xc2\x86', '').replace('\xc2\x87', '')


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)

config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigEnableDisable(default=True)
config.plugins.autotimer.delay = ConfigNumber(default=3)
config.plugins.autotimer.editdelay = ConfigNumber(default=3)

default_unit = "hour"
if getImageDistro() in ('beyonwiz', 'teamblue', 'openatv', 'openvix', 'opendroid'):  # distros that want default polling in minutes
	default_unit = "minute"
config.plugins.autotimer.unit = ConfigSelection(choices=[
		("hour", _("Hour")),
		("minute", _("Minute"))
	], default=default_unit
)

default_interval = {"hour": 4, "minute": 30}  # default poll every 4 hours or 30 minutes
if getImageDistro() in ('teamblue', 'openatv'):
	default_interval["minute"] = 240
config.plugins.autotimer.interval = ConfigNumber(default=default_interval[config.plugins.autotimer.unit.value])

config.plugins.autotimer.timeout = ConfigNumber(default=5)
config.plugins.autotimer.popup_timeout = ConfigNumber(default=5)
config.plugins.autotimer.check_eit_and_remove = ConfigYesNo(default=False)
config.plugins.autotimer.always_write_config = ConfigYesNo(default=True)
config.plugins.autotimer.refresh = ConfigSelection(choices=[
		("none", _("None")),
		("auto", _("Only AutoTimers created during this session")),
		("all", _("All non-repeating timers"))
	], default="all"
)
config.plugins.autotimer.try_guessing = ConfigEnableDisable(default=True)
config.plugins.autotimer.editor = ConfigSelection(choices=[
		("epg", _("Import from EPG")),
		("plain", _("Classic")),
		("wizard", _("Wizard"))
	], default="plain"
)
config.plugins.autotimer.addsimilar_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.onlyinstandby = ConfigEnableDisable(default=False)
config.plugins.autotimer.add_autotimer_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.add_name_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.disabled_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.show_in_plugins = ConfigYesNo(default=False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.autotimer.fastscan = ConfigYesNo(default=False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default=True)
config.plugins.autotimer.notifsimilar = ConfigYesNo(default=True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default=0)
config.plugins.autotimer.enable_multiple_timer = ConfigSelection(choices=[
		("0", _("No")),
		("s", _("If specified services")),
		("b", _("If specified bouquets")),
		("sb", _("If specified services or bouquets"))
	], default="0"
)
config.plugins.autotimer.show_help = ConfigYesNo(default=True)
config.plugins.autotimer.skip_during_records = ConfigYesNo(default=False)
config.plugins.autotimer.skip_during_epgrefresh = ConfigYesNo(default=False)

try:
	xrange = xrange
	iteritems = lambda d: six.iteritems(d)
	itervalues = lambda d: six.itervalues(d)
except NameError:
	xrange = range
	iteritems = lambda d: d.items()
	itervalues = lambda d: d.values()

__all__ = ['_', 'config', 'iteritems', 'itervalues', 'xrange']
