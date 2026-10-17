import json
import unittest
from io import BytesIO
from unittest.mock import patch

from tear_reproduction.client import OpenAICompatibleClient


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class ClientTests(unittest.TestCase):
    def test_chat_request_uses_compatible_payload_and_auth(self):
        payload = {
            "choices": [{"message": {"content": "{\"ok\": true}"}}],
        }
        response = FakeResponse(json.dumps(payload).encode())
        client = OpenAICompatibleClient(
            "http://localhost:1234/v1",
            "test-model",
            api_key="secret",
        )
        with patch(
            "tear_reproduction.client.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            result = client.chat("system", "user")
        self.assertEqual(result, '{"ok": true}')
        request = urlopen.call_args.args[0]
        sent = json.loads(request.data.decode())
        self.assertEqual(request.full_url, "http://localhost:1234/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(sent["model"], "test-model")
        self.assertEqual(sent["temperature"], 0.5)
        self.assertEqual(sent["top_p"], 0.5)

    def test_embeddings_are_returned_in_request_order(self):
        payload = {
            "data": [
                {"index": 1, "embedding": [0.0, 1.0]},
                {"index": 0, "embedding": [1.0, 0.0]},
            ]
        }
        client = OpenAICompatibleClient(
            "http://localhost:1234/v1",
            "test-model",
            embedding_model="test-embedding-model",
        )
        with patch(
            "tear_reproduction.client.urllib.request.urlopen",
            return_value=FakeResponse(json.dumps(payload).encode()),
        ):
            self.assertEqual(client.embed(["first", "second"]), [[1.0, 0.0], [0.0, 1.0]])

    def test_embedding_request_without_model_fails(self):
        client = OpenAICompatibleClient("http://localhost:1234/v1", "test-model")
        with self.assertRaisesRegex(RuntimeError, "embedding_model"):
            client.embed(["text"])


if __name__ == "__main__":
    unittest.main()
