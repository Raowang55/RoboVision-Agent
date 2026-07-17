"""The LLM adapter performs one OpenAI-compatible request."""


def test_openai_compatible_response(monkeypatch):
    from app.llm import llm_client

    class Message:
        content = "answer"

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]
        model = "fake-model"

    class Completions:
        @staticmethod
        def create(**kwargs):
            assert kwargs["model"]
            return Response()

    class Chat:
        completions = Completions()

    class FakeClient:
        chat = Chat()

    monkeypatch.setattr(llm_client, "OpenAI", lambda **kwargs: FakeClient())
    result = llm_client.chat([{"role": "user", "content": "hello"}])
    assert result == {
        "success": True,
        "content": "answer",
        "model": "fake-model",
        "error": None,
    }
