from .url import Gist, Haste, Discord, Obs, Pastebin


class Fetcher:

    @staticmethod
    def url(location):
        obs = Obs()
        obs.set_next(Discord()).set_next(Pastebin()).set_next(Haste()).set_next(Pastebin()).set_next(Gist())
        return obs.parse(location)

    @staticmethod
    def file(location):
        try:
            with open(location, "r") as f:
                return f.read()
        except OSError:
            return None
