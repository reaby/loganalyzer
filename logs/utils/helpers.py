import datetime
import re
from logs.utils.windows_versions import *
from logs.utils.macos_versions import *

CURRENT_VERSION = '26.1.0'

RED = "\033[1;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
CYAN = "\033[1;36m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"

LEVEL_NONE = 0
LEVEL_INFO = 1
LEVEL_WARNING = 2
LEVEL_CRITICAL = 3

_CACHE = dict()

clean_log = "<br>To make a clean log file, please follow these steps: <br><br>!"
"1) Restart OBS. <br>"
"2) Start your stream/recording for about 30 seconds. Make sure you replicate any issues as best you can, "
"which means having any games/apps open and captured, etc. <br>"
"3) Stop your stream/recording. <br>"
"4) Select Help > Log Files > Upload Current Log File. "
"Send that link via this troubleshooting tool or whichever support chat you are using."


def search(term, lines):
    return [s for s in lines if term in s]


def search_with_index(term, lines):
    return [[s, i] for i, s in enumerate(lines) if term in s]


def get_next_pos(old, lst):
    for new in lst:
        if new > old:
            return new


def get_scenes(lines):
    if "Scenes" in _CACHE:
        return _CACHE['Scenes']

    scenes = []
    for i, s in enumerate(lines):
        if '- scene' in s:
            scenes.append(i)
    _CACHE['Scenes'] = scenes
    return scenes


def get_obs_version_line(lines):
    if "ObsVersionLine" in _CACHE:
        return _CACHE['ObsVersionLine']

    version_lines = search('OBS', lines)
    correct_line = 0
    if 'already running' in version_lines[correct_line]:
        correct_line += 1
    if 'multiple instances' in version_lines[correct_line]:
        correct_line += 1

    _CACHE['ObsVersionLine'] = version_lines[correct_line]
    return version_lines[correct_line]


def get_obs_version(lines):
    if "ObsVersion" in _CACHE:
        return _CACHE['ObsVersion']

    version_line = get_obs_version_line(lines)
    if version_line.split()[0] == 'OBS':
        _CACHE['ObsVersion'] = version_line.split()[1]
        return version_line.split()[1]
    elif version_line.split()[2] == 'OBS':
        _CACHE['ObsVersion'] = version_line.split()[3]
        return version_line.split()[3]

    _CACHE['ObsVersion'] = version_line.split()[2]
    return version_line.split()[2]


def get_windows_version(lines):
    # Log line examples:
    # win 7: 19:39:17.395: Windows Version: 6.1 Build 7601 (revision: 24535; 64-bit)
    # win 10: 15:30:58.866: Windows Version: 10.0 Build 19041 (release: 2004; revision: 450; 64-bit)
    if "WindowsVersion" in _CACHE:
        return _CACHE['WindowsVersion']

    ver_lines = search('Windows Version:', lines)
    line = None
    if len(ver_lines) > 0:
        line = ver_lines[0]

    if not line:
        _CACHE['WindowsVersion'] = None
        return None

    match = winver_re.search(line)
    if not match:
        _CACHE['WindowsVersion'] = None
        return None

    ver = {
        "version": match.group("version"),
        "build": int(match.group("build")),
        "revision": int(match.group("revision")),
        "bits": int(match.group("bits")),
        "release": 0
    }

    # Older naming/numbering/etc
    if ver["version"] in winversions:
        v = winversions[ver["version"]]
        ver.update(v)
        _CACHE['WindowsVersion'] = ver
        return ver

    if ver["version"] == "10.0":
        if ver["build"] in win10versions:
            v = win10versions[ver["build"]]
            ver.update(v)
        _CACHE['WindowsVersion'] = ver
        return ver

    _CACHE['WindowsVersion'] = None
    return None


def get_mac_version(lines):
    if "MacVersion" in _CACHE:
        return _CACHE['MacVersion']

    is_mac = search('OS Name: Mac OS X', lines)
    mac_version = search('OS Version:', lines)
    version_line = None
    if len(is_mac) > 0 and len(mac_version) > 0:
        version_line = mac_version[0]

    if not version_line:
        _CACHE['MacVersion'] = None
        return

    match = macver_re.search(version_line)
    if not match:
        _CACHE['MacVersion'] = None
        return

    ver = {
        "major": match.group("major"),
        "minor": match.group("minor"),
        "full": match.group("major") + "." + match.group("minor")
    }

    if ver["full"] in macversions:
        v = macversions[ver["full"]]
        ver.update(v)
        _CACHE['MacVersion'] = ver
        return ver

    if ver["major"] in macversions:
        v = macversions[ver["major"]]
        ver.update(v)
        _CACHE['MacVersion'] = ver
        return ver

    _CACHE['MacVersion'] = None
    return


def get_monitor_refreshes(lines):
    if "refreshes" in _CACHE:
        return _CACHE['refreshes']

    refreshes = {}

    refresh_lines = search('refresh=', lines)
    refresh_re = re.compile(r"""
            (?i)
            output \s+ (?P<output_num>[0-9]+):
            .*
            refresh = (?P<refresh> [0-9.]+),
            .*
            name = (?P<name> .*)
            """, re.VERBOSE)

    for rl in refresh_lines:
        m = refresh_re.search(rl)

        if m is not None:
            if m.group("name") is not None:
                output = m.group("name").strip() + " (" + str(int(m.group("output_num")) + 1) + ")"
            else:
                output = "Display " + m.group("output_num")
            refresh = float(m.group("refresh"))

            refreshes[output] = refresh

    _CACHE['refreshes'] = refreshes
    return refreshes


def get_render_lag(lines):
    if "renderLag" in _CACHE:
        return _CACHE['renderLag']

    drops = search('rendering lag', lines)
    val = 0

    for drop in drops:
        v = float(drop[drop.find("(") + 1: drop.find(")")].strip('%').replace(",", "."))
        if v > val:
            val = v

    _CACHE['renderLag'] = val
    return val


def get_obs_platform(lines):
    obs_line = get_obs_version_line(lines)
    if "linux" in obs_line:
        return "linux"
    if "windows" in obs_line:
        return "windows"
    if "mac" in obs_line:
        return "mac"
    return ""


def get_wasapi_sample_rates(lines):
    if "samplerateWASAPI" in _CACHE:
        return _CACHE['samplerateWASAPI']

    sample_re = re.compile(r"""
        (?i)
        WASAPI:
        .*
        '(?P<device>.*)'
        .*
        \[(?P<sample>\d{2,12})\sHz\]
        .*
    """, re.VERBOSE)

    samples = {}
    sample_lines = search(' Hz] initialized', lines)

    for sl in sample_lines:
        m = sample_re.search(sl)

        if m is not None:
            device = str(m.group('device'))
            sample = int(m.group('sample'))

            samples[device] = sample

    _CACHE['samplerateWASAPI'] = samples
    return samples
