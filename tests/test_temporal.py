"""Tests for Week 8 temporal features - TTL, decay, as_of queries."""

import math
from datetime import datetime, timedelta

import pytest

from remembra.services.memory import MemoryService, parse_ttl


class TestParseTTL:
    """Test TTL string parsing."""
    
    def test_parse_days(self):
        """Test parsing day-based TTL."""
        result = parse_ttl("30d")
        assert result == timedelta(days=30)
        
        result = parse_ttl("1d")
        assert result == timedelta(days=1)
        
        result = parse_ttl("365d")
        assert result == timedelta(days=365)
    
    def test_parse_weeks(self):
        """Test parsing week-based TTL."""
        result = parse_ttl("2w")
        assert result == timedelta(weeks=2)
        
        result = parse_ttl("1w")
        assert result == timedelta(weeks=1)
    
    def test_parse_months(self):
        """Test parsing month-based TTL (30 days per month)."""
        result = parse_ttl("1m")
        assert result == timedelta(days=30)
        
        result = parse_ttl("6m")
        assert result == timedelta(days=180)
    
    def test_parse_years(self):
        """Test parsing year-based TTL (365 days per year)."""
        result = parse_ttl("1y")
        assert result == timedelta(days=365)
        
        result = parse_ttl("2y")
        assert result == timedelta(days=730)
    
    def test_parse_none(self):
        """Test None input returns None."""
        assert parse_ttl(None) is None
        assert parse_ttl("") is None
        assert parse_ttl("   ") is None
    
    def test_parse_invalid(self):
        """Test invalid formats return None."""
        assert parse_ttl("invalid") is None
        assert parse_ttl("30x") is None
        assert parse_ttl("abc") is None
        assert parse_ttl("30") is None  # No unit
    
    def test_case_insensitive(self):
        """Test TTL parsing is case-insensitive."""
        assert parse_ttl("30D") == timedelta(days=30)
        assert parse_ttl("2W") == timedelta(weeks=2)
        assert parse_ttl("1M") == timedelta(days=30)
        assert parse_ttl("1Y") == timedelta(days=365)


class TestDecayScore:
    """Test memory decay score calculation."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a minimal MemoryService for testing decay calculation."""
        # We only need the calculate_decay_score method, which doesn't need initialization
        service = object.__new__(MemoryService)
        return service
    
    def test_fresh_memory_high_score(self, mock_service):
        """Fresh memories should have high decay scores (~1.0)."""
        now = datetime.utcnow()
        score = mock_service.calculate_decay_score(
            created_at=now,
            last_accessed=None,
            access_count=0,
            half_life_days=30.0,
        )
        
        # Fresh memory should be very close to 1.0
        assert score > 0.99
    
    def test_half_life_decay(self, mock_service):
        """Memory at half-life should have ~0.5 score."""
        now = datetime.utcnow()
        created = now - timedelta(days=30)  # Exactly half-life
        
        score = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=None,
            access_count=0,
            half_life_days=30.0,
        )
        
        # Should be close to 0.5 (exponential decay)
        assert 0.48 < score < 0.52
    
    def test_old_memory_low_score(self, mock_service):
        """Very old memories should have low decay scores."""
        now = datetime.utcnow()
        created = now - timedelta(days=365)  # 1 year old
        
        score = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=None,
            access_count=0,
            half_life_days=30.0,
        )
        
        # 365/30 = ~12 half-lives, should be very small
        assert score < 0.001
    
    def test_access_boost(self, mock_service):
        """Accessed memories should have higher scores."""
        now = datetime.utcnow()
        created = now - timedelta(days=30)
        
        # Without access
        score_no_access = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=None,
            access_count=0,
            half_life_days=30.0,
        )
        
        # With access
        score_with_access = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=None,
            access_count=10,
            half_life_days=30.0,
        )
        
        assert score_with_access > score_no_access
    
    def test_recency_boost(self, mock_service):
        """Recently accessed memories should have higher scores."""
        now = datetime.utcnow()
        created = now - timedelta(days=60)
        
        # Not recently accessed
        score_old_access = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=now - timedelta(days=30),
            access_count=5,
            half_life_days=30.0,
        )
        
        # Recently accessed
        score_recent_access = mock_service.calculate_decay_score(
            created_at=created,
            last_accessed=now - timedelta(hours=1),
            access_count=5,
            half_life_days=30.0,
        )
        
        assert score_recent_access > score_old_access


class TestChangelogParser:
    """Test changelog parsing."""
    
    def test_parse_keep_a_changelog_format(self):
        """Test parsing Keep a Changelog format."""
        from remembra.ingestion.changelog import ChangelogParser
        
        content = """# Changelog

## [1.2.0] - 2024-02-01

### Added
- Feature A
- Feature B

### Fixed
- Bug fix 1

## [1.1.0] - 2024-01-15

### Added
- Feature C
"""
        parser = ChangelogParser()
        releases = parser.parse(content)
        
        assert len(releases) == 2
        
        assert releases[0].version == "1.2.0"
        assert releases[0].date == datetime(2024, 2, 1)
        assert "Added" in releases[0].sections
        assert len(releases[0].sections["Added"]) == 2
        assert "Fixed" in releases[0].sections
        
        assert releases[1].version == "1.1.0"
        assert releases[1].date == datetime(2024, 1, 15)
    
    def test_parse_unreleased(self):
        """Test parsing [Unreleased] section."""
        from remembra.ingestion.changelog import ChangelogParser
        
        content = """# Changelog

## [Unreleased]

### Added
- WIP feature

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        parser = ChangelogParser()
        releases = parser.parse(content)
        
        assert len(releases) == 2
        assert releases[0].version == "Unreleased"
        assert releases[0].date is None
    
    def test_parse_no_date(self):
        """Test parsing version without date."""
        from remembra.ingestion.changelog import ChangelogParser
        
        content = """
