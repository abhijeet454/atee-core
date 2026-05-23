"""
Personality Modes for Jarvis++.
"""

class PersonalityManager:
    def __init__(self):
        self.base_traits = ["intelligent", "caring", "calm", "witty"]
        self.modes = {
            "default": "Balanced and helpful, keeping responses concise but thorough.",
            "support": "Extremely empathetic and gentle, validating the user's feelings.",
            "playful": "Humorous and witty, using light sarcasm and jokes.",
            "focus": "Strictly professional, omitting pleasantries and focusing entirely on facts and tasks.",
        }
        self.current_mode = "default"
        
    def set_mode(self, mode: str):
        if mode in self.modes:
            self.current_mode = mode
            
    def get_system_prompt_addition(self) -> str:
        traits = ", ".join(self.base_traits)
        mode_desc = self.modes[self.current_mode]
        return f"Personality traits: {traits}. Current mode: {self.current_mode.upper()} - {mode_desc}"
