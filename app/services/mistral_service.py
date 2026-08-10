import os
import requests
from flask import current_app
from app.utils.logger import logger

def ask_mistral(messages, system_prompt=None):
    """
    Calls the Mistral AI API with the specified messages and optional system prompt.
    """
    api_key = current_app.config.get('MISTRAL_API_KEY') or os.environ.get('MISTRAL_API_KEY')
    model = current_app.config.get('MISTRAL_MODEL', 'mistral-tiny')
    
    if not api_key:
        logger.error("Mistral API Key is missing.")
        raise ValueError("Mistral AI service is misconfigured: API Key is missing.")
        
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload_messages = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})
        
    payload_messages.extend(messages)
    
    data = {
        "model": model,
        "messages": payload_messages,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Mistral API returned status code {response.status_code}: {response.text}")
            raise Exception(f"Mistral API error: {response.text}")
    except requests.exceptions.Timeout:
        logger.error("Mistral API request timed out.")
        raise TimeoutError("Mistral AI request timed out. Please try again.")
    except Exception as e:
        logger.error(f"Error calling Mistral API: {str(e)}")
        raise e
