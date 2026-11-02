# -*- coding: utf-8 -*-
"""
Module for download-related classes and functions.

We currently support an internal downloader written in Python with just the
essential functionality and four "industrial-strength" external downloaders,
namely, aria2c, axel, curl, and wget.
"""

from __future__ import print_function

import glob
import hashlib
import logging
import math
import os
import subprocess
import sys
import time
from urllib.parse import urlsplit

import requests

from . import download_progress

# Seconds to wait for a connection / for more data before giving up on a file.
DOWNLOAD_TIMEOUT = (15, 60)

# An unfinished download lives here until complete, so a file under its real
# name is always a finished one, and a later run can continue from this file.
PARTIAL_SUFFIX = '.part'

#
# Below are file downloaders, they are wrappers for external downloaders.
#

class Downloader(object):
    """
    Base downloader class.

    Every subclass should implement the _start_download method.

    Usage::

      >>> import downloaders
      >>> d = downloaders.SubclassFromDownloader()
      >>> d.download('http://example.com', 'save/to/this/file')
    """

    def _start_download(self, url, filename, resume):
        """
        Actual method to download the given url to the given file.
        This method should be implemented by the subclass.
        """
        raise NotImplementedError("Subclasses should implement this")

    def download(self, url, filename, resume=False):
        """
        Download the given url to the given file. When the download
        is aborted by the user, the partially downloaded file is also removed.
        """

        try:
            self._start_download(url, filename, resume)
        except BaseException:
            # A partial file would later be mistaken for a finished one, so
            # keep it only if resume is True.
            if not resume:
                logging.info('Download interrupted -- Removing partial file: %s',
                             filename)
                try:
                    os.remove(filename)
                except OSError:
                    pass
            raise


class ExternalDownloader(Downloader):
    """
    Downloads files with an external downloader.

    We could possibly use python to stream files to disk,
    but this is slow compared to these external downloaders.

    :param session: Requests session.
    :param bin: External downloader binary.
    """

    # External downloader binary
    bin = None

    def __init__(self, session, bin=None, downloader_arguments=None):
        self.session = session
        self.bin = bin or self.__class__.bin
        self.downloader_arguments = downloader_arguments or []

        if not self.bin:
            raise RuntimeError("No bin specified")

        self._check_bin()

    def _prepare_cookies(self, command, url):
        """
        Extract cookies from the requests session and add them to the command
        """

        req = requests.models.Request()
        req.method = 'GET'
        req.url = url

        cookie_values = requests.cookies.get_cookie_header(
            self.session.cookies, req)

        if cookie_values:
            self._add_cookies(command, cookie_values)

    def _enable_resume(self, command):
        """
        Enable resume feature
        """

        raise RuntimeError("Subclass should implement this")

    def _add_cookies(self, command, cookie_values):
        """
        Add the given cookie values to the command
        """

        raise RuntimeError("Subclasses should implement this")

    def _create_command(self, url, filename):
        """
        Create command to execute in a subprocess.
        """
        raise NotImplementedError("Subclasses should implement this")

    def _check_bin(self):
        """
        Make sure the downloader is installed
        """
        try:
            ret = subprocess.run([self.bin, "--version"])
        except FileNotFoundError:
            raise RuntimeError(f"Downloader '{self.bin}' not found")

        if(ret.returncode != 0):
            raise RuntimeError(f"Downloader '{self.bin}' returned a non-zero exit status")

    def _start_download(self, url, filename, resume):
        command = self._create_command(url, filename)
        command.extend(self.downloader_arguments)
        self._prepare_cookies(command, url)
        if resume:
            self._enable_resume(command)

        logging.debug('Executing %s: %s', self.bin, command)
        try:
            subprocess.call(command)
        except OSError as e:
            msg = "{0}. Are you sure that '{1}' is the right bin?".format(
                e, self.bin)
            raise OSError(msg)


class WgetDownloader(ExternalDownloader):
    """
    Uses wget, which is robust and gives nice visual feedback.
    """

    bin = 'wget'

    def _enable_resume(self, command):
        command.append('-c')

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-O', filename, '--no-cookies',
                '--no-check-certificate']