## [2.0.0]

### Changed
- Breaking change
"""
        parser = ChangelogParser()
        releases = parser.parse(content)
        
        assert len(releases) == 1
        assert releases[0].version == "2.0.0"
        assert releases[0].date is None
    
    def test_to_memory_content(self):
        """Test converting release to memory content."""
        from remembra.ingestion.changelog import ChangelogRelease
        
        release = ChangelogRelease(
            version="1.0.0",
            date=datetime(2024, 1, 15),
            sections={
                "Added": ["Feature X", "Feature Y"],
                "Fixed": ["Bug Z"],
            },
        )
        
        content = release.to_memory_content()
        
        assert "Version 1.0.0" in content
        assert "2024-01-15" in content
        assert "Feature X" in content
        assert "Bug Z" in content


class TestDatabaseTemporal:
    """Test database temporal operations."""
    
    @pytest.fixture
    async def db(self, tmp_path):
        """Create a temporary database."""
        from remembra.storage.database import Database
        
        db_path = str(tmp_path / "test.db")
        db = Database(db_path)
        await db.connect()
        await db.init_schema()
        yield db
        await db.close()
    
    @pytest.mark.asyncio
    async def test_get_expired_memories(self, db):
        """Test getting expired memories."""
        now = datetime.utcnow()
        
        # Insert an expired memory
        await db.save_memory_metadata(
            memory_id="expired-1",
            user_id="user1",
            project_id="default",
            content="Old content",
            extracted_facts=["Old content"],
            metadata={},
            created_at=now - timedelta(days=60),
            expires_at=now - timedelta(days=1),  # Expired yesterday
        )
        
        # Insert a non-expired memory
        await db.save_memory_metadata(
            memory_id="valid-1",
            user_id="user1",
            project_id="default",
            content="Valid content",
            extracted_facts=["Valid content"],
            metadata={},
            created_at=now - timedelta(days=30),
            expires_at=now + timedelta(days=30),  # Expires in 30 days
        )
        
        expired = await db.get_expired_memories(user_id="user1")
        
        assert len(expired) == 1
        assert expired[0] == "expired-1"
    
    @pytest.mark.asyncio
    async def test_get_memories_as_of(self, db):
        """Test historical query (as_of)."""
        now = datetime.utcnow()
        
        # Memory created 30 days ago
        await db.save_memory_metadata(
            memory_id="old-mem",
            user_id="user1",
            project_id="default",
            content="Old memory",
            extracted_facts=["Old memory"],
            metadata={},
            created_at=now - timedelta(days=30),
        )
        
        # Memory created today
        await db.save_memory_metadata(
            memory_id="new-mem",
            user_id="user1",
            project_id="default",
            content="New memory",
            extracted_facts=["New memory"],
            metadata={},
            created_at=now,
        )
        
        # Query as of 15 days ago - should only see old memory
        historical = await db.get_memories_as_of(
            user_id="user1",
            project_id="default",
            as_of=now - timedelta(days=15),
        )
        
        assert len(historical) == 1
        assert historical[0]["id"] == "old-mem"
        
        # Query as of now - should see both
        current = await db.get_memories_as_of(
            user_id="user1",
            project_id="default",
            as_of=now + timedelta(hours=1),
        )
        
        assert len(current) == 2
    
    @pytest.mark.asyncio
    async def test_migrate_memory_relationships(self, db):
        """Test relationship migration during UPDATE consolidation."""
        now = datetime.utcnow()
        
        # Create entities
        from remembra.models.memory import Entity, Relationship
        
        entity = Entity(
            id="entity-1",
            canonical_name="Test Entity",
            type="person",
        )
        await db.save_entity(entity, "user1", "default")
        
        # Create old memory with link
        await db.save_memory_metadata(
            memory_id="old-mem",
            user_id="user1",
            project_id="default",
            content="Old content",
            extracted_facts=["Old content"],
            metadata={},
            created_at=now - timedelta(days=1),
        )
        await db.link_memory_to_entity("old-mem", "entity-1")
        
        # Create new memory
        await db.save_memory_metadata(
            memory_id="new-mem",
            user_id="user1",
            project_id="default",
            content="New content",
            extracted_facts=["New content"],
            metadata={},
            created_at=now,
        )
        
        # Migrate relationships
        await db.migrate_memory_relationships("old-mem", "new-mem")
        
        # Check new memory has the entity link
        new_entities = await db.get_memory_entities("new-mem")
        assert len(new_entities) == 1
        assert new_entities[0].id == "entity-1"
