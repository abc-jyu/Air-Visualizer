# 感情分析ロジック
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, Optional
import asyncio

# Global variables for model and tokenizer
_model: Optional[AutoModelForSequenceClassification] = None
_tokenizer: Optional[AutoTokenizer] = None
_device: str = "cpu"

# Emotion mapping for WRIME dataset (8 emotions)
EMOTION_LABELS = [
    "喜び",      # joy
    "悲しみ",    # sadness
    "期待",      # anticipation
    "驚き",      # surprise
    "怒り",      # anger
    "恐れ",      # fear
    "嫌悪",      # disgust
    "信頼"       # trust
]


async def initialize_sentiment_model() -> None:
    """Initialize the sentiment analysis model on startup"""
    global _model, _tokenizer

    try:
        # Load tokenizer and model from HuggingFace Hub
        model_name = "neuralnaut/deberta-wrime-emotions"

        print(f"Loading sentiment model: {model_name}...")

        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load model (already fine-tuned for WRIME emotions)
        _model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=8  # 8 WRIME emotions
        )

        # Set to evaluation mode
        _model.eval()

        # Move to CPU
        _model.to(_device)

        # Set CPU thread count for optimization
        torch.set_num_threads(4)

        print(f"✓ Sentiment model loaded successfully on {_device}")

    except Exception as e:
        print(f"✗ Failed to load sentiment model: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow app to start without sentiment analysis


async def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of Japanese text

    Args:
        text: Japanese text string to analyze

    Returns:
        Dictionary with emotion scores:
        {
            "喜び": 0.1,
            "悲しみ": 0.05,
            "期待": 0.15,
            "驚き": 0.10,
            "怒り": 0.05,
            "恐れ": 0.05,
            "嫌悪": 0.05,
            "信頼": 0.50
        }
    """
    if _model is None or _tokenizer is None:
        raise RuntimeError("Sentiment model not initialized. Call initialize_sentiment_model() first.")

    if not text or not text.strip():
        # Return neutral scores for empty text
        return {label: 0.0 for label in EMOTION_LABELS}

    try:
        # Run inference in thread pool to not block event loop
        result = await asyncio.to_thread(_run_inference, text)
        return result

    except Exception as e:
        print(f"Error during sentiment analysis: {e}")
        import traceback
        traceback.print_exc()
        # Return neutral scores on error
        return {label: 0.0 for label in EMOTION_LABELS}


def _run_inference(text: str) -> Dict[str, float]:
    """
    Synchronous inference function (runs in thread pool)
    """
    # Tokenize input
    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )

    # Move to device
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    # Run inference
    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits

    # Apply softmax to get probabilities
    probabilities = torch.nn.functional.softmax(logits, dim=-1)

    # Convert to dictionary
    scores = probabilities[0].cpu().numpy().tolist()

    return {
        label: float(score)
        for label, score in zip(EMOTION_LABELS, scores)
    }


async def shutdown_sentiment_model() -> None:
    """Clean up model resources"""
    global _model, _tokenizer
    _model = None
    _tokenizer = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("✓ Sentiment model cleaned up")
