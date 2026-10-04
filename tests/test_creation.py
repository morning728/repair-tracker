import tempfile
import unittest
from pathlib import Path

from app import create_app
from store import get_request


class CreationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / 'requests.db'
        self.app = create_app(self.database)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.client.get('/requests/new')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']
        self.values = dict(client='Анна Иванова', phone='+7 (900) 123-45-67',
            device='Lenovo ThinkPad', device_type='Ноутбук', problem='Не включается',
            priority='Высокий', status='Новая', csrf_token=self.token)

    def tearDown(self):
        self.temp.cleanup()

    def test_create_and_persist(self):
        response = self.client.post('/requests/new', data=self.values)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_request(self.database, 1)['client'], 'Анна Иванова')
        other_client = create_app(self.database).test_client()
        self.assertEqual(other_client.get('/').status_code, 200)
        self.assertEqual(get_request(self.database, 1)['device'], 'Lenovo ThinkPad')

    def test_invalid_phone_retains_fields(self):
        response = self.client.post('/requests/new', data={**self.values, 'phone': '123'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('Анна Иванова', response.get_data(as_text=True))
        self.assertIsNone(get_request(self.database, 1))

    def test_invalid_option_is_rejected(self):
        response = self.client.post('/requests/new', data={**self.values, 'priority': 'unknown'})
        self.assertEqual(response.status_code, 422)

    def test_csrf_is_required(self):
        response = self.client.post('/requests/new', data={**self.values, 'csrf_token': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(get_request(self.database, 1))

    def test_empty_fields_are_rejected(self):
        response = self.client.post('/requests/new', data={'csrf_token': self.token})
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
