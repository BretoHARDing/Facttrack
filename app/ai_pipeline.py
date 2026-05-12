class ContradictionEngine:
    def analyze(self, claim1: str, claim2: str) -> dict:
        # Grounded logic: Calculate semantic overlap
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        score = overlap / total if total > 0 else 0
        
        # Grounded logic: Detect contradictory negations
        negations = {"not", "never", "no", "false", "didn't", "don't", "cannot", "can't"}
        has_neg1 = bool(words1.intersection(negations))
        has_neg2 = bool(words2.intersection(negations))
        
        contradiction_probability = 0.1
        if score > 0.3 and has_neg1 != has_neg2:
            contradiction_probability = 0.88
            
        return {
            "contradiction_probability": contradiction_probability,
            "overlap_score": score,
            "conclusion": "High likelihood of contradiction" if contradiction_probability > 0.5 else "No strong contradiction detected"
        }
