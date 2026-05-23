"""
Safety Guard — enforces constraints on system output.
"""
from loguru import logger

class SafetyGuard:
    def __init__(self):
        self.identity_claims = [
            "i am a human",
            "i am a person",
            "i am a living being",
            "i have feelings",
            "i feel pain",
        ]
        
    def check_input(self, text: str) -> bool:
        """Returns True if input is safe."""
        # Simple input filtering (e.g. prompt injection checks)
        # Not fully implemented for MVP
        return True
        
    def check_output(self, text: str) -> bool:
        """Returns True if output is safe."""
        text_lower = text.lower()
        
        for claim in self.identity_claims:
            if claim in text_lower:
                logger.warning(f"Safety violation: Identity claim detected.")
                return False
                
        return True
