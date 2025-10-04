"""PostgreSQL-specific database functionality tests."""

from sqlalchemy import text


class TestPostgreSQLFeatures:
    """Test PostgreSQL-specific features like TSRANGE and advanced queries."""

    def test_postgresql_connection(self, db_session):
        """Test basic PostgreSQL connectivity."""
        result = db_session.execute(text("SELECT version()")).fetchone()
        assert "PostgreSQL" in result[0]
        print("✅ PostgreSQL connection confirmed")

    def test_tsrange_basic_functionality(self, db_session):
        """Test basic TSRANGE operations."""
        result = db_session.execute(text("""
            SELECT
                '[2024-01-01 09:00:00,2024-01-01 17:00:00)'::tsrange as range_value,
                lower('[2024-01-01 09:00:00,2024-01-01 17:00:00)'::tsrange) as start_time,
                upper('[2024-01-01 09:00:00,2024-01-01 17:00:00)'::tsrange) as end_time
        """)).fetchone()

        assert result.range_value is not None
        assert "2024-01-01 09:00:00" in str(result.start_time)
        assert "2024-01-01 17:00:00" in str(result.end_time)
        print("✅ TSRANGE basic operations working")

    def test_tsrange_overlap_detection(self, db_session):
        """Test TSRANGE overlap detection."""
        result = db_session.execute(text("""
            SELECT
                '[2024-01-01 09:00:00,2024-01-01 12:00:00)'::tsrange &&
                '[2024-01-01 10:00:00,2024-01-01 14:00:00)'::tsrange as has_overlap,
                '[2024-01-01 09:00:00,2024-01-01 10:00:00)'::tsrange &&
                '[2024-01-01 11:00:00,2024-01-01 14:00:00)'::tsrange as no_overlap
        """)).fetchone()

        assert result.has_overlap is True
        assert result.no_overlap is False
        print("✅ TSRANGE overlap detection working")

    def test_uuid_generation(self, db_session):
        """Test PostgreSQL UUID generation."""
        result = db_session.execute(text("""
            SELECT gen_random_uuid() as new_uuid
        """)).fetchone()

        assert result.new_uuid is not None
        assert len(str(result.new_uuid)) == 36  # Standard UUID length with hyphens
        print("✅ PostgreSQL UUID generation working")

    def test_json_operations(self, db_session):
        """Test PostgreSQL JSON operations."""
        result = db_session.execute(text("""
            SELECT
                '{"name": "John", "age": 25}'::jsonb as json_data,
                '{"name": "John", "age": 25}'::jsonb ->> 'name' as name_value
        """)).fetchone()

        assert result.json_data is not None
        assert result.name_value == "John"
        print("✅ PostgreSQL JSON operations working")

    def test_array_operations(self, db_session):
        """Test PostgreSQL array operations."""
        result = db_session.execute(text("""
            SELECT
                ARRAY['CS101', 'MATH201'] as course_array,
                'CS101' = ANY(ARRAY['CS101', 'MATH201']) as contains_cs101
        """)).fetchone()

        assert result.course_array == ['CS101', 'MATH201']
        assert result.contains_cs101 is True
        print("✅ PostgreSQL array operations working")
