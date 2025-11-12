"""
Consistency Validator
Validates coherence and consistency across generated story elements
"""
from typing import List
from utils.extractor import StoryElements
from schema.models import WorldSetting, MappedCharacter, TransformedPlotAct, ConsistencyIssue, ConsistencyReport


def validate_character_consistency(
    character_mappings: List[MappedCharacter],
    plot_acts: List[TransformedPlotAct]
) -> List[ConsistencyIssue]:
    """
    Check if character names used in plot match the mappings
    
    Args:
        character_mappings: List of character mappings
        plot_acts: List of transformed plot acts
    
    Returns:
        List of consistency issues found
    """
    issues = []
    
    # Build set of valid new character names
    valid_names = {m.new_name.lower() for m in character_mappings}
    original_to_new = {m.original_name.lower(): m.new_name for m in character_mappings}
    
    # Check each act for character name consistency
    for act in plot_acts:
        act_text = " ".join(act.key_events).lower()
        
        # Check if original character names appear (they shouldn't)
        for orig_name, new_name in original_to_new.items():
            if orig_name in act_text and orig_name not in ['rama', 'sita']:  # Common words check
                issues.append(ConsistencyIssue(
                    severity="warning",
                    category="character",
                    description=f"Original character name '{orig_name}' found in plot. Should use '{new_name}'.",
                    location=f"Act {act.act_number}"
                ))
    
    return issues


def validate_theme_preservation(
    original_themes: List[str],
    plot_acts: List[TransformedPlotAct]
) -> List[ConsistencyIssue]:
    """
    Check if original themes are preserved in transformed plot
    
    Args:
        original_themes: Core themes from original story
        plot_acts: Transformed plot acts
    
    Returns:
        List of consistency issues
    """
    issues = []
    
    # Check if each act mentions theme manifestation
    for act in plot_acts:
        if not act.theme_manifestation or len(act.theme_manifestation.strip()) < 20:
            issues.append(ConsistencyIssue(
                severity="warning",
                category="theme",
                description="Theme manifestation is missing or too brief",
                location=f"Act {act.act_number}: {act.act_name}"
            ))
    
    # Check if major themes are mentioned across all acts
    all_act_text = " ".join([act.theme_manifestation.lower() for act in plot_acts])
    
    critical_themes = ['dharma', 'righteousness', 'ethics', 'loyalty', 'exile']
    mentioned_themes = sum(1 for theme in critical_themes if theme in all_act_text)
    
    if mentioned_themes < 2:
        issues.append(ConsistencyIssue(
            severity="warning",
            category="theme",
            description=f"Only {mentioned_themes} major themes mentioned. Original story has {len(original_themes)} core themes.",
            location="Overall plot"
        ))
    
    return issues


def validate_world_consistency(
    world: WorldSetting,
    plot_acts: List[TransformedPlotAct]
) -> List[ConsistencyIssue]:
    """
    Check if plot events align with established world rules
    
    Args:
        world: Generated world setting
        plot_acts: Transformed plot acts
    
    Returns:
        List of consistency issues
    """
    issues = []
    
    # Extract key world elements from setting
    world_text = (world.overview + " " + world.setting_details).lower()
    
    # Check if plot references the established world
    all_plot_text = " ".join([
        " ".join(act.key_events) for act in plot_acts
    ]).lower()
    
    # Basic world element detection
    world_elements = []
    if 'tech' in world_text or 'startup' in world_text or 'silicon' in world_text:
        world_elements.extend(['tech', 'startup', 'company', 'digital', 'data'])
    if 'space' in world_text:
        world_elements.extend(['space', 'ship', 'planet'])
    if 'medieval' in world_text or 'kingdom' in world_text:
        world_elements.extend(['kingdom', 'castle', 'knight'])
    
    # Check if plot uses world elements
    elements_used = sum(1 for elem in world_elements if elem in all_plot_text)
    
    if world_elements and elements_used == 0:
        issues.append(ConsistencyIssue(
            severity="critical",
            category="world",
            description="Plot events don't reference the established world setting",
            location="Overall plot"
        ))
    
    return issues


