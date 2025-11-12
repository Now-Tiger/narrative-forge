"""
Output Assembler
Assembles all generated components into final markdown document
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime
from utils.extractor import StoryElements
from schema.models import WorldSetting, MappedCharacter, TransformedPlotAct
from utils.validator import ConsistencyReport
from tabulate import tabulate


def format_character_table(
    mappings: List[MappedCharacter],
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> str:
    """
    Format character mappings as markdown table with optional title/subtitle.
    
    Args:
        mappings: List of MappedCharacter objects
        title: Optional section title (e.g. "## Character Mapping Table")
        subtitle: Optional short description or context
    
    Returns:
        Markdown formatted text containing title, subtitle, and table
    """

    # Prepare table data
    table_data = []
    for mapping in mappings:
        traits = ", ".join(mapping.core_traits[:3]) if mapping.core_traits else "-"
        table_data.append([
            mapping.original_name,
            mapping.new_name,
            mapping.new_role,
            traits,
            mapping.motivation
        ])

    headers = ["Original", "Reimagined", "New Role", "Core Traits", "Motivation"]

    # Generate markdown table using tabulate
    markdown_table = tabulate(table_data, headers=headers, tablefmt="github")

    # Add optional title and subtitle
    parts = []
    if title:
        parts.append(f"## {title.strip()}")
    if subtitle:
        parts.append(f"*{subtitle.strip()}*")
    parts.append("")  # blank line before table
    parts.append(markdown_table)
    parts.append("")  # trailing newline for markdown

    return "\n".join(parts)



def format_character_rationales(mappings: List[MappedCharacter]) -> str:
    """
    Format transformation rationales for each character
    
    Args:
        mappings: List of character mappings
    
    Returns:
        Formatted rationales section
    """
    output = ""
    for mapping in mappings:
        output += f"### {mapping.original_name} → {mapping.new_name}\n\n"
        output += f"**Role:** {mapping.new_role}\n\n"
        output += f"**Transformation Rationale:** {mapping.transformation_rationale}\n\n"
    
    return output


def format_plot_acts(acts: List[TransformedPlotAct]) -> str:
    """
    Format plot acts with events and themes
    
    Args:
        acts: List of transformed plot acts
    
    Returns:
        Formatted plot section
    """
    output = ""
    
    for act in acts:
        output += f"### Act {act.act_number}: {act.act_name}\n\n"
        output += f"**Emotional Arc:** {act.emotional_arc}\n\n"
        output += "**Key Events:**\n\n"
        
        for i, event in enumerate(act.key_events, 1):
            output += f"{i}. {event}\n\n"
        
        output += "**How Original Themes Manifest:**\n\n"
        output += f"{act.theme_manifestation}\n\n"
        output += "---\n\n"
    
    return output


def assemble_final_output(
    elements: StoryElements,
    world: WorldSetting,
    character_mappings: List[MappedCharacter],
    plot_acts: List[TransformedPlotAct],
    consistency_report: ConsistencyReport,
    target_world: str = "tech startup ecosystem"
) -> str:
    """
    Assemble complete reimagined story document
    
    Args:
        elements: Original story elements
        world: Generated world setting
        character_mappings: Character mappings
        plot_acts: Transformed plot acts
        consistency_report: Validation report
        target_world: Description of target world
    
    Returns:
        Complete markdown document
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Format source type and target world properly
    source_formatted = elements.source_type.replace('_', ' ').title()
    target_formatted = target_world.title()
    
    output = f"""# The Reimagined {elements.title}
## From {source_formatted} to {target_formatted}

*Generated on {timestamp}*

---

## Overview

This is a narrative transformation of **{elements.title}**, reimagining the timeless epic in a completely new context while preserving its emotional core, dramatic structure, and thematic depth.

**Original Setting:** {source_formatted}  
**New Setting:** {target_formatted}  
**Core Conflict:** {elements.core_conflict}

---

## World-Building

### World Overview

{world.overview}

### Setting Details

{world.setting_details}

### How Themes Translate

{world.theme_translation}

---

## Character Mapping

The characters from {elements.title} have been reimagined to fit naturally within the new world while preserving their essential traits and motivations.

{format_character_table(character_mappings)}

---

### Transformation Rationales

{format_character_rationales(character_mappings)}

---    
## Main Plot Reinterpretation

### Core Dramatic Question

**Original:** {elements.core_conflict}

**Reimagined:** In the {target_formatted}, this becomes: Can ethical technology and integrity prevail against exploitative practices driven by greed and ego?

### Plot Structure

{format_plot_acts(plot_acts)}

---

## Creative Rationale

### Why This Transformation Works

This reimagining succeeds because:

1. **Thematic Preservation:** The core themes of {', '.join(elements.core_themes[:3])} remain central to the narrative, translated authentically into the new context.

2. **Character Integrity:** Each character's fundamental motivations and relationships are preserved. The hero's journey, the partner's resilience, the antagonist's complexity - all remain intact while their expressions change.

3. **Structural Fidelity:** The three-act structure mirrors the original's dramatic progression: setup and loss, struggle and separation, confrontation and resolution.

4. **Cultural Resonance:** The new setting amplifies the story's relevance, making ancient wisdom accessible to modern audiences while honoring its origins.

### Emotional Depth in New Context

The transformation deepens emotional impact by:

- **Exile to Professional Displacement:** Modern audiences understand career upheaval and corporate politics
- **Kingdom to Company:** Power structures remain, contexts change
- **Dharma to Ethics:** Righteousness translates to integrity in modern professional life
- **Battle to Competition:** Conflict manifests differently but remains equally intense

The new setting doesn't diminish the original's power - it refracts it through a contemporary lens, making the eternal struggle between right and wrong immediately recognizable.

---

## Consistency Validation

{consistency_report.summary}

**Validation Results:**
- Total Checks Performed: {consistency_report.total_checks}
- Issues Found: {len(consistency_report.issues_found)}
- Status: {"PASSED" if consistency_report.passed else "NEEDS REVIEW"}

"""
    
    # Add issues if any
    if consistency_report.issues_found:
        output += "\n### Validation Issues\n\n"
        for issue in consistency_report.issues_found:
            severity_marker = {"critical": "[CRITICAL]", "warning": "[WARNING]", "info": "[INFO]"}.get(issue.severity, "")
            output += f"**{severity_marker}** ({issue.category}): {issue.description} - *{issue.location}*\n\n"
    
    output += f"""
---

## Metadata

**Source Story:** {elements.title}  
**Original Culture:** {elements.cultural_origin}  
**Target World:** {target_formatted}  
**Characters Mapped:** {len(character_mappings)}  
**Acts Transformed:** {len(plot_acts)}  
**Generation Date:** {timestamp}

---

*This transformation was created using an AI-powered narrative adaptation system that preserves thematic essence while reimagining context.*
"""
    
    return output


def save_output(content: str, filename: str = "reimagined_story.md") -> Path:
    """
    Save the assembled content to markdown file with proper UTF-8 encoding
    
    Args:
        content: Markdown content to save
        filename: Output filename
    
    Returns:
        Path to saved file
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    
    # Use UTF-8 encoding explicitly and handle potential encoding issues
    with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print(f"[Info] Output saved with UTF-8 encoding to: {output_path}")
    
    return output_path

