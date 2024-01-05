import unittest
from unittest.mock import patch
from helpers import get_mock_discord_message, get_response
from lib.Responses import help
from lib.Responses import gpt

class TestHelp(unittest.TestCase):
    to = help.Help()

    def setUp(self):
        # Setup responses that are useful for this test
        self.to.responses = {'_gpt': gpt.GptResponse(), 'prompt': gpt.ChangePrompt(), 'ai4': gpt.Gpt4Completion()}

    def test_general_case_filtering(self):
        # Test that only the responses with blurbs show up
        request = get_mock_discord_message()
        actual, context = get_response(self.to, "", request)

        expected = 'Sure! here is a list of commands:\n' 
        expected += '* prompt: {}\n'.format(gpt.ChangePrompt().blurb)
        expected +='* ai4: {}'.format(gpt.Gpt4Completion().blurb)
        expected += help.get_non_response_commands()

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)

    def test_specific_help_texts(self):
        # Test requesting specific help texts, and that it uses either
        #   get_help or the default blurb as avaliable
        request = get_mock_discord_message()
        actual, context = get_response(self.to, "prompt ai4", request)     
        expected = gpt.ChangePrompt().get_help()
        expected += '\n\n'
        # GPT4 doesnt have custom help text, so it uses the blurb instead
        expected += "!ai4 will " + gpt.Gpt4Completion().blurb + "."

        self.assertEqual(actual, expected)
        self.assertEqual(context, request)