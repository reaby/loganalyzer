from logs.utils.helpers import *


class Graphics:

    def parse(self, lines):
        messages = []
        messages.extend([
            self.check_video_init(lines),
            self.check_video_settings(lines),
            self.check_refreshes(lines),
            self.check_render_lag(lines),
            self.check_amd_drivers(lines),
            self.check_nvidia_drivers(lines),
            self.check_geforce_940(lines)
        ])

        return [x for x in messages if x is not None]

    @staticmethod
    def check_refreshes(lines):
        if get_obs_platform(lines) != "windows":
            return None

        refreshes = get_monitor_refreshes(lines)
        verinfo = get_windows_version(lines)

        # Our log doesn't have any refresh rates, so bail
        if len(refreshes) == 0:
            return

        # Couldn't figure out windows version
        if not verinfo:
            return

        # We don't care about refresh rates on Vista
        if verinfo["version"] == "6.1":
            return

        # If we know nothing about the windows version (Insider build?),
        # assume mixed refresh is fine
        if verinfo["version"] == "10.0" and "release" not in verinfo:
            return

        # FINALLY fixed in WIn10/2004
        if verinfo["version"] and verinfo["release"] >= 2004:
            return

        # We're on a version that has the mixed-refresh-rate problem, so lets
        # build a dict of the refresh rates we have, and see if it's bigger
        # than a single element. We're going to round each entry as we add
        # it, so that (e.g.) 59.94Hz and 60Hz are considered the same, since
        # that doesn't really cause a problem.
        r = {}
        for _, hz in refreshes.items():
            r[round(hz)] = True

        if len(r) > 1:
            rfrshs = "<br>"
            for output, hz in refreshes.items():
                rfrshs += "<br>" + output + ": <strong>" + str(int(hz)) + "</strong>Hz"
            return [
                LEVEL_WARNING,
                "Mismatched Refresh Rates",
                "The version of Windows you are running has a limitation which causes performance issues "
                "in hardware accelerated applications (such as games) if multiple monitors with different "
                "refresh rates are present. Your system's monitors have " + str(len(r)) +
                " different refresh rates, so you are affected by this limitation. "
                "<br><br>To fix this issue, we recommend updating to the Windows 10 May 2020 Update. Follow "
                "<a href=\"https://blogs.windows.com/windowsexperience/2020/05/27/how-to-get-the-windows-10-may-2020-update/\">"
                "these instructions</a> if you're not sure how to update." + rfrshs
            ]
        return None

    @staticmethod
    def check_video_init(lines):
        if len(search('Failed to initialize video', lines)) > 0:
            return [
                LEVEL_CRITICAL,
                "Initialize Failed",
                "Failed to initialize video. Your GPU may not be supported, or your graphics drivers "
                "may need to be updated."
            ]

    @staticmethod
    def check_render_lag(lines):
        val = get_render_lag(lines)
        if val != 0:
            severity = LEVEL_INFO
            if val >= 10:
                severity = LEVEL_CRITICAL
            elif 10 > val >= 3:
                severity = LEVEL_WARNING

            return [
                severity,
                f"{val}% Rendering Lag",
                "Your GPU is maxed out and OBS can't render scenes fast enough. "
                "Running a game without vertical sync or a frame rate limiter will frequently cause performance "
                "issues with OBS because your GPU will be maxed out. OBS requires a little GPU to render your scene. "
                "<br><br>Enable Vsync or set a reasonable frame rate limit that your GPU can handle without hitting "
                "100% usage. <br><br>If that's not enough you may also need to turn down some of the video quality "
                "options in the game. If you are experiencing issues in general while using OBS, your GPU may be "
                "overloaded for the settings you are trying to use.<br><br>Please check our guide for ideas why this "
                "may be happening, and steps you can take to correct it: "
                "<a href=\"https://obsproject.com/wiki/GPU-overload-issues\">GPU Overload Issues</a>."
            ]

    @staticmethod
    def check_amd_drivers(lines):
        if len(search('The AMF Runtime is very old and unsupported', lines)) > 0:
            return [
                LEVEL_WARNING,
                "AMD Drivers",
                "The AMF Runtime is very old and unsupported."
                "The AMF Encoder will no work properly or not show up at all. "
                "Consider updating your drivers by downloading the newest installer from "
                "<a href=\"https://support.amd.com/en-us/download\">AMD's website</a>."
            ]

    @staticmethod
    def check_nvidia_drivers(lines):
        term = '[jim-nvenc] Current driver version does not support this NVENC version, please upgrade your driver'
        if len(search(term, lines)) > 0:
            return [
                LEVEL_WARNING,
                "Old NVIDIA Drivers",
                "The installed NVIDIA driver does not support NVENC features needed for optimized encoders. "
                "Consider updating your drivers by downloading the newest installer from "
                "<a href=\"https://www.nvidia.de/Download/index.aspx\">NVIDIA's website</a>. "
            ]

    @staticmethod
    def check_video_settings(lines):
        video_settings = []
        res = []
        for i, s in enumerate(lines):
            if "video settings reset:" in s:
                video_settings.append(i)
        if len(video_settings) > 0:
            basex, basey = lines[video_settings[-1] + 1].split()[-1].split('x')
            outx, outy = lines[video_settings[-1] + 2].split()[-1].split('x')
            fps_num, fps_den = lines[video_settings[-1] + 4].split()[-1].split('/')
            fmt = lines[video_settings[-1] + 5].split()[-1]
            yuv = lines[video_settings[-1] + 6].split()[-1]
            base_aspect = float(basex) / float(basey)
            out_aspect = float(outx) / float(outy)
            fps = float(fps_num) / float(fps_den)

            if (not ((1.77 < base_aspect) and (base_aspect < 1.7787))) \
                    or \
                    (not ((1.77 < out_aspect) and (out_aspect < 1.7787))):
                res.append(
                    [LEVEL_WARNING,
                     "Non-Standard Aspect Ratio",
                     "Almost all modern streaming services and video platforms expect video in 16:9 aspect ratio. "
                     "OBS is currently configured to record in an aspect ration that differs from that. "
                     "You (or your viewers) will see black bars during playback."
                     "Go to Settings -> Video and change your Canvas Resolution to one that is 16:9."
                     ])
            if fmt != 'NV12':
                res.append(
                    [
                        LEVEL_CRITICAL,
                        "Wrong Color Format",
                        "Color Formats other than NV12 are primarily intended for recording, and are not recommended "
                        "when streaming. Streaming may incur increased CPU usage due to color format conversion. "
                        "You can change your Color Format in Settings -> Advanced."
                    ])
            if not ((fps == 60) or (fps == 30)):
                res.append(
                    [
                        LEVEL_WARNING,
                        "Non-Standard Framerate",
                        "Framerates other than 30fps or 60fps may lead to playback issues like stuttering or screen "
                        "tearing. Stick to either of these for better compatibility with video players. "
                        "You can change your OBS frame rate in Settings -> Video."
                    ])
            if fps >= 144:
                res.append(
                    [
                        LEVEL_WARNING,
                        "Excessively High Framerate",
                        "Recording at a tremendously high framerate will not give you higher quality recordings. "
                        " Usually quite the opposite. Most computers cannot handle encoding at high framerates. "
                        "You can change your OBS frame rate in Settings -> Video."
                    ])
            if 'Full' in yuv:
                res.append(
                    [
                        LEVEL_WARNING,
                        "Wrong YUV Color Range",
                        "Having the YUV Color range set to \"Full\" will cause playback issues in certain browsers and "
                        "on various video platforms. Shadows, highlights and color will look off. "
                        "In OBS, go to \"Settings -> Advanced\" and set \"YUV Color Range\" back to \"Partial\"."
                    ])
        if len(res) > 0:
            return res

    def check_geforce_940(self, lines):
        gpu = search('NVIDIA GeForce 940', lines)
        attempt = search('NVENC encoder', lines)
        if (len(gpu) > 0) and (len(attempt) > 0):
            return [
                LEVEL_CRITICAL,
                "NVENC Not Supported",
                "The NVENC Encoder is not supported on the NVIDIA 940 and 940MX. "
                "Recording fails to start because of this. Please select \"Software (x264)\" or "
                "\"Hardware (QSV)\" as encoder instead in Settings > Output."
            ]