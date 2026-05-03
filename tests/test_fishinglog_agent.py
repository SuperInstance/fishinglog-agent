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


class TestFishingLogAgent:
    """Tests for FishingLogAgent."""
    
    def test_agent_init(self):
        """Test agent initialization."""
        agent = FishingLogAgent()
        
        assert agent.room == "fishinglog-ai"
        assert agent.plato_url == "http://localhost:8847"
    
    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        dist = FishingLogAgent._haversine(41.5, -71.3, 41.5, -71.3)
        assert dist == 0.0


class TestMockSonar:
    """Tests for mock sonar data generation."""
    
    def test_mock_sonar_reading(self):
        """Test mock sonar reading generation."""
        sonar = mock_sonar_reading()
        
        assert "depth_meters" in sonar
        assert 20 <= sonar["depth_meters"] <= 100