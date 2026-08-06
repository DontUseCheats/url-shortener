import unittest
from main import app
from unittest.mock import patch, MagicMock

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
            # runs before every test
        

    # Fake function
    @patch('main.get_connection')
    def test_post_route(self, mock_get_connection):
        # configuring the fake function
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor().fetchone.return_value = None

        # send POST request
        response = self.client.post('/shorten', json={'url': 'https://www.google.com'})

        # assert results test
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertEqual(len(response_text), 6)


    @patch('main.get_connection')
    def test_get_route(self, mock_get_connection):
        # configuring the fake function
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor().fetchone.return_value = ('https://www.google.com',)

        # send GET request
        response = self.client.get('/abc123')

        # assert results test
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://www.google.com', response.headers['Location'])