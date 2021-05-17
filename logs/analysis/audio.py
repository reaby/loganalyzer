from logs.utils.helpers import *


class Audio:

    def parse(self, lines):
        messages = []
        messages.extend([
            self.check_wasapi_samples(lines),

        ])

        return [x for x in messages if x is not None]

    def check_wasapi_samples(self, lines):
        if get_obs_platform(lines) != "windows":
            return

        samples_re = re.compile(r"""
            (?i)
            samples \sper \ssec:
            \s*
            (?P<samples>\d+)
        """, re.VERBOSE)

        obs_sample_lines = search('samples per sec: ', lines)
        obs_sample = ""
        for osl in obs_sample_lines:
            m = samples_re.search(osl)
            if m is not None:
                obs_sample = int(m.group('samples'))
        samples = get_wasapi_sample_rates(lines)

        if len(samples) == 0:
            return

        s = {}
        if obs_sample != "":
            s[round(obs_sample)] = True
        for _, hz in samples.items():
            s[round(hz)] = True

        if len(s) > 1:
            smpls = ""
            if obs_sample != "":
                smpls += "<br>OBS Sample Rate: <strong>" + str(obs_sample) + "</strong> Hz"
            for d, hz in samples.items():
                smpls += "<br>" + d + ": <strong>" + str(hz) + "</strong> Hz"
            return [
                LEVEL_WARNING,
                "Mismatched Sample Rates",
                "At least one of your audio devices has a sample rate that doesn't match the rest. "
                "This can result in audio drift over time or sound distortion. Check your audio devices in "
                "Windows settings (both Playback and Recording) and ensure the Default Format (under Advanced) "
                "is consistent. 48000 Hz is recommended." + smpls
            ]
