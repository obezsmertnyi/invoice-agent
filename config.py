# config.py - Updated for October 2025
import os

# Default model if not set in environment
DEFAULT_PRIMARY_MODEL = "gpt-5-nano"

def get_primary_model():
    """Get primary model from environment or use default"""
    return os.getenv('PRIMARY_MODEL', DEFAULT_PRIMARY_MODEL)

MODEL_CONFIGS = {
    "openai": {
        "models": ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4.1", "gpt-4.1-mini", "gpt-4o", "o3", "o3-mini", "o4-mini"],
        "best_for": "Highest accuracy, reasoning, coding",
        "cost": "$-$$$",
        "speed": "Fast"
    },
    "anthropic": {
        "models": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5", "claude-opus-4-1", "claude-sonnet-4", "claude-opus-4"],
        "best_for": "Long documents (200K-1M context), extended thinking, vision",
        "cost": "$$-$$$",
        "speed": "Fast to Lightning-fast"
    },
    "ollama": {
        "models": ["llama3.3", "qwen2.5:14b", "mistral", "deepseek-r1:7b"],
        "best_for": "Local processing, privacy, no API costs",
        "cost": "Free",
        "speed": "Moderate"
    },
    "cohere": {
        "models": ["command-r-plus", "command-r", "command"],
        "best_for": "Bulk processing, multilingual",
        "cost": "$",
        "speed": "Very Fast"
    }
}

def get_optimal_model(requirements):
    """Select optimal model based on requirements (October 2025 models)"""
    if requirements.get("privacy_critical"):
        return "ollama/llama3.3"  # Latest Llama 3.3 (local, free)
    elif requirements.get("reasoning_required"):
        return "o3"  # OpenAI o3 reasoning model
    elif requirements.get("coding_required"):
        return "gpt-5"  # GPT-5 for code
    elif requirements.get("highest_accuracy"):
        return "gpt-5"  # GPT-5 flagship
    elif requirements.get("mini_model"):
        return "gpt-5-mini"  # GPT-5-mini (highlighted in pricing)
    elif requirements.get("long_document"):
        return "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 (200K-1M context)
    elif requirements.get("speed_critical"):
        return "claude-haiku-4-5"  # Claude Haiku 4.5 (lightning-fast)
    elif requirements.get("cost_sensitive"):
        return "gpt-4o-mini"  # Most cost-effective proven model
    elif requirements.get("multilingual"):
        return "command-r-plus"  # Cohere multilingual
    else:
        return "gpt-5-nano"  # Default: cheapest model ($0.05/$0.40 per 1M tokens)