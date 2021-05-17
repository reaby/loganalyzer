import html
import re
from typing import Set
from pkg_resources import parse_version
from logs.utils.helpers import *

regex_ver = re.compile(r"""
      (?i)
      (?P<ver_major>[0-9]+)
      \.
      (?P<ver_minor>[0-9]+)
      \.
      (?P<ver_micro>[0-9]+)
      (
          -
          (?P<special> (?P<special_type> rc|beta) \d*)
      )?
      $
      """, re.VERBOSE)


class Core:
    def parse(self, lines):
        messages = []
        messages.extend([
            self.check_obs_version(lines),
            self.check_cpu(lines),
            self.check_dual_instances(lines)
        ])

        return (x for x in messages if x is not None)

    def check_dual_instances(self, lines):
        if len(search('Warning: OBS is already running!', lines)) > 0:
            return [
                LEVEL_CRITICAL,
                "Two Instances",
                "Two instances of OBS are running. If you are not intentionally running two instances, "
                "they will likely interfere with each other and consume excessive resources. Stop one of them. "
                "Check Task Manager for stray OBS processes if you can't find the other one."
            ]

    def check_autoconfig(self, lines):
        if len(search('Auto-config wizard', lines)) > 0:
            return [
                LEVEL_CRITICAL,
                "Auto-Config Wizard",
                "The log contains an Auto-Config Wizard run. Results of this analysis are therefore inaccurate. "
                "Please post a link to a clean log file." + clean_log
            ]

    def check_obs_version(self, lines):
        version = get_obs_version(lines)

        if parse_version(version) == parse_version('21.1.0'):
            return [
                LEVEL_WARNING,
                "Broken Auto-Update",
                "You are not running the latest version of OBS Studio."
                "Automatic updates in version 21.1.0 are broken due to a bug. "
                "<br>Please update by downloading the latest installer from the "
                "<a href=\"https://obsproject.com/download\">downloads page</a> and running it."
            ]

        m = regex_ver.search(version.replace('-modified', ''))
        if m is None:
            if re.match(r"(?:\d)+\.(?:\d)+\.(?:\d)+\+(?:[\d\w\-\.~\+])+", version):
                return [
                    LEVEL_INFO,
                    "Unofficial OBS Build (%s)" % (html.escape(version)),
                    "Your OBS version identifies itself as '%s', which is not an official build.<br>"
                    "If you are on Linux, ensure you're using the PPA."
                    "If you cannot switch to the PPA, contact the maintainer of the package for any support issues."
                    % (html.escape(version))
                ]
            if re.match(r"(?:\d)+\.(?:\d)+\.(?:\d\w)+(?:-caffeine)", version):
                return [
                    LEVEL_INFO,
                    "Third party OBS Version (%s)" % (html.escape(version)),
                    "Your OBS version identifies itself as '%s', which is made by a third party."
                    "Contact them for any support issues."
                    % (html.escape(version))
                ]
            if re.match(r"(?:\d)+\.(?:\d)+\.(?:\d)+-(?:[\d-])*([a-z0-9]+)(?:-modified){0,1}", version):
                return [
                    LEVEL_INFO,
                    "Custom OBS Build (%s)" % (html.escape(version)),
                    "Your OBS version identifies itself as '%s', which is not a released OBS version."
                    % (html.escape(version))
                ]
            return [
                LEVEL_INFO,
                "Unparseable OBS Version (%s)" % (html.escape(version)),
                "Your OBS version identifies itself as '%s', which cannot be parsed as a valid OBS version number."""
                % (html.escape(version))
            ]

        # Do we want these to check the version number and tell the user that a
        # release version is actually available, if one is actually available?
        # We can consider adding something like that later.
        if m.group("special") is not None:
            if m.group("special_type") == "beta":
                return [
                    LEVEL_INFO,
                    "Beta OBS Version (%s)" % (html.escape(version)),
                    "You are running a beta version of OBS. "
                    "There is nothing wrong with this, but you may experience problems that you may not experience "
                    "with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as "
                    "soon as one is available."
                ]

            if m.group("special_type") == "rc":
                return [
                    LEVEL_INFO,
                    "Release Candidate OBS Version (%s)" % (html.escape(version)),
                    "You are running a release candidate version of OBS. "
                    "There is nothing wrong with this, but you may experience problems that you may not experience "
                    "with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as "
                    "soon as one is available."
                ]

        if parse_version(version.replace('-modified', '')) < parse_version(CURRENT_VERSION):
            return [
                LEVEL_WARNING,
                "Old Version",
                "You are not running the latest version of OBS Studio. "
                "Please update by downloading the latest installer from the "
                "<a href=\"https://obsproject.com/download\">downloads page</a> and running it."
            ]

    def check_cpu(self, lines):
        cpu = search('CPU Name', lines)
        if len(cpu) > 0:
            if ('APU' in cpu[0]) or ('Pentium' in cpu[0]) or ('Celeron' in cpu[0]):
                return [LEVEL_CRITICAL, "Insufficient Hardware",
                        "Your system is below minimum specs for OBS to run and may be too underpowered to livestream."
                        "There are no recommended settings we can suggest, "
                        "but try the Auto-Config Wizard in the Tools menu. "
                        "You may need to upgrade or replace your computer for a better experience."]
            elif 'i3' in cpu[0]:
                return [LEVEL_INFO, "Insufficient Hardware",
                        "Your system is below minimum specs for OBS to run and is too underpowered "
                        "to livestream using software encoding. "
                        "Livestreams and recordings will only run smoothly if you are using the hardware "
                        "QuickSync encoder (via Settings -> Output)."
                        ]
