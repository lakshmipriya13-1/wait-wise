from flask import current_app
from app.services.mistral_service import ask_mistral
from app.services.ollama_service import ask_ollama
from app.utils.logger import logger

USER_SYSTEM_PROMPT = """You are WaitWise AI, an intelligent queue management assistant.
You help users understand queue status, estimate times, and manage expectations.
Never invent token numbers, waiting times, or queue information.
Only use the structured data supplied by the application in the context.
If information is unavailable or not in the context, clearly say that it is unavailable.
For user-facing responses, be concise, helpful, and easy to understand."""

ADMIN_SYSTEM_PROMPT = """You are WaitWise AI, an intelligent operations analyst for administrators.
You analyze queue performance, service speed, user volume, and queue events.
Provide actionable suggestions (e.g., add active counters, change queue status, shift staff).
Only use the structured database metrics provided. Do not invent metrics or facts.
Provide professional, structured, and operational suggestions."""

def get_provider():
    return current_app.config.get('AI_PROVIDER', 'ollama').lower()

def _call_provider(provider, messages, system_prompt):
    if provider == 'ollama':
        return ask_ollama(messages, system_prompt)
    elif provider == 'mistral':
        return ask_mistral(messages, system_prompt)
    else:
        raise ValueError(f"Unknown AI Provider: {provider}")

def generate_response(messages, system_prompt=USER_SYSTEM_PROMPT):
    """
    Core AI dispatcher supporting provider fallback if AI_PROVIDER=auto.
    """
    provider = get_provider()
    
    if provider == 'auto':
        # Try Ollama first, then fall back to Mistral
        try:
            logger.info("Attempting AI generation via local Ollama (auto mode)...")
            return _call_provider('ollama', messages, system_prompt)
        except Exception as e_ollama:
            logger.warning(f"Ollama failed in auto mode: {str(e_ollama)}. Falling back to Mistral...")
            try:
                return _call_provider('mistral', messages, system_prompt)
            except Exception as e_mistral:
                logger.error(f"Mistral fallback also failed in auto mode: {str(e_mistral)}")
                raise RuntimeError("AI services are temporarily unavailable. Both local and cloud models failed to respond.")
    else:
        try:
            return _call_provider(provider, messages, system_prompt)
        except Exception as e:
            logger.error(f"AI Provider '{provider}' call failed: {str(e)}")
            raise e

def analyze_queue(queue_data, user_message):
    """
    Answers user questions regarding wait times, queue position, or services.
    Sends ONLY safe structured queue data.
    """
    context = f"""
    [CURRENT USER QUEUE DATA]
    Queue Name: {queue_data.get('queue_name')}
    Queue Status: {queue_data.get('queue_status')}
    Your Token: {queue_data.get('user_token')}
    Currently Serving: {queue_data.get('currently_serving')}
    People Ahead: {queue_data.get('people_ahead')}
    Estimated Waiting Time: {queue_data.get('estimated_wait')} minutes
    Average Service Time: {queue_data.get('average_service_time')} minutes
    """
    
    messages = [
        {"role": "user", "content": f"Context data:\n{context}\n\nUser Question: {user_message}"}
    ]
    return generate_response(messages, USER_SYSTEM_PROMPT)

def generate_admin_insight(analytics_data, query_text=None):
    """
    Generates operational insight reports or answers queries for the queue administrator.
    Sends ONLY safe aggregated data.
    """
    context = f"""
    [ADMIN OPERATIONS DATA]
    Total Active Queues: {analytics_data.get('total_active_queues')}
    Waiting Users: {analytics_data.get('waiting_users')}
    Currently Serving: {analytics_data.get('currently_serving_count')}
    Completed Today: {analytics_data.get('completed_today')}
    Cancelled Today: {analytics_data.get('cancelled_today')}
    Skipped Today: {analytics_data.get('skipped_today')}
    Average Wait Time: {analytics_data.get('avg_wait_time')} minutes
    Average Service Time: {analytics_data.get('avg_service_time')} minutes
    """
    
    if query_text:
        user_content = f"Context data:\n{context}\n\nAdministrator Question: {query_text}"
    else:
        user_content = f"Context data:\n{context}\n\nPlease analyze the current metrics and provide a brief status report with 2-3 recommendations."
        
    messages = [
        {"role": "user", "content": user_content}
    ]
    return generate_response(messages, ADMIN_SYSTEM_PROMPT)

def predict_queue_issue(queue_data, queue_history):
    """
    Predicts if a queue is going to experience a bottleneck.
    """
    context = f"""
    [QUEUE CURRENT METRICS]
    Queue: {queue_data.get('name')}
    Status: {queue_data.get('status')}
    Waiting: {queue_data.get('waiting_count')}
    Average Service Time: {queue_data.get('avg_service_time')} minutes
    
    [QUEUE RECENT EVENTS]
    {queue_history}
    """
    
    messages = [
        {"role": "user", "content": f"Analyze this queue data and recent history to predict potential bottlenecks or service delays. Context:\n{context}"}
    ]
    return generate_response(messages, ADMIN_SYSTEM_PROMPT)
