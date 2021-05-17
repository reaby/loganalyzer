import html
from pkg_resources import parse_version
from logs.utils.helpers import *


class Windows:

    def parse(self, lines):
        messages = []
        messages.extend([
            self.check_windows_ver(lines),
            self.check_admin(lines),
            self.check_32bit_on_64bit(lines),

            self.check_gpu(lines),
            self.check_microsoft_software_gpu(lines),
            self.check_open_gl_on_windows(lines),

            self.check_game_dvr(lines),
            self.check_win10_hags(lines),
        ])

        return (x for x in messages if x is not None)

    def check_gpu(self, lines):
        version_string = get_obs_version(lines)
        if parse_version(version_string) < parse_version('23.2.1'):
            adapters = search('Adapter 1', lines)
            try:
                adapters.append(search('Adapter 2', lines)[0])
            except IndexError:
                pass
        else:
            adapters = search('Adapter 0', lines)
            try:
                adapters.append(search('Adapter 1', lines)[0])
            except IndexError:
                pass
        d3d_adapter = search('Loading up D3D11', lines)
        if len(d3d_adapter) > 0:
            if len(adapters) == 2 and ('Intel' in d3d_adapter[0]):
                return [
                    LEVEL_CRITICAL,
                    "Wrong GPU",
                    "Your Laptop has two GPUs. OBS is running on the weak integrated Intel GPU. "
                    "For better performance as well as game capture being available you should run OBS on "
                    "the dedicated GPU. Check the "
                    "<a href=\"https://obsproject.com/wiki/Laptop-Troubleshooting\">Laptop Troubleshooting Guide</a>."
                ]
            if len(adapters) == 2 and ('Vega' in d3d_adapter[0]):
                return [
                    LEVEL_CRITICAL,
                    "Wrong GPU",
                    "Your Laptop has two GPUs. OBS is running on the weak integrated AMD Vega GPU. "
                    "For better performance as well as game capture being available you should run OBS on "
                    "the dedicated GPU. Check the "
                    "<a href=\"https://obsproject.com/wiki/Laptop-Troubleshooting\">Laptop Troubleshooting Guide</a>."
                ]
            elif len(adapters) == 1 and ('Intel' in adapters[0]):
                return [
                    LEVEL_WARNING,
                    "Integrated GPU",
                    "OBS is running on an Intel iGPU. This hardware is generally not powerful enough to be used for "
                    "both gaming and running obs. Situations where only sources from e.g. cameras and capture cards "
                    "are used might work."
                ]

    def check_microsoft_software_gpu(self, lines):
        if len(search('Microsoft Basic Render Driver', lines)) > 0:
            return [
                LEVEL_CRITICAL,
                "No GPU driver available",
                "Your GPU is using the Microsoft Basic Render Driver, which is a pure software render. "
                "This will cause very high CPU load when used with OBS. "
                "Make sure to install proper drivers for your GPU. "
                "To use OBS in a virtual machine, you need to enable GPU passthrough."
            ]

    def check_open_gl_on_windows(self, lines):
        opengl = search('Warning: The OpenGL renderer is currently in use.', lines)
        if len(opengl) > 0:
            return [
                LEVEL_CRITICAL,
                "OpenGL Renderer",
                "The OpenGL renderer should not be used on Windows, as it is not well optimized and can have "
                "visual artifacting. Switch back to the Direct3D renderer in Settings > Advanced."
            ]

    def check_game_dvr(self, lines):
        if search('Game DVR Background Recording: On', lines):
            return [LEVEL_WARNING,
                    "Windows 10 Game DVR",
                    "To ensure that OBS Studio has the hardware resources it needs for realtime streaming and "
                    "recording, we recommend disabling the \"Game DVR Background Recording\" feature via "
                    "<a href=\"https://obsproject.com/wiki/How-to-disable-Windows-10-Gaming-Features#game-dvrcaptures\">"
                    "these instructions</a>."
                    ]

    def check_game_mode(self, lines):
        verinfo = get_windows_version(lines)

        if not verinfo or verinfo["version"] != "10.0":
            return

        if verinfo["version"] == "10.0" and "release" not in verinfo:
            return

        if search("Game Mode: On", lines) and verinfo["release"] < 1809:
            return [
                LEVEL_WARNING,
                "Windows 10 Game Mode",
                "In some versions of Windows 10 (prior to version 1809), the \"Game Mode\" feature interferes with OBS "
                "Studio's normal functionality by starving it of CPU and GPU resources. We recommend disabling it via "
                "<a href=\"https://obsproject.com/wiki/How-to-disable-Windows-10-Gaming-Features#game-mode\">"
                "these instructions</a>."
            ]
        if search("Game Mode: Off", lines):
            return [
                LEVEL_INFO,
                "Windows 10 Game Mode",
                "In Windows 10 versions 1809 and newer, we recommend that \"Game Mode\" be enabled for maximum gaming "
                "performance. Game Mode can be enabled via the Windows 10 \"Settings\" app, under "
                "Gaming > <a href=\"ms-settings:gaming-gamemode\">Game Mode</a>."
            ]

    def check_win10_hags(self, lines):
        if search('Hardware GPU Scheduler: On', lines):
            return [
                LEVEL_CRITICAL,
                "Hardware-accelerated GPU Scheduler",
                "The new Windows 10 Hardware-accelerated GPU scheduling (\"HAGS\") added with version 2004 is "
                "currently known to cause performance and capture issues with OBS, games and overlay tools. "
                "It's a new and experimental feature and we recommend disabling it via "
                "<a href=\"ms-settings:display-advancedgraphics\">this screen</a> or "
                "<a href=\"https://obsproject.com/wiki/How-to-disable-Windows-10-Hardware-GPU-Scheduler\">"
                "these instructions</a>."
            ]

    def check_windows_ver(self, lines):
        verinfo = get_windows_version(lines)
        if not verinfo:
            return None

        # This is such a hack, but it's unclear how to do this better
        if verinfo["version"] == "10.0" and verinfo["release"] == 0:
            return [
                LEVEL_WARNING,
                "Windows 10 Version Unknown",
                "You are running an unknown Windows 10 release (build %d), "
                "which means you are probably using an Insider build. Some checks that are applicable only to specific "
                "Windows versions will not be performed. Also, because Insider builds are test versions, you may have "
                "problems that would not happen with release versions of Windows." % (verinfo["build"])
            ]

        if "EoS" in verinfo and datetime.date.today() > verinfo["EoS"]:
            return [
                LEVEL_WARNING,
                "%s (EOL)" % (html.escape(verinfo["name"])),
                "You are running %s, which has not been supported by Microsoft since <strong>%s</strong>. "
                "We recommend updating to the latest Windows release to ensure continued security, "
                "functionality, and compatibility." \
                % (html.escape(verinfo["name"]), verinfo["EoS"].strftime("%B %Y"))
            ]

        # special case for OBS 24.0.3 and earlier, which report Windows 10/1909
        # as being Windows 10/1903
        obs_version = get_obs_version(lines)
        if parse_version(obs_version) <= parse_version("24.0.3"):
            if verinfo["version"] == "10.0" and verinfo["release"] == 1903:
                return [
                    LEVEL_INFO,
                    "Windows 10 1903/1909",
                    "Due to a bug in OBS versions 24.0.3 and earlier, the exact release of Windows 10 you are using "
                    "cannot be determined. You are using either release 1903, or release 1909. Fortunately, there were "
                    "no major changes in behavior between Windows 10 release 1903 and Windows 10 release 1909, "
                    "and instructions given here for release 1903 can also be used for release 1909, and vice versa."
                ]

        # our windows version isn't out of support, so just say what version the user has and when
        # it actually does go out of support
        wv = "%s (OK)" % (html.escape(verinfo["name"]))
        if "EoS" in verinfo:
            msg = "You are running %s, which will be supported by Microsoft until <strong>%s</strong>." % (
                html.escape(verinfo["name"]), verinfo["EoS"].strftime("%B %Y"))
        else:
            msg = "You are running %s, for which Microsoft has not yet announced an end of life date." % (
                html.escape(verinfo["name"]))

        return [LEVEL_INFO, wv, msg]

    def check_admin(self, lines):
        admin_lines = search('Running as administrator', lines)
        if (len(admin_lines) > 0) and (admin_lines[0].split()[-1] == 'false'):
            render_lag = get_render_lag(lines)

            if render_lag >= 3:
                return [
                    LEVEL_WARNING,
                    "Not Admin",
                    "OBS is not running as Administrator. "
                    "Because of this, OBS will not be able to Game Capture certain games, and it will not be able to "
                    "request a higher GPU priority for itself -- which is the likely cause of the render lag you are "
                    "currently experincing. Run OBS as Administrator to help alleviate this problem."
                ]
            return [
                LEVEL_INFO,
                "Not Admin",
                "OBS is not running as Administrator. This can lead to OBS not being able to "
                "Game Capture certain games. If you are not running into issues, you can ignore this."
            ]

    def check_32bit_on_64bit(self, lines):
        win_version = search('Windows Version', lines)
        obs_version = get_obs_version_line(lines)
        if (len(win_version) > 0 and '64-bit' in win_version[0] and '64-bit' not
                in obs_version and '64-bit' not in obs_version):
            # thx to secretply for the bugfix
            return [
                LEVEL_WARNING,
                "32-bit OBS on 64-bit Windows",
                "You are running the 32 bit version of OBS on a 64 bit system. This will reduce performance and "
                "greatly increase the risk of crashes due to memory limitations. You should only use the 32 bit "
                "version if you have a capture device that lacks 64 bit drivers. "
                "Please run OBS using the 64-bit shortcut."
            ]
