"""Tests for story generator."""

from unittest.mock import MagicMock

import pytest

from ba_analyser.generators.story_generator import StoryGenerator
from ba_analyser.models import CoverageReport, UserStory


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config.bedrock_temperature_analysis = 0.1
    client.config.bedrock_temperature_generation = 0.4
    return client


@pytest.fixture
def generator(mock_client):
    return StoryGenerator(mock_client)


def _mock_requirements() -> dict:
    return {
        "requirements": [
            {
                "id": "REQ-F001",
                "description": "Display book catalogue",
                "type": "functional",
                "section": "Section 4",
            },
            {
                "id": "REQ-F002",
                "description": "Search for books",
                "type": "functional",
                "section": "Section 4",
            },
        ]
    }


def _mock_personas() -> dict:
    return {
        "personas": [
            {
                "name": "Online Customer",
                "description": "A customer browsing and buying books",
                "primary_needs": ["Browse", "Search", "Buy"],
                "related_requirement_ids": ["REQ-F001", "REQ-F002"],
            },
        ]
    }


def _mock_stories() -> dict:
    return {
        "epics": [
            {"name": "Catalogue", "description": "Book browsing and search"},
        ],
        "stories": [
            {
                "id": "US-001",
                "epic": "Catalogue",
                "title": "Browse book catalogue",
                "persona": "Online Customer",
                "goal": "browse the book catalogue",
                "benefit": "discover books to purchase",
                "acceptance_criteria": [
                    "Books displayed with title, author, price",
                    "Pagination with 20 items per page",
                ],
                "priority": "Must",
                "estimate_complexity": "M",
                "dependencies": [],
                "source_requirement_ids": ["REQ-F001"],
            },
            {
                "id": "US-002",
                "epic": "Catalogue",
                "title": "Search for books",
                "persona": "Online Customer",
                "goal": "search for books by title or author",
                "benefit": "quickly find specific books",
                "acceptance_criteria": [
                    "Search by title, author, ISBN, keyword",
                    "Results within 1 second",
                ],
                "priority": "Must",
                "estimate_complexity": "M",
                "dependencies": ["US-001"],
                "source_requirement_ids": ["REQ-F002"],
            },
        ],
    }


class TestStoryGeneratorGenerate:
    def test_generate_calls_three_step_chain(self, generator, mock_client):
        """generate() should call Bedrock 3 times: extract, personas, generate."""
        mock_client.invoke_structured.side_effect = [
            _mock_requirements(),
            _mock_personas(),
            _mock_stories(),
        ]

        stories = generator.generate("Some requirements text")

        assert mock_client.invoke_structured.call_count == 3

    def test_generate_returns_user_stories(self, generator, mock_client):
        mock_client.invoke_structured.side_effect = [
            _mock_requirements(),
            _mock_personas(),
            _mock_stories(),
        ]

        stories = generator.generate("Some requirements text")

        assert len(stories) == 2
        assert all(isinstance(s, UserStory) for s in stories)
        assert stories[0].id == "US-001"
        assert stories[0].persona == "Online Customer"
        assert stories[0].priority == "Must"

    def test_generate_skips_invalid_stories(self, generator, mock_client):
        bad_stories = _mock_stories()
        bad_stories["stories"].append(
            {
                "id": "US-BAD",
                "epic": "Test",
                "title": "Bad",
                "persona": "User",
                "goal": "test",
                "benefit": "test",
                "acceptance_criteria": [],
                "priority": "InvalidPriority",  # Will fail validation
                "estimate_complexity": "M",
                "dependencies": [],
                "source_requirement_ids": [],
            }
        )
        mock_client.invoke_structured.side_effect = [
            _mock_requirements(),
            _mock_personas(),
            bad_stories,
        ]

        stories = generator.generate("Some text")

        # Should have 2 valid stories, bad one skipped
        assert len(stories) == 2


class TestStoryGeneratorCoverage:
    def test_validate_coverage(self, generator, mock_client):
        mock_client.invoke_structured.side_effect = [
            _mock_requirements(),  # extract call
            {
                "total_requirements": 2,
                "covered_requirements": 2,
                "coverage_percentage": 100.0,
                "uncovered_requirements": [],
                "over_covered_requirements": [],
            },
        ]

        stories = [
            UserStory(
                id="US-001",
                epic="Cat",
                title="Browse",
                persona="Customer",
                goal="browse",
                benefit="discover",
                acceptance_criteria=["AC1"],
                priority="Must",
                estimate_complexity="M",
                source_requirement_ids=["REQ-F001"],
            ),
        ]

        report = generator.validate_coverage("Req text", stories)

        assert isinstance(report, CoverageReport)
        assert report.coverage_percentage == 100.0
        assert report.uncovered_requirements == []

    def test_validate_coverage_with_gaps(self, generator, mock_client):
        mock_client.invoke_structured.side_effect = [
            _mock_requirements(),
            {
                "total_requirements": 2,
                "covered_requirements": 1,
                "coverage_percentage": 50.0,
                "uncovered_requirements": [
                    {
                        "requirement_id": "REQ-F002",
                        "description": "Search for books",
                        "suggestion": "Add a search story",
                    }
                ],
                "over_covered_requirements": [],
            },
        ]

        report = generator.validate_coverage("Req text", [])

        assert report.coverage_percentage == 50.0
        assert "REQ-F002" in report.uncovered_requirements


class TestStoryGeneratorRefine:
    def test_refine_story(self, generator, mock_client):
        original = UserStory(
            id="US-001",
            epic="Catalogue",
            title="Browse books",
            persona="Online Customer",
            goal="browse books",
            benefit="find books",
            acceptance_criteria=["Books are shown"],
            priority="Must",
            estimate_complexity="M",
            dependencies=[],
            source_requirement_ids=["REQ-F001"],
        )

        mock_client.invoke_structured.return_value = {
            "id": "US-001",
            "epic": "Catalogue",
            "title": "Browse book catalogue",
            "persona": "Online Customer",
            "goal": "browse the full book catalogue with details",
            "benefit": "discover books to purchase",
            "acceptance_criteria": [
                "Books displayed with cover, title, author, price",
                "Pagination with 20 items per page",
                "Detail page accessible on click",
            ],
            "priority": "Must",
            "estimate_complexity": "M",
            "dependencies": [],
            "source_requirement_ids": ["REQ-F001"],
        }

        refined = generator.refine_story(original, "Add more acceptance criteria")

        assert isinstance(refined, UserStory)
        assert len(refined.acceptance_criteria) == 3
        assert refined.goal != original.goal
