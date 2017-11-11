import datetime
import unittest

from aiogram import types
from dataset import MESSAGE


class TestMessage(unittest.TestCase):
    def setUp(self):
        self.message = types.Message(**MESSAGE)

    def test_update_id(self):
        self.assertEqual(self.message.message_id, MESSAGE['message_id'], 'test')
        self.assertEqual(self.message['message_id'], MESSAGE['message_id'])

    def test_from(self):
        self.assertIsInstance(self.message.from_user, types.User)
        self.assertEqual(self.message.from_user, self.message['from'])

    def test_chat(self):
        self.assertIsInstance(self.message.chat, types.Chat)
        self.assertEqual(self.message.chat, self.message['chat'])

    def test_date(self):
        self.assertIsInstance(self.message.date, datetime.datetime)
        self.assertEqual(int(self.message.date.timestamp()), MESSAGE['date'])
        self.assertEqual(self.message.date, self.message['date'])

    def test_text(self):
        self.assertEqual(self.message.text, MESSAGE['text'])
        self.assertEqual(self.message['text'], MESSAGE['text'])


if __name__ == '__main__':
    unittest.main()
