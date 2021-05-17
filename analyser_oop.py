#!/usr/bin/env python3
import argparse
from logs.analyser import LogAnalyser
from logs.fetcher import Fetcher

"""
Go go go
"""
if __name__ == '__main__':
    cmd_parser = argparse.ArgumentParser()
    group = cmd_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", '-u', dest='url',
                       default=None, help="url of gist or haste with log")
    group.add_argument("--file", "-f", dest='file',
                       default=None, help="local filename with log")
    flags = cmd_parser.parse_args()
    contents = None
    fetch = Fetcher()

    if flags.url:
        contents = fetch.url(flags.url)
    if flags.file:
        contents = fetch.file(flags.file)

    messages = LogAnalyser().analyse(contents)

    # todo make factory for different output formatting options
    print(messages)