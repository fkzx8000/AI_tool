import openai
import unittest
from unittest.mock import patch

openai.api_key = 'you openai KEY'


def is_api_key_valid():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "This is a test."}
            ],
            max_tokens=1
        )
    except openai.error.OpenAIError as e:
        print(f"OpenAI error: {e}")
        return False
    except Exception as e:
        print(f"General error: {e}")
        return False
    else:
        return True


class TestAPIKeyValidity(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_api_key_valid(self, mock_create):
        # Mock a successful response
        mock_create.return_value = {"choices": [{"message": {"role": "assistant", "content": "Test"}}]}

        self.assertTrue(is_api_key_valid())

    @patch('openai.ChatCompletion.create')
    def test_api_key_invalid(self, mock_create):
        # Mock an OpenAI error
        mock_create.side_effect = openai.error.OpenAIError("Invalid API key")

        self.assertFalse(is_api_key_valid())

    @patch('openai.ChatCompletion.create')
    def test_general_error(self, mock_create):
        # Mock a general exception
        mock_create.side_effect = Exception("General error")

        self.assertFalse(is_api_key_valid())


if __name__ == '__main__':
    unittest.main()
