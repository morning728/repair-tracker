import tempfile
import unittest
from pathlib import Path

from app import create_app
from store import create_request, get_request


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'requests.db'
        self.app = create_app(self.path)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']
        self.values = dict(client='Анна Иванова', phone='+7 900 123-45-67', device='ThinkPad',
                           device_type='Ноутбук', problem='Не включается', priority='Высокий', status='Новая')
        self.id = create_request(self.path, self.values)

    def tearDown(self):
        self.temp.cleanup()

    def test_list_and_case_insensitive_search(self):
        response = self.client.get('/?q=ИВАНОВА')
        self.assertIn('Анна Иванова', response.get_data(as_text=True))
        response = self.client.get('/?q=unknown')
        self.assertIn('Ничего не найдено', response.get_data(as_text=True))

    def test_filters(self):
        response = self.client.get('/?status=Готова')
        self.assertNotIn('ThinkPad', response.get_data(as_text=True))
        self.assertEqual(self.client.get('/?status=wrong').status_code, 400)

    def test_detail_and_missing(self):
        self.assertIn('Не включается', self.client.get(f'/requests/{self.id}').get_data(as_text=True))
        self.assertEqual(self.client.get('/requests/999').status_code, 404)

    def test_edit_and_validation(self):
        url = f'/requests/{self.id}/edit'
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, data={**self.values, 'status': 'В работе', 'csrf_token': self.token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_request(self.path, self.id)['status'], 'В работе')
        response = self.client.post(url, data={**self.values, 'phone': '123', 'csrf_token': self.token})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(get_request(self.path, self.id)['status'], 'В работе')

    def test_delete_requires_post_and_token(self):
        url = f'/requests/{self.id}/delete'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertIsNotNone(get_request(self.path, self.id))
        self.assertEqual(self.client.post(url, data={'csrf_token': self.token}).status_code, 302)
        self.assertIsNone(get_request(self.path, self.id))
        self.assertEqual(self.client.post(url, data={'csrf_token': self.token}).status_code, 404)

    def test_html_is_escaped(self):
        create_request(self.path, {**self.values, 'client': '<script>alert(1)</script>'})
        html = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_pagination(self):
        for i in range(16):
            create_request(self.path, {**self.values, 'client': f'Клиент {i}'})
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('Страница 1 из 2', html)
        html = self.client.get('/?page=2').get_data(as_text=True)
        self.assertIn('Страница 2 из 2', html)
        self.assertIn('Страница 1 из 2', self.client.get('/?page=oops').get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
