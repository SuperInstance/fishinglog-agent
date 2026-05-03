"""Tests for PLATO Fishing Log Agent."""

import pytest
from fishinglog_agent import FishingLogAgent, FishingTile, mock_sonar_reading


class TestFishingTile:
    """Tests for FishingTile dataclass."""
    
    def test_tile_creation(self):
        """Test creating a fishing tile."""
        tile = FishingTile(
            session_id="test-001",
            timestamp="2026-05-03T10:00:00Z",
            latitude=41.5,
            longitude=-71.3,
            depth_meters=45.0,
            species="tuna",
            catch_count=12,
            notes="Test session"
        )
        
        assert tile.session_id == "test-001"
        assert tile.species == "tuna"
        assert tile.catch_count == 12
    
    def test_tile_to_plato_tile(self):
        """Test converting to PLATO tile format."""
        tile = FishingTile(
            session_id="test-001",
            timestamp="2026-05-03T10:00:00Z",
            latitude=41.5,
            longitude=-71.3,
            depth_meters=45.0,
            species="tuna",
            catch_count=12
        )
        
        plato_tile = tile.to_plato_tile()
        
        assert plato_tile["domain"] == "fishinglog-ai"
        assert plato_tile["type"] == "fishing_session"
        assert plato_tile["content"]["species"] == "tuna"
        assert plato_tile["content"]["catch_count"] == 12
    
    def test_tile_hash(self):
        """Test tile hash generation."""
        tile = FishingTile(
            session_id="test-001",
            timestamp="2026-05-03T10:00:00Z",
            latitude=41.5,
            longitude=-71.3,
            depth_meters=45.0,
            species="tuna",
            catch_count=12
        )
        
        assert len(tile.tile_hash) == 12
        assert tile.tile_hash == tile.tile_hash  # Deterministic


class TestFishingLogAgent:
    """Tests for FishingLogAgent."""
    
    def test_agent_init(self):
        """Test agent initialization."""
        agent = FishingLogAgent()
        
        assert agent.room == "fishinglog-ai"
        assert agent.plato_url == "http://localhost:8847"
    
    def test_agent_custom_init(self):
        """Test agent with custom settings."""
        agent = FishingLogAgent(
            plato_url="http://custom:8847",
            room="custom-room",
            agent_name="test-agent"
        )
        
        assert agent.plato_url == "http://custom:8847"
        assert agent.room == "custom-room"
        assert agent.agent_name == "test-agent"
    
    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        # Same point
        dist = FishingLogAgent._haversine(41.5, -71.3, 41.5, -71.3)
        assert dist == 0.0
        
        # Known distance (roughly 1 degree latitude = 111km)
        dist = FishingLogAgent._haversine(41.5, -71.3, 42.5, -71.3)
        assert 109 < dist < 113


class TestMockSonar:
    """Tests for mock sonar data generation."""
    
    def test_mock_sonar_reading(self):
        """Test mock sonar reading generation."""
        sonar = mock_sonar_reading()
        
        assert "depth_meters" in sonar
        assert "temperature_celsius" in sonar
        assert 20 <= sonar["depth_meters"] <= 100
        assert 10 <= sonar["temperature_celsius"] <= 20


class TestNaturalLanguageQuery:
    """Tests for natural language query parsing."""
    
    def test_parse_tuna_query(self):
        """Test parsing 'where were tuna' query."""
        agent = FishingLogAgent()
        agent.query = lambda **kwargs: []  # Mock
        
        answer = agent.query_natural_language("where were tuna last Tuesday?")
        
        assert "tuna" in answer.lower()
    
    def test_no_results(self):
        """Test query with no results."""
        agent = FishingLogAgent()
        agent.query = lambda **kwargs: []
        
        answer = agent.query_natural_language("where were unicorns?")
        
        assert "no" in answer.lower() or "not found" in answer.lower()