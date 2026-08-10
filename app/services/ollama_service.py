import requests
from flask import current_app
from app.utils.logger import logger

def ask_ollama(messages, system_prompt=None):
    """
    Calls the local Ollama API with the specified messages and optional system prompt.
    """
    base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = current_app.config.get('OLLAMA_MODEL', 'gemma')
    
    url = f"{base_url.rstrip('/')}/api/chat"
    
    payload_messages = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})
        
    payload_messages.extend(messages)
    
    data = {
        "model": model,
        "messages": payload_messages,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result['message']['content']
        else:
            logger.error(f"Ollama API returned status code {response.status_code}: {response.text}")
            raise Exception(f"Ollama API error: status {response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Ollama connection failed at URL: {url}. Make sure Ollama is running locally.")
        raise ConnectionError("Local AI service (Ollama) is currently unavailable. Please make sure it is running.")
    except requests.exceptions.Timeout:
        logger.error("Ollama API request timed out.")
        raise TimeoutError("Ollama AI request timed out.")
    except Exception as e:
        logger.error(f"Error calling Ollama API: {str(e)}")
        raise e
