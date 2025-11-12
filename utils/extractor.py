#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story Element Extractor
Extracts and structures core narrative elements from source material
"""
import json
from pathlib import Path
from schema.models import StoryElements, PlotAct, Character


def load_story_metadata(story_name: str = "ramayana") -> dict:
    """
    Load story metadata from JSON file
    
    Args:
        story_name: Name of the story (matches filename)
    
    Returns:
        Dictionary containing story metadata
    """
    data_path = Path("data") / f"{story_name}_metadata.json"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Story metadata not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_story_elements(story_name: str = "ramayana") -> StoryElements:
    """
    Extract and structure story elements from metadata
    
    Args:
        story_name: Name of the source story
    
    Returns:
        StoryElements object with all extracted components
    """
    # Load raw metadata
    raw_data = load_story_metadata(story_name)
    
    # Parse characters
    characters = [
        Character(
            name=char["name"],
            role=char["role"],
            traits=char["traits"],
            motivation=char["motivation"]
        )
        for char in raw_data["main_characters"]
    ]
    
    # Parse plot structure (from metadata format)
    plot_structure = {
        act_key: PlotAct(
            name=act_data["name"],
            key_events=act_data["key_events"],
            emotional_arc=act_data["emotional_arc"]
        )
        for act_key, act_data in raw_data["plot_structure"].items()
    }
    
    # Assemble structured elements
    story_elements = StoryElements(
        title=raw_data["title"],
        source_type=raw_data["source_type"],
        cultural_origin=raw_data.get("cultural_origin", "Unknown"),  # Added this line
        core_themes=raw_data["core_themes"],
        main_characters=characters,
        plot_structure=plot_structure,
        core_conflict=raw_data["core_conflict"],
        resolution_theme=raw_data["resolution_theme"]
    )
    
    return story_elements


def get_character_summary(elements: StoryElements) -> str:
    """
    Generate a text summary of characters for prompt context
    
    Args:
        elements: Structured story elements
    
    Returns:
        Formatted string describing all characters
    """
    summary = []
    for char in elements.main_characters:
        summary.append(
            f"- {char.name} ({char.role}): {', '.join(char.traits)}. "
            f"Motivated by: {char.motivation}"
        )
    return "\n".join(summary)


def get_plot_summary(elements: StoryElements) -> str:
    """
    Generate a text summary of plot structure for prompt context
    
    Args:
        elements: Structured story elements
    
    Returns:
        Formatted string describing plot acts
    """
    summary = []
    for act_key, act in elements.plot_structure.items():
        events = "; ".join(act.key_events)
        summary.append(
            f"{act.name}: {events} | Emotional arc: {act.emotional_arc}"
        )
    return "\n".join(summary)


# Testing function
if __name__ == "__main__":
    from rich import print as rprint
    from rich.panel import Panel
    from rich.console import Console
    
    console = Console()
    
    # Extract story elements
    console.print("\n[bold cyan]Extracting Story Elements...[/bold cyan]\n")
    
    try:
        elements = extract_story_elements("ramayana")
        
        # Display extracted data
        rprint(Panel(
            f"[green]✓[/green] Successfully extracted: [bold]{elements.title}[/bold]",
            title="Story Loaded"
        ))
        
        console.print("\n[yellow]Core Themes:[/yellow]")
        for theme in elements.core_themes:
            console.print(f"  • {theme}")
        
        console.print("\n[yellow]Characters:[/yellow]")
        console.print(get_character_summary(elements))
        
        console.print("\n[yellow]Plot Structure:[/yellow]")
        console.print(get_plot_summary(elements))
        
        console.print("\n[yellow]Core Conflict:[/yellow]")
        console.print(f"  {elements.core_conflict}")
        
        console.print("\n[bold green]✓ Extractor working correctly![/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
