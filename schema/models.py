#!/usr/bin/env python3
# -*- coding: utf-8 -*_
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class WorldSetting(BaseModel):
    """Structured representation of the reimagined world"""

    overview: str = Field(description="High-level world description")
    setting_details: str = Field(description="Specific details about locations, time, technology")
    theme_translation: str = Field(description="How original themes manifest in new world")
    full_description: str = Field(description="Complete world-building text")


class Character(BaseModel):
    """Represents a character with traits and motivation"""

    name: str
    role: str
    traits: List[str]
    motivation: str


class PlotAct(BaseModel):
    """Represents a story act with events and emotional arc"""

    name: str
    key_events: List[str]
    emotional_arc: str


class TransformedPlotAct(BaseModel):
    """Represents a transformed story act in new world"""

    act_number: int
    act_name: str
    emotional_arc: str
    key_events: List[str]
    theme_manifestation: str


class StoryElements(BaseModel):
    """Complete structured representation of source story"""

    title: str
    source_type: str
    cultural_origin: str = Field(default="Unknown", description="Cultural origin of the story")
    core_themes: List[str] = Field(description="Central themes of the story")
    main_characters: List[Character]
    plot_structure: Dict[str, PlotAct]
    core_conflict: str
    resolution_theme: str


class OriginalCharacter(BaseModel):

    name: str
    role: Optional[str] = Field(None, description="Short role tag or archetype (e.g., 'protagonist, prince')")
    motivation: Optional[str] = Field(None, description="Short motivation or goal")


class MappedCharacter(BaseModel):
    """Represents a character mapped to new world"""

    original_name: str
    new_name: str
    new_role: str
    core_traits: List[str]
    motivation: str
    transformation_rationale: str


class MappingResult(BaseModel):

    source: str
    target_world: str
    mappings: List[MappedCharacter]


class ConsistencyIssue(BaseModel):
    """Represents a consistency issue found during validation"""
    severity: str = Field(description="critical, warning, or info")
    category: str = Field(description="character, theme, world, or narrative")
    description: str
    location: str = Field(description="Where the issue was found")


class ConsistencyReport(BaseModel):
    """Complete consistency validation report"""
    total_checks: int
    issues_found: List[ConsistencyIssue]
    passed: bool
    summary: str

