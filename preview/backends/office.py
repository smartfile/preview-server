import logging
import subprocess

from tempfile import NamedTemporaryFile
from concurrent.futures import ThreadPoolExecutor
from runpy import run_path

from preview.backends.base import BaseBackend
from preview.backends.pdf import PdfBackend
from preview.utils import log_duration
from preview.config import (
    SOFFICE_ADDR, SOFFICE_PORT, SOFFICE_TIMEOUT, SOFFICE_RETRY, MAX_OFFICE_WORKERS
)
from preview.models import PathModel
from preview.errors import InvalidPageError


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
TEXT_FORMATS = [
    'log',
]
FMTS = run_path('/usr/local/bin/unoconv')['fmts']


def convert(obj, retry=SOFFICE_RETRY, pages=(1, 1)):
    cmd = [
        'unoconv', '--server=%s' % SOFFICE_ADDR, '--port=%s' % SOFFICE_PORT,
        '--stdout',
    ]

    if pages != (0, 0):
        cmd.extend(['-e', 'PageRange=%i-%i' % pages])

    # Give a hint at which input filter to use. The file name passed to unoconv
    # may not have an extension.
    format = FMTS.byextension('.%s' % obj.src.extension)
    if format:
        cmd.extend(['-I', format[0].name])

    file_data = None
    if obj.src.is_shared:
        cmd.append(obj.src.path)

    else:
        cmd.append('--stdin')
        with open(obj.src.path, 'rb') as f:
            file_data = f.read()

    LOGGER.debug('unoconv cmd: %s' % cmd)

    while True:
        try:
            p = subprocess.run(cmd, input=file_data, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=SOFFICE_TIMEOUT,
                               check=True)

            return p.stdout

        except subprocess.CalledProcessError as e:
            if pages not in ((0, 0), (1, 1)):
                LOGGER.exception(
                    'unoconv failed, throwing page error: %i; %s\n%s',
                    e.returncode, e.stdout, e.stderr)
                # Specific page(s) beyond the first were requested.
                raise InvalidPageError(pages)

            if not retry:
                raise
            LOGGER.debug(
                'unoconv failed, retrying: %i; %s\n%s',
                e.returncode, e.stdout, e.stderr)

        except Exception as e:
            if not retry:
                raise
            LOGGER.debug('unoconv failed, retrying: %s', e, exc_info=True)

        finally:
            retry -= 1


class OfficeBackend(BaseBackend):
    name = 'office'
    extensions = [
        # https://en.wikipedia.org/wiki/LibreOffice#Supported_file_formats
        'dot', 'docm', 'dotx', 'dotm', 'psw', 'doc', 'xls', 'ppt', 'wpd',
        'wps', 'csv', 'sdw', 'sgl', 'vor', 'docx', 'xlsx', 'pptx', 'xlsm',
        'xltx', 'xltm', 'xlt', 'xlw', 'dif', 'rtf', 'pxl', 'pps', 'ppsx',
        'odt', 'ods', 'odp', 'log', 'txt', 'abw', 'zabw', 'cwk', 'hwp',
        'jtd', 'jtt', 'psw', 'wri', '602', 'wpd', 'wps', 'pmd', 'pm3', 'pm4',
        'pm5', 'pm6', 'p65', 'pub', 'qxp', 'html', 'htm', 'fb2', 'rfl',
        # Though listed, epub does not seem to be supported...
        # 'epub',
        # Calibre could possibly be used in a separate backend for conversion
        # from epub to pdf.
    ]
    executor = ThreadPoolExecutor(max_workers=MAX_OFFICE_WORKERS) \
        if MAX_OFFICE_WORKERS else None

    @log_duration
    def _preview_pdf(self, obj):
        with NamedTemporaryFile(delete=False, suffix='.pdf') as t:
            t.write(convert(obj, pages=obj.args.get('pages')))
            obj.dst = PathModel(t.name)

    @log_duration
    def _preview_image(self, obj):
        with NamedTemporaryFile(delete=False, suffix='.pdf') as t:
            t.write(convert(obj, pages=obj.args.get('pages')))
            obj.src = PathModel(t.name)

        # We need to override the pages parameter since the pdf we just
        # generated contains only the pages we want, we don't need to further
        # limit pages.
        PdfBackend()._preview_image(obj, pages=(0, 0))
