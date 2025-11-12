#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story Transformation Engine
Handles world-building, character mapping, and plot transformation
"""
import json
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import PromptTemplate

from utils.geminiclient import initialize_llm
from utils.helpers import load_prompt_template, clean_incomplete_sentences, fix_incomplete_json
from schema.models import WorldSetting, StoryElements, MappedCharacter, TransformedPlotAct


# Load environment variables
_ = load_dotenv(find_dotenv())


def generate_new_setting(elements: StoryElements, target_world: str = "tech_startup", temperature: float = 0.7) -> WorldSetting:
    """
    Generate a new world setting for the story
    
    Args:
        elements: Extracted story elements from source material
        target_world: Description of target world (e.g., "tech_startup", "space_exploration")
        temperature: LLM creativity level
    
    Returns:
        WorldSetting object with complete world description
    """
    # Initialize LLM
    llm = initialize_llm(temperature)

    # Load prompt template
    template_text = load_prompt_template("world_building")

    # Format themes as bullet points
    themes_formatted = "\n".join([f"- {theme}" for theme in elements.core_themes])

    # Create prompt
    prompt = PromptTemplate(
        input_variables=["title", "source_type", "themes", "target_world"],
        template=template_text
    )

    # Generate world description
    formatted_prompt = prompt.format(
        title=elements.title,
        source_type=elements.source_type,
        themes=themes_formatted,
        target_world=target_world
    )

    # Add explicit instruction at the end to ensure completion
    formatted_prompt += "\n\nIMPORTANT: Complete ALL sections fully. Do not stop mid-sentence or mid-section."

    response = llm.invoke(formatted_prompt)
    full_description = response.content

    # Clean incomplete sentences from the end
    full_description = clean_incomplete_sentences(full_description)

    # Validate minimum length (rough check)
    if len(full_description) < 800:  # Approximately 120-150 words
        print(f"[Warning] Generated content is too short ({len(full_description)} chars). Regenerating...")
        # Retry once with higher temperature
        response = llm.invoke(formatted_prompt)
        full_description = clean_incomplete_sentences(response.content)

    # Parse response into sections
    sections = parse_world_description(full_description)

    return WorldSetting(
        overview=sections.get("overview", "No overview generated"),
        setting_details=sections.get("details", "No details generated"),
        theme_translation=sections.get("themes", "No theme translation generated"),
        full_description=full_description
    )


def parse_world_description(text: str) -> dict[str, str]:
    """
    Parse LLM output into structured sections
    
    Args:
        text: Raw LLM output
    
    Returns:
        Dictionary with overview, details, themes sections
    """
    sections = {
        "overview": "",
        "details": "",
        "themes": ""
    }
    
    # Simple parsing based on headers
    lines = text.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        line_lower = line.lower().strip()

        if "## world overview" in line_lower or "world overview" in line_lower:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "overview"
            current_content = []

        elif "## setting details" in line_lower or "setting details" in line_lower:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "details"
            current_content = []

        elif "## how themes translate" in line_lower or "themes translate" in line_lower:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "themes"
            current_content = []

        elif current_section and line.strip() and not line.startswith('#'):
            current_content.append(line)

    # Add last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def map_characters(elements: StoryElements, world: WorldSetting, temperature: float = 0.7) -> list[MappedCharacter]:
    """
    Map original characters to new world equivalents
    
    Args:
        elements: Extracted story elements with original characters
        world: Generated world setting
        temperature: LLM creativity level
    
    Returns:
        List of CharacterMapping objects
    """
    # Initialize LLM with higher token limit for character mappings
    llm = initialize_llm(temperature, max_tokens=6000)
    
    # Load prompt template
    template_text = load_prompt_template("character_mapping")
    
    # Format characters for prompt
    from utils.extractor import get_character_summary
    characters_formatted = get_character_summary(elements)
    
    # Format themes
    themes_formatted = "\n".join([f"- {theme}" for theme in elements.core_themes])
    
    # Build prompt by replacing placeholders manually (safer than .format())
    formatted_prompt = template_text
    formatted_prompt = formatted_prompt.replace("{title}", elements.title)
    formatted_prompt = formatted_prompt.replace("{world_description}", 
                                                world.overview + "\n\n" + world.setting_details[:500])  # Limit world desc
    formatted_prompt = formatted_prompt.replace("{characters}", characters_formatted)
    formatted_prompt = formatted_prompt.replace("{themes}", themes_formatted)
    
    # Add explicit instruction for complete JSON
    formatted_prompt += "\n\nIMPORTANT: Generate COMPLETE JSON with all closing brackets. Do not stop mid-response."
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = llm.invoke(formatted_prompt)
            raw_output = response.content.strip()
            
            # Clean JSON output (remove markdown if present)
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
            # Remove any leading/trailing whitespace
            raw_output = raw_output.strip()
            
            # Validate JSON is complete (basic check)
            if not raw_output.endswith(']'):
                print(f"[Warning] JSON appears incomplete (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print("[Info] Retrying with adjusted parameters...")
                    continue
                else:
                    # Try to fix incomplete JSON
                    raw_output = fix_incomplete_json(raw_output)
            
            # Parse JSON response
            mappings_data = json.loads(raw_output)
            
            # Validate it's a list
            if not isinstance(mappings_data, list):
                raise ValueError("Expected JSON array, got object")
            
            # Validate we got all characters (or at least some)
            if len(mappings_data) == 0:
                raise ValueError("No character mappings returned")
            
            # Convert to Pydantic models
            mappings = [
                MappedCharacter(**mapping)
                for mapping in mappings_data
            ]
            
            print(f"[Success] Mapped {len(mappings)} characters")
            return mappings
            
        except json.JSONDecodeError as e:
            print(f"[Error] JSON parsing failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"[Debug] First 500 chars: {raw_output[:500]}")
                print(f"[Debug] Last 200 chars: {raw_output[-200:]}")
                print("[Info] Retrying...")
                # Lower temperature for more structured output
                llm = initialize_llm(temperature=0.5, max_tokens=6000)
            else:
                print(f"[Debug] Full output:\n{raw_output}")
                raise ValueError(f"Failed to get valid JSON after {max_retries} attempts")
    
    raise ValueError("Character mapping failed")


def transform_plot(elements: StoryElements, world: WorldSetting, character_mappings: list[MappedCharacter], temperature: float = 0.75) -> list[TransformedPlotAct]:
    """
    Transform original plot structure to new world setting
    
    Args:
        elements: Extracted story elements with original plot
        world: Generated world setting
        character_mappings: Mapped characters
        temperature: LLM creativity level
    
    Returns:
        List of TransformedPlotAct objects for each act
    """
    # Initialize LLM
    llm = initialize_llm(temperature, max_tokens=6000)
    
    # Load prompt template
    template_text = load_prompt_template("plot_transformation")
    
    # Format character mappings for context
    char_map_text = "\n".join([
        f"- {m.original_name} → {m.new_name} ({m.new_role})"
        for m in character_mappings
    ])
    
    # Format original plot structure
    from utils.extractor import get_plot_summary
    plot_summary = get_plot_summary(elements)
    
    # Format themes
    themes_formatted = ", ".join(elements.core_themes)
    
    # Build prompt
    formatted_prompt = template_text
    formatted_prompt = formatted_prompt.replace("{title}", elements.title)
    formatted_prompt = formatted_prompt.replace("{world_description}", world.overview + "\n" + world.setting_details[:400])
    formatted_prompt = formatted_prompt.replace("{character_mappings}", char_map_text)
    formatted_prompt = formatted_prompt.replace("{plot_structure}", plot_summary)
    formatted_prompt = formatted_prompt.replace("{core_conflict}", elements.core_conflict)
    formatted_prompt = formatted_prompt.replace("{themes}", themes_formatted)
    
    # Add completion instruction
    formatted_prompt += "\n\nIMPORTANT: Complete all three acts fully. Do not stop mid-response."
    
    response = llm.invoke(formatted_prompt)
    full_output = response.content
    
    # Debug: Print raw output
    # print(f"\n[Debug] Raw LLM Output (first 1000 chars):\n{full_output[:1000]}\n")
    
    # Clean incomplete sentences
    full_output = clean_incomplete_sentences(full_output)
    
    # Parse the response into structured acts
    acts = parse_plot_acts(full_output)
    
    # print(f"[Debug] Parsed {len(acts)} acts")
    
    return acts


def parse_plot_acts(text: str) -> list[TransformedPlotAct]:
    """
    Parse LLM plot output into structured TransformedPlotAct objects
    
    Args:
        text: Raw LLM output with act descriptions
    
    Returns:
        List of TransformedPlotAct objects
    """
    import re
    
    acts = []
    
    # Split by act headers (## Act)
    act_pattern = r'##\s*Act\s+(\d+|One|Two|Three):\s*(.+?)(?=##\s*Act|\Z)'
    matches = re.finditer(act_pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        act_num_str = match.group(1).strip()
        act_content = match.group(2).strip()
        
        # Convert act number
        if act_num_str.isdigit():
            act_number = int(act_num_str)
        else:
            word_to_num = {'one': 1, 'two': 2, 'three': 3}
            act_number = word_to_num.get(act_num_str.lower(), 0)
        
        if act_number == 0:
            continue
        
        # Extract act name (first line before any section)
        lines = act_content.split('\n')
        act_name = lines[0].strip() if lines else "Untitled Act"
        
        # Extract emotional arc
        emotional_arc = ""
        emotional_match = re.search(r'\*\*Emotional Arc:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', act_content, re.IGNORECASE)
        if emotional_match:
            emotional_arc = emotional_match.group(1).strip()
        
        # Extract key events
        key_events = []
        events_match = re.search(r'\*\*Key Events:\*\*\s*(.+?)(?=\n\*\*|\Z)', act_content, re.DOTALL | re.IGNORECASE)
        if events_match:
            events_text = events_match.group(1).strip()
            # Split by numbered list items
            event_lines = re.findall(r'^\d+\.\s*(.+?)(?=^\d+\.|\Z)', events_text, re.MULTILINE | re.DOTALL)
            for event in event_lines:
                cleaned = event.strip()
                if cleaned:
                    key_events.append(cleaned)
        
        # Extract theme manifestation
        theme_manifestation = ""
        theme_match = re.search(r'\*\*How Original Themes Manifest:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)', act_content, re.DOTALL | re.IGNORECASE)
        if theme_match:
            theme_manifestation = theme_match.group(1).strip()
        
        # Create act object
        if key_events:  # Only add if we have events
            acts.append(TransformedPlotAct(
                act_number=act_number,
                act_name=act_name,
                emotional_arc=emotional_arc,
                key_events=key_events,
                theme_manifestation=theme_manifestation
            ))
    
    return acts

# Testing function
if __name__ == "__main__":
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table

    from utils.extractor import extract_story_elements

    # Save output in the output folder as a markdown
    OUTPUT_DIR = Path("output")
    FILE_NAME = "ramayana_x_silicon_valley_ninth"
    outputfile = OUTPUT_DIR / f'{FILE_NAME}.md'

    console = Console()

    console.print("\n[bold cyan]🌍 World Builder Test[/bold cyan]\n")

    try:
        # Extract story elements
        console.print("[yellow]Step 1:[/yellow] Extracting story elements...")
        elements = extract_story_elements("ramayana")
        console.print("[green]✓[/green] Story extracted\n")

        # Generate new world
        console.print("[yellow]Step 2:[/yellow] Generating Tech Startup world...")
        console.print("[dim]This may take 10-15 seconds...[/dim]\n")

        world = generate_new_setting(
            elements=elements,
            target_world="Silicon Valley tech startup ecosystem",
            temperature=0.8
        ) 

        console.print("[green]✓[/green] World generated!\n")

        # Display results
        console.print(Panel(
            Markdown(world.full_description),
            title="[bold]Generated World Setting[/bold]",
            border_style="cyan"
        ))

        if OUTPUT_DIR.exists():
            console.print(f"[yellow]Step 3:[/yellow] Saving output at {OUTPUT_DIR}/...")
            with open(outputfile, 'w', encoding='utf-8') as f:
                f.write(world.full_description)

            console.print("[bold green]✓[/bold green] Done!")

        console.print("\n[bold green]✓ World Builder working correctly![/bold green]\n")

        # Step 3: Map characters
        console.print("[yellow]Step 4:[/yellow] Mapping characters to new world...")
        console.print("[dim]This may take 15-20 seconds...[/dim]\n")
        
        mappings = map_characters(
            elements=elements,
            world=world,
            temperature=0.7
        )
        
        console.print("[green]✓[/green] Characters mapped!\n")
        
        # Display results in table
        table = Table(title="Character Mappings", show_header=True, header_style="bold magenta")
        table.add_column("Original", style="cyan", width=12)
        table.add_column("New Name", style="green", width=12)
        table.add_column("New Role", style="yellow", width=20)
        table.add_column("Core Traits", style="blue", width=25)
        table.add_column("Motivation", style="magenta", width=30)
        
        for mapping in mappings:
            table.add_row(
                mapping.original_name,
                mapping.new_name,
                mapping.new_role,
                ", ".join(mapping.core_traits[:3]),  # First 3 traits
                mapping.motivation[:60] + "..." if len(mapping.motivation) > 60 else mapping.motivation
            )
        
        console.print(table)
        
        # Display transformation rationales
        console.print("\n[bold yellow]📝 Transformation Rationales:[/bold yellow]\n")
        for mapping in mappings:
            console.print(Panel(
                mapping.transformation_rationale,
                title=f"[cyan]{mapping.original_name}[/cyan] → [green]{mapping.new_name}[/green]",
                border_style="dim"
            ))

        console.print("\n[bold green]✓ Character Mapper working correctly![/bold green]\n")

        # Step 4: Transform plot
        console.print("[yellow]Step 4:[/yellow] Transforming plot structure...")
        console.print("[dim]This may take 20-30 seconds...[/dim]\n")
        
        acts = transform_plot(
            elements=elements,
            world=world,
            character_mappings=mappings,
            temperature=0.75
        )
        
        console.print(f"[green]✓[/green] Plot transformed into {len(acts)} acts!\n")
        
        # Display results
        for act in acts:
            console.print(Panel(
                f"[yellow]Emotional Arc:[/yellow] {act.emotional_arc}\n\n"
                f"[yellow]Key Events:[/yellow]\n" + 
                "\n".join([f"  {i+1}. {event}" for i, event in enumerate(act.key_events)]) +
                f"\n\n[yellow]Theme Manifestation:[/yellow]\n{act.theme_manifestation}",
                title=f"[bold cyan]Act {act.act_number}: {act.act_name}[/bold cyan]",
                border_style="cyan"
            ))
            console.print()

        if OUTPUT_DIR.exists():
            with open('plot_transformer_first_test_output.md', 'w', encoding='utf-8') as f:
                for act in acts:
                    f.write(act.model_dump_json())

        console.print("[bold green]✓ Plot Transformer working correctly![/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")

        import traceback
        console.print(traceback.format_exc())