def validate_narrative_structure(
    plot_acts: List[TransformedPlotAct]
) -> List[ConsistencyIssue]:
    """
    Check if narrative structure is complete and coherent
    
    Args:
        plot_acts: Transformed plot acts
    
    Returns:
        List of consistency issues
    """
    issues = []
    
    # Check if we have 3 acts
    if len(plot_acts) != 3:
        issues.append(ConsistencyIssue(
            severity="critical",
            category="narrative",
            description=f"Expected 3 acts, found {len(plot_acts)}",
            location="Plot structure"
        ))
    
    # Check if each act has events
    for act in plot_acts:
        if len(act.key_events) < 2:
            issues.append(ConsistencyIssue(
                severity="warning",
                category="narrative",
                description=f"Act has too few events ({len(act.key_events)}). Expected at least 3.",
                location=f"Act {act.act_number}"
            ))
        
        # Check if emotional arc is defined
        if not act.emotional_arc or len(act.emotional_arc.strip()) < 10:
            issues.append(ConsistencyIssue(
                severity="warning",
                category="narrative",
                description="Emotional arc is missing or too brief",
                location=f"Act {act.act_number}"
            ))
    
    return issues


def run_consistency_check(
    elements: StoryElements,
    world: WorldSetting,
    character_mappings: List[MappedCharacter],
    plot_acts: List[TransformedPlotAct]
) -> ConsistencyReport:
    """
    Run complete consistency validation across all generated content
    
    Args:
        elements: Original story elements
        world: Generated world setting
        character_mappings: Character mappings
        plot_acts: Transformed plot acts
    
    Returns:
        ConsistencyReport with all findings
    """
    all_issues = []
    
    # Run all validation checks
    all_issues.extend(validate_character_consistency(character_mappings, plot_acts))
    all_issues.extend(validate_theme_preservation(elements.core_themes, plot_acts))
    all_issues.extend(validate_world_consistency(world, plot_acts))
    all_issues.extend(validate_narrative_structure(plot_acts))
    
    # Count by severity
    critical_count = sum(1 for i in all_issues if i.severity == "critical")
    warning_count = sum(1 for i in all_issues if i.severity == "warning")
    
    # Determine pass/fail
    passed = critical_count == 0
    
    # Generate summary
    if passed and len(all_issues) == 0:
        summary = "✓ All consistency checks passed! Story transformation is coherent."
    elif passed:
        summary = f"✓ Passed with {warning_count} warnings. Review recommended."
    else:
        summary = f"✗ Failed with {critical_count} critical issues and {warning_count} warnings."
    
    return ConsistencyReport(
        total_checks=4,  # Number of validation functions
        issues_found=all_issues,
        passed=passed,
        summary=summary
    )


# Testing function
if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from utils.extractor import extract_story_elements
    from utils.transformer import generate_new_setting, map_characters, transform_plot
    
    console = Console()
    
    console.print("\n[bold cyan]🔍 Consistency Checker Test[/bold cyan]\n")
    
    try:
        # Run full pipeline
        console.print("[yellow]Step 1:[/yellow] Extracting story...")
        elements = extract_story_elements("ramayana")
        console.print("[green]✓[/green]\n")
        
        console.print("[yellow]Step 2:[/yellow] Generating world...")
        world = generate_new_setting(elements, "Silicon Valley tech startup ecosystem")
        console.print("[green]✓[/green]\n")
        
        console.print("[yellow]Step 3:[/yellow] Mapping characters...")
        mappings = map_characters(elements, world)
        console.print("[green]✓[/green]\n")
        
        console.print("[yellow]Step 4:[/yellow] Transforming plot...")
        acts = transform_plot(elements, world, mappings)
        console.print("[green]✓[/green]\n")
        
        # Run consistency check
        console.print("[yellow]Step 5:[/yellow] Running consistency validation...")
        report = run_consistency_check(elements, world, mappings, acts)
        console.print("[green]✓[/green]\n")
        
        # Display results
        console.print(Panel(
            f"[bold]{report.summary}[/bold]\n\n"
            f"Total Checks: {report.total_checks}\n"
            f"Issues Found: {len(report.issues_found)}\n"
            f"Status: {'[green]PASSED[/green]' if report.passed else '[red]FAILED[/red]'}",
            title="Consistency Report",
            border_style="cyan"
        ))
        
        # Show issues if any
        if report.issues_found:
            console.print("\n[bold yellow]Issues Found:[/bold yellow]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Severity", width=10)
            table.add_column("Category", width=12)
            table.add_column("Location", width=20)
            table.add_column("Description", width=50)
            
            for issue in report.issues_found:
                severity_color = {
                    "critical": "[red]",
                    "warning": "[yellow]",
                    "info": "[blue]"
                }.get(issue.severity, "")
                
                table.add_row(
                    f"{severity_color}{issue.severity.upper()}[/]",
                    issue.category,
                    issue.location,
                    issue.description
                )
            
            console.print(table)
        
        console.print("\n[bold green]✓ Consistency Checker working correctly![/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        import traceback
        console.print(traceback.format_exc())
