"""
PLATO Fishing Log Agent - Captain's Mate
========================================
A git-agent pattern for fishing logs. Every fishing session is a committed tile to PLATO.

Usage:
    from fishinglog_agent import FishingLogAgent
    
    agent = FishingLogAgent()
    agent.log_session(latitude=41.5, longitude=-71.3, depth_meters=45, species="tuna", catch_count=12)
    results = agent.query(species="tuna", days_back=7)
"""

import requests
import json
import hashlib
import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

__version__ = "0.1.0"

# Default PLATO endpoint
DEFAULT_PLATO_URL = "http://localhost:8847"
FISHINGLOG_ROOM = "fishinglog-ai"


@dataclass
class FishingTile:
    """A fishing session tile committed to PLATO."""
    session_id: str
    timestamp: str
    latitude: float
    longitude: float
    depth_meters: float
    species: str
    catch_count: int
    notes: str = ""
    agent: str = "captains-mate"
    
    def to_plato_tile(self) -> Dict[str, Any]:
        """Convert to PLATO tile format."""
        return {
            "domain": "fishinglog-ai",
            "agent": self.agent,
            "type": "fishing_session",
            "question": f"Where were {self.species} on {self.timestamp}?",
            "answer": f"Caught {self.catch_count} {self.species} at {self.latitude}N, {self.longitude}W, depth {self.depth_meters}m. Notes: {self.notes}",
            "confidence": 0.9,
            "content": asdict(self)
        }
    
    @property
    def tile_hash(self) -> str:
        """Generate a deterministic hash for this tile."""
        content = f"{self.session_id}{self.timestamp}{self.species}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class FishingLogAgent:
    """
    Captain's Mate for fishinglog.ai.
    
    Receives sonar depth data → writes to PLATO as functional tiles.
    Answers questions like "where were tuna last Tuesday?" by querying PLATO tiles.
    """
    
    def __init__(
        self,
        plato_url: str = DEFAULT_PLATO_URL,
        room: str = FISHINGLOG_ROOM,
        agent_name: str = "captains-mate"
    ):
        self.plato_url = plato_url.rstrip("/")
        self.room = room
        self.agent_name = agent_name
        
    def _get_room_url(self) -> str:
        """Get the room API URL."""
        return f"{self.plato_url}/room/{self.room}"
    
    def _get_tiles_url(self) -> str:
        """Get the tiles API URL."""
        return f"{self.plato_url}/room/{self.room}/tiles"
    
    def room_exists(self) -> bool:
        """Check if the fishinglog-ai room exists."""
        try:
            resp = requests.get(self._get_room_url(), timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
    
    def ensure_room(self) -> bool:
        """Ensure the fishinglog-ai room exists, create if not."""
        if self.room_exists():
            return True
        
        # Try to create via first tile (rooms are created on first write in some PLATO implementations)
        try:
            test_tile = FishingTile(
                session_id="init",
                timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                latitude=0.0,
                longitude=0.0,
                depth_meters=0.0,
                species="init",
                catch_count=0,
                notes="Room initialization"
            )
            resp = requests.post(
                self._get_tiles_url(),
                json=test_tile.to_plato_tile(),
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            return resp.status_code in (200, 201)
        except requests.RequestException:
            return False
    
    def log_session(
        self,
        latitude: float,
        longitude: float,
        depth_meters: float,
        species: str,
        catch_count: int,
        session_id: Optional[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Log a fishing session to PLATO (like a git commit).
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude (negative for west)
            depth_meters: Sonar depth reading in meters
            species: Fish species caught
            catch_count: Number of fish caught
            session_id: Optional session identifier (auto-generated if not provided)
            notes: Optional notes about the session
            
        Returns:
            Dict with the committed tile info
        """
        if not session_id:
            ts = datetime.datetime.utcnow().isoformat()
            session_id = f"sess-{hashlib.md5(ts.encode()).hexdigest()[:8]}"
        
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        tile = FishingTile(
            session_id=session_id,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            depth_meters=depth_meters,
            species=species,
            catch_count=catch_count,
            notes=notes,
            agent=self.agent_name
        )
        
        # Write to PLATO
        try:
            resp = requests.post(
                self._get_tiles_url(),
                json=tile.to_plato_tile(),
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if resp.status_code in (200, 201):
                return {
                    "success": True,
                    "session_id": session_id,
                    "tile_hash": tile.tile_hash,
                    "timestamp": timestamp
                }
            else:
                return {
                    "success": False,
                    "error": f"PLATO returned {resp.status_code}: {resp.text[:200]}",
                    "tile": tile.to_plato_tile()  # Return tile for manual logging
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "tile": tile.to_plato_tile()
            }
    
    def query(
        self,
        species: Optional[str] = None,
        days_back: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 10.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query past fishing sessions from PLATO.
        
        Args:
            species: Filter by fish species (e.g., "tuna", "mahi-mahi")
            days_back: Only look at sessions from the last N days
            latitude: Filter by proximity to this latitude
            longitude: Filter by proximity to this longitude
            radius_km: Search radius in km when using lat/lon
            limit: Maximum number of results
            
        Returns:
            List of matching fishing tiles
        """
        try:
            resp = requests.get(
                self._get_tiles_url(),
                timeout=10
            )
            
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            tiles = data.get("tiles", []) if isinstance(data, dict) else data
            
            results = []
            cutoff_time = None
            if days_back:
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
                cutoff_time = cutoff.timestamp()
            
            for tile in tiles:
                content = tile.get("content", {})
                if not content:
                    continue
                
                # Filter by species
                if species and species.lower() not in content.get("species", "").lower():
                    continue
                
                # Filter by time
                if cutoff_time:
                    try:
                        tile_time = datetime.datetime.fromisoformat(
                            content.get("timestamp", "").replace("Z", "")
                        ).timestamp()
                        if tile_time < cutoff_time:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                # Filter by location
                if latitude is not None and longitude is not None:
                    tile_lat = content.get("latitude", 0)
                    tile_lon = content.get("longitude", 0)
                    dist = self._haversine(latitude, longitude, tile_lat, tile_lon)
                    if dist > radius_km:
                        continue
                
                results.append(tile)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except requests.RequestException:
            return []
    
    def query_natural_language(self, question: str) -> str:
        """
        Answer a natural language question about fishing.
        
        Args:
            question: Question like "where were tuna last Tuesday?"
            
        Returns:
            Natural language answer
        """
        # Parse simple questions
        question_lower = question.lower()
        
        # Extract species
        species = None
        for fish in ["tuna", "mahi-mahi", "marlin", "swordfish", "bass", "salmon", "cod", "halibut"]:
            if fish in question_lower:
                species = fish
                break
        
        # Extract time range
        days_back = 7
        if "yesterday" in question_lower:
            days_back = 1
        elif "last week" in question_lower:
            days_back = 7
        elif "last month" in question_lower:
            days_back = 30
        elif "tuesday" in question_lower:
            # Rough approximation - would need proper date parsing
            days_back = 7
        elif "wednesday" in question_lower or "thursday" in question_lower:
            days_back = 7
        
        # Query PLATO
        tiles = self.query(species=species, days_back=days_back, limit=5)
        
        if not tiles:
            return f"No {species or 'fishing'} records found in the last {days_back} days."
        
        # Summarize results
        total_catch = sum(t.get("content", {}).get("catch_count", 0) for t in tiles)
        locations = []
        for t in tiles[:3]:
            c = t.get("content", {})
            loc = f"{c.get('latitude', '?')}N, {c.get('longitude', '?')}W at {c.get('depth_meters', '?')}m"
            locations.append(loc)
        
        species_str = species or "fish"
        loc_str = "; ".join(locations)
        
        return f"Found {len(tiles)} {species_str} sessions with {total_catch} total catch. Locations: {loc_str}"
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km (approximate)."""
        # Very rough approximation for small distances
        lat_diff = abs(lat1 - lat2) * 111  # ~111km per degree latitude
        lon_diff = abs(lon1 - lon2) * 85   # ~85km per degree longitude at mid-latitudes
        return (lat_diff**2 + lon_diff**2)**0.5


def mock_sonar_reading() -> Dict[str, Any]:
    """Generate mock sonar data for testing."""
    import random
    return {
        "depth_meters": random.uniform(20, 100),
        "temperature_celsius": random.uniform(10, 20),
        "salinity_ppt": random.uniform(32, 36),
        "bottom_type": random.choice(["sand", "rock", "mud", "reef"])
    }


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PLATO Fishing Log Agent - Captain's Mate")
    parser.add_argument("action", choices=["log", "query", "mock"], help="Action to perform")
    parser.add_argument("--species", "-s", help="Fish species")
    parser.add_argument("--lat", "-l", type=float, help="Latitude")
    parser.add_argument("--lon", "-o", type=float, help="Longitude")
    parser.add_argument("--depth", "-d", type=float, help="Depth in meters")
    parser.add_argument("--count", "-c", type=int, default=0, help="Catch count")
    parser.add_argument("--notes", "-n", default="", help="Session notes")
    parser.add_argument("--days", type=int, default=7, help="Days back for queries")
    parser.add_argument("--plato-url", default=DEFAULT_PLATO_URL, help="PLATO server URL")
    
    args = parser.parse_args()
    
    agent = FishingLogAgent(plato_url=args.plato_url)
    
    if args.action == "log":
        if not all([args.lat, args.lon, args.depth, args.species]):
            print("Error: --species, --lat, --lon, --depth required for log")
            exit(1)
        
        result = agent.log_session(
            latitude=args.lat,
            longitude=args.lon,
            depth_meters=args.depth,
            species=args.species,
            catch_count=args.count,
            notes=args.notes
        )
        print(json.dumps(result, indent=2))
        
    elif args.action == "query":
        if args.species:
            results = agent.query(species=args.species, days_back=args.days)
        else:
            results = agent.query(days_back=args.days)
        print(json.dumps(results, indent=2))
        
    elif args.action == "mock":
        # Generate mock sonar and log it
        sonar = mock_sonar_reading()
        print(f"Mock sonar: {json.dumps(sonar, indent=2)}")
        
        if args.species and args.lat and args.lon:
            result = agent.log_session(
                latitude=args.lat,
                longitude=args.lon,
                depth_meters=sonar["depth_meters"],
                species=args.species,
                catch_count=args.count,
                notes=f"Mock session. Bottom: {sonar['bottom_type']}"
            )
            print(f"Logged: {json.dumps(result, indent=2)}")