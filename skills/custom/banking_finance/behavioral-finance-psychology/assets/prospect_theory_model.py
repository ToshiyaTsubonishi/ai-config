import math
import time
import functools

# --- Optimization: Cache Decorator ---
# Based on project finding: High-frequency psychological scoring requires caching.
def lru_cache_with_ttl(maxsize=128, ttl=60):
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
            result = func(*args, **kwargs)
            if len(cache) >= maxsize:
                # Simple eviction (remove first key)
                del cache[next(iter(cache))]
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

class ProspectTheoryModel:
    """
    Implements Behavioral Finance models (Prospect Theory) to quantify user psychology.
    Used for 'Empathy Guardrails' in AGI Banking Systems.
    
    Key Concepts:
    - Loss Aversion: Lambda (approx 2.25)
    - Diminishing Sensitivity: Alpha (approx 0.88)
    """
    
    def __init__(self, lambda_param=2.25, alpha=0.88):
        self.lambda_param = lambda_param # Loss aversion coefficient
        self.alpha = alpha # Diminishing sensitivity

    @lru_cache_with_ttl(maxsize=1024, ttl=300) 
    def calculate_subjective_value(self, amount: float) -> float:
        """
        Calculates V(x): The subjective value of a gain or loss.
         Formula: 
           x^alpha             if x >= 0
           -lambda * (-x)^alpha if x < 0
        """
        if amount >= 0:
            return math.pow(amount, self.alpha)
        else:
            return -self.lambda_param * math.pow(abs(amount), self.alpha)

    def diagnose_psych_state(self, daily_pl: float, total_assets: float) -> dict:
        """
        Diagnoses the user's psychological state based on P/L and assets.
        Returns detailed state and recommended UI mode.
        """
        if total_assets == 0:
            return {"state": "neutral", "ui_mode": "Zero-Click", "pain_score": 0.0}

        # Calculate relative impact
        impact_ratio = daily_pl / total_assets
        
        # Calculate subjective pain (cached)
        subjective_pain = self.calculate_subjective_value(daily_pl)
        
        # Thresholds (Calibrated from Shimane Bank PoC)
        if impact_ratio < -0.05: # -5% drop
            return {
                "state": "panic",
                "ui_mode": "High-Friction", # Force Dialogue
                "pain_score": abs(subjective_pain),
                "reason": "Loss aversion trigger detected."
            }
        elif impact_ratio < -0.02:
            return {
                "state": "anxious",
                "ui_mode": "Medium-Friction", # Confirm with Empathy
                "pain_score": abs(subjective_pain),
                "reason": "Moderate volatility anxiety."
            }
        elif impact_ratio > 0.05:
            return {
                "state": "greed",
                "ui_mode": "Risk-Warning", # Warn about leverage
                "pain_score": 0.0,
                "reason": "Euphoria detected."
            }
            
        return {"state": "neutral", "ui_mode": "Zero-Click", "pain_score": 0.0}
