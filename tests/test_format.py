from os.path import join as pathjoin, dirname

from aiohttp.test_utils import unittest_run_loop
from aiohttp import web

from tests.base import PreviewTestCase

ROOT = dirname(dirname(__file__))
FIXTURE_SAMPLE_PDF = pathjoin(ROOT, 'fixtures/sample.pdf')
FIXTURE_SAMPLE_DOC = pathjoin(ROOT, 'fixtures/sample.doc')
FIXTURE_QUICKTIME_MOV = pathjoin(ROOT, 'fixtures/Quicktime_Video.mov')


class PreviewFormatTestCase(PreviewTestCase):
    @unittest_run_loop
    async def test_pdf(self):
        "Request a preview as PDF and ensure PDF is returned."
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'pdf', 'path': FIXTURE_SAMPLE_PDF})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'application/pdf')

    @unittest_run_loop
    async def test_image(self):
        "Request a preview as an image and ensure GIF is returned."
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'image', 'path': FIXTURE_QUICKTIME_MOV})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'image/gif')

    @unittest_run_loop
    async def test_invalid(self):
        'Request an invalid format and ensure a 400 is returned.'
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'foobar', 'path': FIXTURE_SAMPLE_PDF})
        self.assertEqual(r.status, 400)