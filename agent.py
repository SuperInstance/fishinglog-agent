#!/usr/bin/env python3
"""
fishinglog-agent — AI-powered commercial fishing intelligence
Track catches, weather, tides, and market prices. Find patterns humans miss.
Built by a commercial fisherman.

Now uses domain-agent-base for PLATO integration, health checks, and reporting.
"""

import json, time, random
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from domain_agent_base import DomainAgent
except ImportError:
    # Fallback if domain-agent-base not installed
    class DomainAgent:
        domain = "base"
        plato_url = "http://147.224.38.131:8847"
        def __init__(self):
            self.tiles_submitted = []
            self.errors = []
            self.start_time = time.time()
        def submit_tile(self, question, answer, room=None):
            self.tiles_submitted.append({"q": question, "a": answer})
            return True
        def get_stats(self):
            return {"domain": self.domain, "tiles": len(self.tiles_submitted)}
        def run(self):
            raise NotImplementedError

@dataclass
class Catch:
    species: str
    weight_kg: float
    location: str
    timestamp: float
    conditions: Dict
    price_per_kg: Optional[float] = None

class FishingLogAgent(DomainAgent):
    """Fishing intelligence agent — now with DomainAgent base class."""
    
    domain = "fishing"
    version = "0.2.0"
    
    def __init__(self):
        super().__init__()
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
        
        # Submit to PLATO via base class
        self.submit_tile(
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
            if c.species not in best_conditions:
                best_conditions[c.species] = {"catches": 0, "total_weight": 0}
            best_conditions[c.species]["catches"] += 1
            best_conditions[c.species]["total_weight"] += c.weight_kg
        
        # Average price trend
        price_trend = []
        for c in self.catches:
            if c.price_per_kg:
                price_trend.append({"species": c.species, "price": c.price_per_kg, "time": c.timestamp})
        
        return {
            "total_catches": len(self.catches),
            "species_seen": list(self.species_seen),
            "species_frequency": species_count,
            "best_conditions": best_conditions,
            "price_trend": price_trend[-10:]  # Last 10
        }
    
    def predict_best_spot(self, species: str) -> Dict:
        """Predict best fishing spot for a species based on historical data."""
        matches = [c for c in self.catches if c.species == species]
        if not matches:
            return {"error": f"No data for {species}"}
        
        # Simple: return location with highest average weight
        location_scores = {}
        for c in matches:
            if c.location not in location_scores:
                location_scores[c.location] = {"total_weight": 0, "count": 0}
            location_scores[c.location]["total_weight"] += c.weight_kg
            location_scores[c.location]["count"] += 1
        
        best = max(location_scores.items(), key=lambda x: x[1]["total_weight"] / x[1]["count"])
        
        return {
            "species": species,
            "best_location": best[0],
            "avg_weight": round(best[1]["total_weight"] / best[1]["count"], 2),
            "confidence": min(best[1]["count"] / 10, 1.0)  # More catches = higher confidence
        }
    
    def run(self):
        """Main agent loop — log demo catches and submit insights."""
        print(f"FishingLogAgent v{self.version} starting...")
        
        # Log some demo catches
        self.log_catch("Tuna", 15.2, "GPS:42.3,-71.0", "sunny", "incoming", 18.5, 12.50)
        self.log_catch("Cod", 8.7, "GPS:42.1,-70.8", "cloudy", "slack", 16.0, 8.25)
        self.log_catch("Tuna", 22.1, "GPS:42.3,-71.0", "sunny", "incoming", 19.0, 14.00)
        
        # Submit pattern insights
        patterns = self.get_patterns()
        self.submit_tile(
            "What patterns emerge from fishing data?",
            json.dumps(patterns, indent=2, default=str)
        )
        
        # Submit prediction
        prediction = self.predict_best_spot("Tuna")
        self.submit_tile(
            "Where is the best spot for Tuna?",
            json.dumps(prediction, indent=2, default=str)
        )
        
        print(f"Run complete. {len(self.catches)} catches logged, {len(self.tiles_submitted)} tiles submitted")

def main():
    agent = FishingLogAgent()
    agent.run()
    print(f"\nStats: {json.dumps(agent.get_stats(), indent=2)}")
    print(f"\nHealth: {json.dumps(agent.health_check(), indent=2)}")

if __name__ == "__main__":
    main()
