
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from openai import APITimeoutError, APIConnectionError, APIStatusError
import os
import subprocess
import sys



client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Restaurant AI Assistant is running",
        "status": "ok",
    }




def test_chat():
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "چلوکباب پیشنهاد می‌کنم."

    with patch(
        "app.main.client.chat.completions.create",
        return_value=fake_response,
    ) as mock_ai:
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 200
    assert response.json()["question"] == "چی بخورم؟"
    assert response.json()["answer"] == "چلوکباب پیشنهاد می‌کنم."

    mock_ai.assert_called_once()



def test_chat_empty_question():
    response = client.post(
        "/chat",
        json={"question": ""},
    )

    assert response.status_code == 422



def test_chat_question_too_long():
    response = client.post(
        "/chat",
        json={"question": "a" * 2001},
    )

    assert response.status_code == 422


def test_chat_missing_question():
    response = client.post(
        "/chat",
        json={},
    )

    assert response.status_code == 422



def test_chat_question_wrong_type():
    response = client.post(
        "/chat",
        json={"question": 123},
    )

    assert response.status_code == 422



def test_chat_timeout():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=APITimeoutError(
            request=MagicMock()
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 504
    assert response.json()["detail"] == "AI service timed out"


def test_chat_connection_error():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=APIConnectionError(
            request=MagicMock()
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Could not connect to AI service"


def test_chat_authentication_error():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=APIStatusError(
            message="Unauthorized",
            response=MagicMock(status_code=401),
            body=None,
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "AI service authentication failed"

    
def test_chat_rate_limit_error():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=APIStatusError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI service rate limit or quota exceeded"
    )


def test_chat_empty_ai_response():
    fake_response = MagicMock()

    fake_response.choices[0].message.content = "   "

    with patch(
        "app.main.client.chat.completions.create",
        return_value=fake_response,
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "AI returned an empty response"

    fake_response.choices[0].message.content = None

    with patch(
        "app.main.client.chat.completions.create",
        return_value=fake_response,
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "AI returned an empty response"


def test_chat_unexpected_error():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=RuntimeError("Unexpected failure"),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Unexpected AI service error"



def test_chat_other_api_status_error():
    with patch(
        "app.main.client.chat.completions.create",
        side_effect=APIStatusError(
            message="Server error",
            response=MagicMock(status_code=500),
            body=None,
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "چی بخورم؟"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "AI service returned an error"


def test_missing_api_key_or_model():
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = ""
    env["OPENROUTER_MODEL"] = ""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from dotenv import load_dotenv; "
            "load_dotenv = lambda *args, **kwargs: False; "
            "import app.main",
        ],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert (
        "OPENROUTER_API_KEY or OPENROUTER_MODEL is missing from .env"
        in result.stderr
    )


      