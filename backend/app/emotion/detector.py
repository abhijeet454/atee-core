"""
Emotion Engine — Rule-based sentiment and emotion classification.
"""
from typing import Tuple

class EmotionDetector:
    def __init__(self):
        # Basic keyword-based heuristics for speed
        self.emotion_map = {
            "happy": ["great", "awesome", "happy", "love", "excellent", "good", "khush", "badiya", "accha", "mast", "shandar"],
            "sad": ["sad", "depressed", "unhappy", "terrible", "bad", "sorry", "dukhi", "kharab", "udaas", "bura"],
            "frustrated": ["annoyed", "frustrated", "angry", "hate", "stupid", "idiot", "damn", "wtf", "gussa", "pagal", "bekaar", "dimag kharab"],
            "curious": ["why", "how", "what", "explain", "curious", "wondering", "kyu", "kaise", "kya", "batao"],
            "urgent": ["emergency", "urgent", "quick", "hurry", "asap", "now", "help", "jaldi", "zaroori", "turant"],
        }
        
    def detect(self, text: str) -> Tuple[str, float]:
        """Returns (emotion, confidence_score)"""
        text_lower = text.lower()
        
        scores = {emotion: 0 for emotion in self.emotion_map}
        total_hits = 0
        
        for emotion, keywords in self.emotion_map.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[emotion] += 1
                    total_hits += 1
                    
        if total_hits == 0:
            return "neutral", 0.5
            
        # Get the highest scoring emotion
        max_emotion = max(scores, key=scores.get)
        confidence = min(0.5 + (scores[max_emotion] * 0.1), 0.95)
        
        return max_emotion, confidence
