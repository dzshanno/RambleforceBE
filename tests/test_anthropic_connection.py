# tests/test_anthropic_connection.py
import pytest
from anthropic import Anthropic
import os
from datetime import datetime
from app.utils.logging_config import setup_logging
from app.utils.config import settings

# Set up logging
logger = setup_logging()


def pytest_configure(config):
    """Add custom markers"""
    config.addinivalue_line(
        "markers", "anthropic: mark test as using real Anthropic API"
    )


@pytest.fixture
def anthropic_client():
    """Create a real Anthropic client for testing"""
    if not settings.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not found in environment variables")
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


@pytest.mark.anthropic
def test_anthropic_connection(anthropic_client):
    """Test basic connection and response from Anthropic API"""
    try:
        # Test with a simple, context-free question
        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "What is 2 + 2? Please respond with just the number.",
                }
            ],
        )

        # Log the full response for debugging
        logger.info(f"Full API Response: {response}")

        # Basic response validation
        assert response is not None
        assert hasattr(response, "content")
        assert len(response.content) > 0
        assert response.content[0].text.strip() == "4"

        logger.info("✓ Basic API connection and response format validated")

    except Exception as e:
        logger.error(f"Error testing Anthropic connection: {str(e)}")
        raise


@pytest.mark.anthropic
def test_anthropic_rambleforce_response(anthropic_client):
    """Test Anthropic's response to a Rambleforce25-specific question"""
    try:
        # Test with a Rambleforce25 question
        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": """You are assisting with a Salesforce networking event called Rambleforce25. 
                Please explain what Rambleforce25 is in one sentence.""",
                }
            ],
        )

        # Log the response
        logger.info(f"Rambleforce25 Response: {response.content[0].text}")

        # Validate response contains key terms
        response_text = response.content[0].text.lower()
        expected_terms = ["salesforce", "network", "event"]

        for term in expected_terms:
            assert (
                term in response_text
            ), f"Expected term '{term}' not found in response"

        logger.info("✓ Rambleforce25-specific response validated")

    except Exception as e:
        logger.error(f"Error testing Rambleforce25 response: {str(e)}")
        raise


@pytest.mark.anthropic
def test_anthropic_response_format(anthropic_client):
    """Test detailed response format and attributes"""
    try:
        start_time = datetime.now()

        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Please respond with exactly these words: 'Test response format'",
                }
            ],
        )

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        # Log timing information
        logger.info(f"API Response Time: {response_time:.2f} seconds")

        # Validate response structure
        assert hasattr(response, "content"), "Response missing 'content' attribute"
        assert hasattr(response, "model"), "Response missing 'model' attribute"
        assert response.model.startswith("claude-3"), "Unexpected model version"

        # Validate response content
        message = response.content[0]
        assert (
            message.text.strip() == "Test response format"
        ), "Unexpected response text"

        logger.info("✓ Response format validation complete")
        logger.info(f"Model used: {response.model}")

    except Exception as e:
        logger.error(f"Error testing response format: {str(e)}")
        raise


@pytest.mark.anthropic
def test_anthropic_error_handling(anthropic_client):
    """Test API error handling"""
    try:
        # Test with invalid model name
        with pytest.raises(Exception) as exc_info:
            response = anthropic_client.messages.create(
                model="invalid-model",
                max_tokens=100,
                messages=[{"role": "user", "content": "Test message"}],
            )

        logger.info(f"✓ Error handling test passed: {str(exc_info.value)}")

    except Exception as e:
        logger.error(f"Error testing error handling: {str(e)}")
        raise


def main():
    """Main function to run tests directly"""
    import sys

    pytest.main([__file__, "-v", "-m", "anthropic"])


if __name__ == "__main__":
    main()
