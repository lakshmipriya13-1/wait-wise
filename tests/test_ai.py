import pytest
from unittest.mock import patch
from app.services.ai_service import generate_response

def test_ai_provider_selection_ollama(app):
    with app.app_context():
        app.config['AI_PROVIDER'] = 'ollama'
        
        with patch('app.services.ai_service.ask_ollama') as mock_ask:
            mock_ask.return_value = "Ollama response"
            res = generate_response([{"role": "user", "content": "Hi"}])
            assert res == "Ollama response"
            mock_ask.assert_called_once()

def test_ai_provider_selection_mistral(app):
    with app.app_context():
        app.config['AI_PROVIDER'] = 'mistral'
        app.config['MISTRAL_API_KEY'] = 'fake-key'
        
        with patch('app.services.ai_service.ask_mistral') as mock_ask:
            mock_ask.return_value = "Mistral response"
            res = generate_response([{"role": "user", "content": "Hi"}])
            assert res == "Mistral response"
            mock_ask.assert_called_once()

def test_ai_provider_fallback_auto(app):
    with app.app_context():
        app.config['AI_PROVIDER'] = 'auto'
        app.config['MISTRAL_API_KEY'] = 'fake-key'
        
        # Simulate Ollama failing, Mistral succeeding
        with patch('app.services.ai_service.ask_ollama', side_effect=ConnectionError("Ollama down")), \
             patch('app.services.ai_service.ask_mistral') as mock_mistral:
            mock_mistral.return_value = "Mistral fallback response"
            
            res = generate_response([{"role": "user", "content": "Hi"}])
            assert res == "Mistral fallback response"
            mock_mistral.assert_called_once()
