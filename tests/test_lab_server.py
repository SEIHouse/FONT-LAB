"""The local Lab server only starts jobs for its own page; jobs only accept Lab-shaped cuts."""
from functools import partial
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from display import lab_jobs, lab_server

ROOT = Path(__file__).resolve().parents[1]


class LabServerTests(unittest.TestCase):
    def setUp(self):
        self.server = lab_server.ThreadingHTTPServer(('127.0.0.1', 0), partial(lab_server.LabHandler, directory=str(ROOT)))
        self.server.token = 'secret-token'
        self.server.jobs = lab_server.Jobs()
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        headers = {'Host': f'localhost:{self.port}', **(headers or {})}
        payload = json.dumps(body).encode() if body is not None else None
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, data

    def test_lab_info_and_static_files_are_served_to_localhost(self):
        status, data = self.request('GET', '/api/lab')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)['token'], 'secret-token')
        self.assertEqual(self.request('GET', '/display/cuts/ink.json')[0], 200)

    def test_other_hostnames_are_refused(self):
        # A page on another site that rebinds its DNS to this machine still sends its own Host.
        self.assertEqual(self.request('GET', '/api/lab', headers={'Host': f'attacker.example:{self.port}'})[0], 403)

    def test_jobs_need_the_page_token_and_the_same_origin(self):
        job = dict(kind='build', cut={})
        self.assertEqual(self.request('POST', '/api/jobs', job)[0], 403)
        self.assertEqual(self.request('POST', '/api/jobs', job, {'X-Lab-Token': 'wrong'})[0], 403)
        self.assertEqual(self.request('POST', '/api/jobs', job, {'X-Lab-Token': 'secret-token',
                                                                  'Origin': 'https://attacker.example'})[0], 403)
        self.assertEqual(self.request('POST', '/api/jobs', dict(kind='shell'), {'X-Lab-Token': 'secret-token'})[0], 400)

    def test_one_job_at_a_time(self):
        with patch.object(lab_server.Jobs, 'run'):
            first = self.request('POST', '/api/jobs', dict(kind='build', cut={}), {'X-Lab-Token': 'secret-token'})
            second = self.request('POST', '/api/jobs', dict(kind='build', cut={}), {'X-Lab-Token': 'secret-token'})
        self.assertEqual((first[0], second[0]), (202, 409))


class LabJobTests(unittest.TestCase):
    def ink(self, **changes):
        return json.loads((ROOT/'display/cuts/ink.json').read_text(encoding='utf-8')) | changes

    def test_validation_accepts_lab_cuts_and_refuses_anything_else(self):
        self.assertEqual(lab_jobs.validate(self.ink(savedAt=1, pen='nib'))['pen'], 'nib')
        self.assertNotIn('savedAt', lab_jobs.validate(self.ink(savedAt=1)))
        for bad in (dict(name='../ink'), dict(weight='heavy'), dict(weight=9999), dict(pen='brush'),
                    dict(uFoot='yes'), dict(alternates=[]), dict(italicForms=1)):
            with self.assertRaises(ValueError, msg=bad):
                lab_jobs.validate(self.ink(**bad))

    def test_promote_keeps_the_file_order_and_float_spelling_and_rebuilds_only_that_cut(self):
        with tempfile.TemporaryDirectory() as directory:
            here = Path(directory)
            (here/'cuts').mkdir()
            source = (ROOT/'display/cuts/ink.json').read_text(encoding='utf-8')
            (here/'cuts/ink.json').write_text(source, encoding='utf-8')
            sent = json.loads(source) | dict(uFoot=True, uprightStraightness=1)  # JavaScript sends 1.0 as 1
            with patch.object(lab_jobs, 'HERE', here), patch('display.build_all_cuts.build_all') as build, \
                    patch.object(lab_jobs.subprocess, 'run'):
                result = lab_jobs.promote(sent)
            build.assert_called_once_with(only=['ink'])
            written = (here/'cuts/ink.json').read_text(encoding='utf-8')
            self.assertEqual(result['changed'], ['uFoot'])
            self.assertIn('"uprightStraightness": 1.0', written)
            self.assertEqual(list(json.loads(written)), list(json.loads(source)))

    def test_promote_refuses_new_cuts(self):
        with self.assertRaisesRegex(ValueError, 'no shipped cut'):
            lab_jobs.promote(self.ink(name='Lotus'))


if __name__ == '__main__':
    unittest.main()
