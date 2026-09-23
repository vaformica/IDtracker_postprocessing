#!/usr/bin/env python3
"""Serve portable review folders locally with MP4 byte-range seeking.

Use: python serve_review.py FOLDER --port 8769
Open http://127.0.0.1:8769/interaction_review.html. Bound to localhost only.
"""
from __future__ import annotations

import argparse
import http.server
import os
import re
from functools import partial


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        self._range = None
        path = self.translate_path(self.path)
        if not os.path.isfile(path) or not self.headers.get('Range'):
            return super().send_head()
        size = os.path.getsize(path)
        match = re.fullmatch(r'bytes=(\d+)-(\d*)', self.headers['Range'].strip())
        if not match:
            self.send_error(416, 'Unsupported byte range')
            return None
        start = int(match.group(1))
        end = min(size-1, int(match.group(2))) if match.group(2) else size-1
        if start >= size or end < start:
            self.send_error(416, 'Range outside file')
            return None
        stream = open(path, 'rb')
        stream.seek(start)
        self._range = end-start+1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(self._range))
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        if self._range is None:
            return super().copyfile(source, outputfile)
        remaining = self._range
        while remaining:
            chunk = source.read(min(1024*1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('--port', type=int, default=8769)
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port),
        partial(RangeHandler, directory=args.folder))
    print(f'Open http://127.0.0.1:{args.port}/interaction_review.html', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
