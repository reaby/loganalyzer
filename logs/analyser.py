from logs.utils.helpers import *
import logs.analysis as analysis


class LogAnalyser:

    def analyse(self, contents):
        if contents is None:
            print("Can't analyse file.")
            exit(1)
        lines = contents.split('\n')
        messages = []
        classic = self.check_classic(lines)

        if classic:
            messages = classic
        else:
            messages += analysis.Core().parse(lines)
            messages += analysis.Graphics().parse(lines)
            if get_obs_platform(lines) == "windows":
                messages += analysis.Windows().parse(lines)
            # if get_obs_platform(lines) == "mac":
            #    messages += analysis.Mac().parse(lines)
            messages += analysis.Audio().parse(lines)

        return messages

    def check_classic(self, lines):
        if len(search(': Open Broadcaster Software v0.', lines)) > 0:
            return [LEVEL_CRITICAL,
                    "OBS Classic",
                    "You are still using OBS Classic. This version is no longer supported. "
                    "While we cannot and will not do anything to prevent you from using it,"
                    "we cannot help with any issues that may come up."
                    "<br>It is recommended that you update to OBS Studio.<br><br>"
                    "Further information on why you should update (and how):"
                    "<a href=\"https://obsproject.com/forum/threads/how-to-easily-switch-to-obs-studio.55820/\">"
                    "OBS Classic to OBS Studio</a>."
                    ]
        return None