class CurlDownloader(ExternalDownloader):
    """
    Uses curl, which is robust and gives nice visual feedback.
    """

    bin = 'curl'

    def _enable_resume(self, command):
        command.extend(['-C', '-'])

    def _add_cookies(self, command, cookie_values):
        command.extend(['--cookie', cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-k', '-#', '-L', '-o', filename]


class Aria2Downloader(ExternalDownloader):
    """
    Uses aria2. Unfortunately, it does not give a nice visual feedback, but
    gets the job done much faster than the alternatives.
    """

    bin = 'aria2c'

    def _enable_resume(self, command):
        command.append('-c')

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-o', filename,
                '--check-certificate=false', '--log-level=notice',
                '--max-connection-per-server=4', '--min-split-size=1M']


class AxelDownloader(ExternalDownloader):
    """
    Uses axel, which is robust and it both gives nice
    visual feedback and get the job done fast.
    """

    bin = 'axel'

    def _enable_resume(self, command):
        logging.warn('Resume download not implemented for this '
                     'downloader!')

    def _add_cookies(self, command, cookie_values):
        command.extend(['-H', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, '-o', filename, '-n', '4', '-a', url]


def format_bytes(bytes):
    """
    Get human readable version of given bytes.
    Ripped from https://github.com/rg3/youtube-dl
    """
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '{0:.2f}{1}'.format(converted, suffix)


class DownloadProgress(object):
    """
    Report download progress.
    Inspired by https://github.com/rg3/youtube-dl
    """

    # Minimum seconds between reports, so that a fast connection does not
    # flood the console and the GUI.
    REPORT_INTERVAL = 0.1

    def __init__(self, total, offset=0):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._offset = offset  # bytes already on disk when resuming
        self._current = 0
        self._start = 0
        self._now = 0
        self._last_report = 0

        self._finished = False

    def start(self):
        self._now = time.time()
        self._start = self._now

    def stop(self):
        self._now = time.time()
        self._finished = True
        self._total = self._current
        self.report_progress()

    def read(self, bytes):
        self._now = time.time()
        self._current += bytes
        self.report_progress()

    def report(self, bytes):
        self._now = time.time()
        self._current = bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        if self._total == 0:
            return '100% done'
        percentage = int(float(self._current) / float(self._total) * 100.0)
        done = int(percentage / 2)
        return '[{0: <50}] {1}%'.format(done * '#', percentage)

    def calc_speed(self):
        dif = self._now - self._start
        if self._current == 0 or dif < 0.001:  # One millisecond
            return '---b/s'
        return '{0}/s'.format(format_bytes(float(self._current) / dif))

    def report_progress(self):
        """Report download progress."""
        if (not self._finished
                and self._now - self._last_report < self.REPORT_INTERVAL):
            return
        self._last_report = self._now

        download_progress.emit(
            'bytes',
            received=self._current,
            current=self._offset + self._current,
            total=None if self._total is None else self._offset + self._total,
        )

        # There is no console under pythonw.exe or in a windowed build.
        if sys.stdout is None:
            return

        percent = self.calc_percent()
        total = format_bytes(self._total)

        speed = self.calc_speed()
        total_speed_report = '{0} at {1}'.format(total, speed)

        report = '\r{0: <56} {1: >30}'.format(percent, total_speed_report)

        if self._finished:
            print(report)
        else:
            print(report, end="")
        sys.stdout.flush()


def partial_filename_for(filename, url):
    """
    Name of the unfinished download of url into filename.

    It carries a tag of the source, so that bytes of a different source, such
    as another video resolution, are never continued into this file. The query
    string is left out: it holds a signature that changes on every run.
    """
    source_tag = hashlib.sha1(urlsplit(url).path.encode('utf-8')).hexdigest()[:8]
    return '{0}.{1}{2}'.format(filename, source_tag, PARTIAL_SUFFIX)


def remove_other_partial_files(filename, keep):
    """Delete unfinished downloads of filename that came from another source."""
    stale = glob.glob(glob.escape(filename) + '.*' + PARTIAL_SUFFIX)
    stale.append(filename + PARTIAL_SUFFIX)  # untagged, from earlier versions
    for path in stale:
        if path != keep and os.path.exists(path):
            logging.info('Removing unfinished download from another source: %s', path)
            try:
                os.remove(path)
            except OSError:
                pass


class NativeDownloader(Downloader):
    """
    'Native' python downloader -- slower than the external downloaders.

    :param session: Requests session.
    """

    def __init__(self, session):
        self.session = session

    def _start_download(self, url, filename, resume=False):
        partial_filename = partial_filename_for(filename, url)
        remove_other_partial_files(filename, partial_filename)
        resume = (os.path.exists(partial_filename)
                  and os.path.getsize(partial_filename) > 0)

        headers = {}
        filesize = None
        if resume:
            filesize = os.path.getsize(partial_filename)
            headers['Range'] = 'bytes={}-'.format(filesize)
            logging.info('Resume downloading %s -> %s', url, filename)
        else:
            logging.info('Downloading %s -> %s', url, filename)

        max_attempts = 3
        attempts_count = 0
        error_msg = ''
        while attempts_count < max_attempts:
            r = self.session.get(url, stream=True, headers=headers,
                                 timeout=DOWNLOAD_TIMEOUT)

            if r.status_code != 200:
                # because in resume state we are downloading only a
                # portion of requested file, server may return
                # following HTTP codes:
                # 206: Partial Content
                # 416: Requested Range Not Satisfiable
                # which are OK for us.
                if resume and r.status_code == 206:
                    pass
                elif resume and r.status_code == 416:
                    logging.info('%s already downloaded', filename)
                    r.close()
                    os.replace(partial_filename, filename)
                    return True
                else:
                    print('%s %s %s' % (r.status_code, url, filesize))
                    logging.warn('Probably the file is missing from the AWS '
                                 'repository...  waiting.')

                    if r.reason:
                        error_msg = r.reason + ' ' + str(r.status_code)
                    else:
                        error_msg = 'HTTP Error ' + str(r.status_code)

                    wait_interval = 2 ** (attempts_count + 1)
                    msg = 'Error downloading, will retry in {0} seconds ...'
                    print(msg.format(wait_interval))
                    download_progress.wait(wait_interval)
                    attempts_count += 1
                    continue

            if resume and r.status_code == 200:
                # if the server returns HTTP code 200 while we are in
                # resume mode, it means that the server does not support
                # partial downloads.
                resume = False

            content_length = r.headers.get('content-length')
            # A small chunk keeps both Stop and the progress bar responsive.
            chunk_sz = 64 * 1024
            progress = DownloadProgress(content_length,
                                        offset=filesize if resume else 0)
            progress.start()
            try:
                # The file must be closed before a stopped download can
                # remove it: Windows refuses to delete an open file.
                with open(partial_filename, 'ab' if resume else 'wb') as f:
                    while True:
                        download_progress.check_cancelled()
                        data = r.raw.read(chunk_sz, decode_content=True)
                        if not data:
                            progress.stop()
                            break
                        f.write(data)
                        progress.report(r.raw.tell())
                if content_length and r.raw.tell() < int(content_length):
                    raise requests.exceptions.ConnectionError(
                        'Connection closed early: ' + filename)
            finally:
                r.close()
            os.replace(partial_filename, filename)
            return True

        if attempts_count == max_attempts:
            logging.warn('Skipping, can\'t download file ...')
            logging.error(error_msg)
            return False


def get_downloader(session, class_name, args):
    """
    Decides which downloader to use.
    """

    external = {
        'wget': WgetDownloader,
        'curl': CurlDownloader,
        'aria2': Aria2Downloader,
        'axel': AxelDownloader,
    }

    for bin, class_ in external.items():
        if getattr(args, bin):
            return class_(session, bin=getattr(args, bin),
                          downloader_arguments=args.downloader_arguments)

    return NativeDownloader(session)
