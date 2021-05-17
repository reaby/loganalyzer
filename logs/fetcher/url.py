from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional
import re
import requests


class Fetcher(ABC):
    @abstractmethod
    def set_next(self, handler: Fetcher) -> Fetcher:
        pass

    @abstractmethod
    def parse(self, request) -> Optional[str]:
        pass


class URLFetcher(Fetcher):
    _next_fetcher: Fetcher = None

    def set_next(self, fetcher: Fetcher) -> Fetcher:
        self._next_fetcher = fetcher
        return fetcher

    @abstractmethod
    def parse(self, url: str) -> Any:
        if self._next_fetcher:
            return self._next_fetcher.parse(url)
        return None


class Gist(URLFetcher):

    def parse(self, url: str) -> Any:
        match = re.match(r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))", url)
        if match:
            gist_id = match.groups()[-1]
            data = requests.get(f'https://api.github.com/gists/{gist_id}').json()
            files = [(v, k) for (k, v) in data['files'].items()]

            # desc = data['description']
            # if desc == "":
            #    desc = data['id']
            return files[0][0]['content']
        return super().parse(url)


class Haste(URLFetcher):

    def parse(self, url: str) -> Any:
        match = re.match(r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))", url)
        if match:
            gist_id = match.groups()[-1]
            data = requests.get(f'https://api.github.com/gists/{gist_id}').json()
            files = [(v, k) for (k, v) in data['files'].items()]
            return files[0][0]['content']
        return super().parse(url)


class Obs(URLFetcher):

    def parse(self, url: str) -> Any:
        match = re.match(r"(?i)\b((?:https?:(?:/{1,3}(www\.)?obsproject\.com)/logs/)(.{16}))", url)
        if match:
            return requests.get(f'https://obsproject.com/logs/{match.groups()[-1]}').text
        return super().parse(url)


class Pastebin(URLFetcher):

    def parse(self, url: str) -> str:
        match = re.match(r"(?i)\b((?:https?:(?:/{1,3}(www\.)?pastebin\.com/))(?:raw/)?(.{8}))", url)
        if match:
            return requests.get(f'https://pastebin.com/raw/{match.groups()[-1]}').text
        return super().parse(url)


class Discord(URLFetcher):

    def parse(self, url: str) -> str:
        match = re.match(
            r"(?i)\b((?:https?:(?:/{1,3}cdn\.discordapp\.com)/)(attachments/)([0-9]{18}/[0-9]{18}/(?:[0-9\-\_]{19}|message).txt))",
            url)
        if match:
            discord_id = match.groups()[-1]
            if discord_id == "message":
                discord_id = match.groups()[-2]

            resp = requests.get(f'https://cdn.discordapp.com/attachments/{discord_id}')
            if resp.status_code == 200:
                return resp.text
        return super().parse(url)
