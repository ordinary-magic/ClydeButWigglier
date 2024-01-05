import unittest
from unittest.mock import patch
from helpers import get_mock_discord_message, get_response
from lib.Responses import basic

class TestTime(unittest.TestCase):
    to = basic.Time()

    def test_time_response(self):
        # Construct a bare message with the id embedded in it
        mock_request = get_mock_discord_message(author_id = 9001)

        # Mock the time so we dont have to deal with real time
        with patch('time.time', return_value="1369"):
            actual, context = get_response(self.to, "", mock_request,)
            
        expected = "<@9001>, your current time is <t:1369:t>. Yay!"
        self.assertEqual(actual, expected)
        self.assertEqual(context, None)

class TestRavioli(unittest.TestCase):
    to = basic.Ravioli()

    def test_ravioli_response(self):
        expected = 'i feel down the stairs and ravioli on me'
        request = get_mock_discord_message()
        actual, context = get_response(self.to, "", request)
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)

class TestEightBall(unittest.TestCase):
    to = basic.EightBall()

    def setUp(self):
        # Replace the responses with preset ones for convenience
        self.to.responses_canon_yes = ['yes']
        self.to.responses_canon_no = ['no']
        self.to.responses_canon_maybe = ['mabye']
        self.to.responses_wiggly = ['wiggly']

    def test_eightball_responses(self):
        # Run the test on each of the possible outcome sets
        cases = [(0.0, "mabye"), (0.5, "yes"), (0.75, "no"), (0.99, "wiggly")]
        for (roll, result) in cases:
            with self.subTest(result):
                request = get_mock_discord_message()

                # Replace the random result with a specific one instead
                with patch('random.random', return_value=roll):
                    actual, context = get_response(self.to, "", request)
                
                self.assertEqual(actual, result)
                self.assertEqual(context, request)

class TestScared(unittest.TestCase):
    to = basic.Scared()

    def test_scared_response(self):
        expected = 'a' * 2001
        request = get_mock_discord_message()
        actual, context = get_response(self.to, "", request)
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)

class TestHighCheck(unittest.TestCase):
    to = basic.HighCheck()

    def setUp(self):
        # Replace the responses with preset ones for convenience
        self.to.adjetives = ['high']

    def test_valid_high_response(self):
        request = get_mock_discord_message(mentions = [12345])

        # Replace the random result with a specific one (69%) instead
        with patch('random.randint', return_value=690):
            actual, context = get_response(self.to, "", request)
        
        expected = "<@12345> is 69.0% high"
        self.assertEqual(actual, expected)
        self.assertEqual(context, request)

    def test_invalid_high_response(self):
        # No mentions means the message is ignored
        request = get_mock_discord_message()
        actual, _ = get_response(self.to, "", request)
        self.assertEqual(actual, None)