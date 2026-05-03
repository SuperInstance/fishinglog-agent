#!/usr/bin/env python3
"""
fishinglog-agent — AI-powered commercial fishing intelligence
Track catches, weather, tides, and market prices. Find patterns humans miss.
Built by a commercial fisherman.
"""

import json, time, random, urllib.request
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Catch:
    species: str
    weight_kg: float
    location: str
    timestamp: float
    conditions: Dict  # weather, tide, temp
    price_per_kg: Optional[float] = None

class FishingLogAgent:
    def __init__(self, agent_name: str = "fishinglog-agent", plato_url: str = "http://147.224.38.131:8847"):
        self.name = agent_name
        self.plato_url = plato_url.rstrip("/")
        self.catches: List[Catch] = []
        self.species_seen: set = set()
    
    def log_catch(self, species: str, weight_kg: float, location: str, 
                  weather: str = "unknown", tide: str = "unknown", temp_c: float = 0.0,
                  price_per_kg: Optional[float] = None):
        """Log a catch with all conditions."""
        catch = Catch(
            species=species,
            weight_kg=weight_kg,
            location=location,
            timestamp=time.time(),
            conditions={"weather": weather, "tide": tide, "temp_c": temp_c},
            price_per_kg=price_per_kg
        )
        self.catches.append(catch)
        self.species_seen.add(species)
        
        # Submit to PLATO
        self._submit_tile(
            question=f"What was caught at {location} under {weather} conditions?",
            answer=f"{species}: {weight_kg}kg at {temp_c}°C, tide={tide}"
        )
        return catch
    
    def get_patterns(self) -> Dict:
        """Find patterns across all logged catches."""
        if not self.catches:
            return {"error": "No catches logged yet"}
        
        # Species frequency
        species_count = {}
        for c in self.catches:
            species_count[c.species] = species_count.get(c.species, 0) + 1
        
        # Best conditions per species
        best_conditions = {}
        for c in self.catches:
            sp = c.species
            if sp not in best_conditions:
                best_conditions[sp] = {"catches": [], "total_kg": 0}
            best_conditions[sp]["catches"].append(c)
            best_conditions[sp]["total_kg"] += c.weight_kg
        
        # Location performance
        loc_perf = {}
        for c in self.catches:
            loc = c.location
            if loc not in loc_perf:
                loc_perf[loc] = {"catches": 0, "total_kg": 0}
            loc_perf[loc]["catches"] += 1
            loc_perf[loc]["total_kg"] += c.weight_kg
        
        return {
            "total_catches": len(self.catches),
            "species_diversity": len(self.species_seen),
            "species_frequency": species_count,
            "best_conditions": {sp: {"avg_kg": data["total_kg"]/len(data["catches"])} 
                                for sp, data in best_conditions.items()},
            "location_performance": loc_perf,
        }
    
    def predict_best_conditions(self, species: str) -> Dict:
        """Predict best weather/tide for a species based on history."""
        relevant = [c for c in self.catches if c.species == species]
        if len(relevant) < 3:
            return {"error": f"Need 3+ catches of {species} for prediction. Have {len(relevant)}."}
        
        # Simple heuristic: most common conditions in top 50% by weight
        relevant.sort(key=lambda c: c.weight_kg, reverse=True)
        top_half = relevant[:len(relevant)//2]
        
        weather_freq = {}
        tide_freq = {}
        for c in top_half:
            w = c.conditions.get("weather", "unknown")
            t = c.conditions.get("tide", "unknown")
            weather_freq[w] = weather_freq.get(w, 0) + 1
            tide_freq[t] = tide_freq.get(t, 0) + 1
        
        best_weather = max(weather_freq, key=weather_freq.get) if weather_freq else "unknown"
        best_tide = max(tide_freq, key=tide_freq.get) if tide_freq else "unknown"
        
        return {
            "species": species,
            "recommend_weather": best_weather,
            "recommend_tide": best_tide,
            "confidence": len(top_half) / len(relevant),
            "avg_weight_top": sum(c.weight_kg for c in top_half) / len(top_half)
        }
    
    def _submit_tile(self, question: str, answer: str):
        """Submit a tile to PLATO gate."""
        payload = json.dumps({
            "question": question,
            "answer": answer,
            "agent": self.name,
            "room": "fishinglog"
        }).encode()
        try:
            req = urllib.request.Request(f"{self.plato_url}/submit", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                pass
        except Exception:
            pass  # PLATO optional

def demo():
    agent = FishingLogAgent()
    
    # Log some catches
    agent.log_catch("Salmon", 12.5, "Point A", "cloudy", "incoming", 14.2, 8.50)
    agent.log_catch("Tuna", 45.0, "Point B", "sunny", "slack", 22.0, 15.00)
    agent.log_catch("Salmon", 18.3, "Point A", "cloudy", "incoming", 13.8, 8.50)
    agent.log_catch("Tuna", 38.0, "Point B", "sunny", "slack", 21.5, 15.00)
    agent.log_catch("Cod", 5.2, "Point C", "rainy", "outgoing", 11.0, 6.00)
    agent.log_catch("Salmon", 15.0, "Point A", "cloudy", "incoming", 14.0, 8.50)
    
    print("=== Fishing Log Patterns ===")
    patterns = agent.get_patterns()
    print(f"Total catches: {patterns['total_catches']}")
    print(f"Species seen: {patterns['species_diversity']}")
    print(f"Frequency: {patterns['species_frequency']}")
    print(f"\nLocation performance: {patterns['location_performance']}")
    
    print("\n=== Prediction: Best conditions for Salmon ===")
    pred = agent.predict_best_conditions("Salmon")
    print(f"Recommend: {pred.get('recommend_weather')} weather, {pred.get('recommend_tide')} tide")
    print(f"Confidence: {pred.get('confidence', 0):.1%}")

if __name__ == "__main__":
    demo()
