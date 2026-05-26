"""
Emotion Engine — Rule-based sentiment and emotion classification.
"""
from typing import Tuple

class EmotionDetector:
    def __init__(self):
        # Basic keyword-based heuristics for speed
        self.emotion_map = {
            "happy": [
                "great", "awesome", "happy", "love", "excellent", "good", "nice",
                "amazing", "fantastic", "super", "best", "cool", "wonderful",
                "proud", "excited", "smile", "smiling", "cheerful", "delighted",

                # Hindi / Hinglish
                "khush", "bahut khush", "badiya", "badhiya", "accha", "acha",
                "mast", "shandar", "zabardast", "maza aa gaya", "majedar",
                "khushi", "sukoon", "dil khush", "khush hu", "happy hu",
                "bohot accha", "bahut accha", "sahi hai", "ekdum mast",
                "jhakkas", "mind blowing", "dhamakedar", "gazab", "waah",
                "wah", "shaandaar", "solid", "top class"
            ],

            "sad": [
                "sad", "depressed", "unhappy", "terrible", "bad", "sorry",
                "hurt", "lonely", "cry", "crying", "low", "down", "upset",
                "broken", "heartbroken", "pain", "painful",

                # Hindi / Hinglish
                "dukhi", "udaas", "udas", "kharab", "bura", "gham",
                "mayus", "nirash", "dil toot gaya", "rona aa raha",
                "ro raha", "ro diya", "mann kharab", "akela",
                "tension me hu", "thak gaya", "toot gaya", "dukhi hu",
                "bahut bura", "dard", "takleef", "pareshan", "mann udaas",
                "jeene ka mann nahi", "hopeless", "bechain"
            ],

            "frustrated": [
                "annoyed", "frustrated", "angry", "hate", "stupid", "idiot",
                "damn", "wtf", "irritated", "mad", "furious", "rage",
                "fed up", "sick of it",

                # Hindi / Hinglish
                "gussa", "ghussa", "pagal", "bekaar", "bakwas",
                "dimag kharab", "dimag kharab ho gaya", "chidh",
                "chidh gaya", "pak gaya", "pareshan ho gaya",
                "tang aa gaya", "had ho gayi", "faltu", "kya yaar",
                "bohot irritating", "sir dard", "jhunjhla gaya",
                "gusse me hu", "frustrate ho gaya", "maar dunga",
                "samajh nahi aa raha", "irritate kar raha"
            ],

            "curious": [
                "why", "how", "what", "explain", "curious", "wondering",
                "tell me", "can you", "could you", "please explain",
                "meaning", "how come", "what is",

                # Hindi / Hinglish
                "kyu", "kyun", "kaise", "kya", "batao", "samjhao",
                "samjha", "matlab", "aisa kyu", "kaise hota hai",
                "ye kya hai", "mujhe jaan na hai", "detail me batao",
                "samajhna hai", "seekhna hai", "kya matlab", "kisliye",
                "kab", "kab tak", "kaun", "kaunsa", "kaunsi"
            ],

            "urgent": [
                "emergency", "urgent", "quick", "hurry", "asap", "now",
                "help", "immediately", "right now", "soon", "fast",
                "priority",

                # Hindi / Hinglish
                "jaldi", "zaroori", "jaruri", "turant", "abhi",
                "fatafat", "please hurry", "abhi chahiye", "urgent hai",
                "jaldi karo", "help karo", "bachao", "emergency hai",
                "time nahi hai", "abhi ke abhi", "instant", "turant help",
                "bahut urgent", "jaldi batao"
            ],

            "confused": [
                "confused", "not sure", "unclear", "doubt", "lost",
                "mixed up", "don't understand",

                # Hindi / Hinglish
                "samajh nahi aa raha", "confuse hu", "ulta lag raha",
                "kuch samajh nahi aa raha", "doubt hai", "clear nahi hai",
                "samajh me nahi aaya", "kaafi confusing", "phasa hua hu"
            ],

            "motivated": [
                "motivated", "inspired", "focused", "determined",
                "ready", "lets do it", "productive",

                # Hindi / Hinglish
                "kar lunga", "kar dunga", "full motivated", "josh",
                "junoon", "mehnat", "focus hai", "taiyar hu",
                "karke dikhaunga", "rukna nahi", "jeetunga",
                "confidence hai", "hustle", "goal", "sapna"
            ]
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
