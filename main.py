#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rich.console import Console
from rich.panel import Panel
from utils.extractor import extract_story_elements
from utils.transformer import generate_new_setting, map_characters, transform_plot
from utils.validator import run_consistency_check
from utils.assembler import assemble_final_output, save_output


# Testing function
def main() -> None:
    console = Console()

    console.print("\n[bold cyan]📄 Output Assembler Test[/bold cyan]\n")

    try:
        # Run full pipeline
        console.print("[yellow]Running complete pipeline...[/yellow]\n")

        console.print("  [dim]1/5[/dim] Extracting story...")
        elements = extract_story_elements("ramayana")
        console.print("  [green]✓[/green] Story extracted\n")

        console.print("  [dim]2/5[/dim] Generating world...")
        target_world = "Silicon Valley tech startup ecosystem"
        world = generate_new_setting(elements, target_world)
        console.print("  [green]✓[/green] World generated\n")

        console.print("  [dim]3/5[/dim] Mapping characters...")
        mappings = map_characters(elements, world)
        console.print(f"  [green]✓[/green] {len(mappings)} characters mapped\n")

        console.print("  [dim]4/5[/dim] Transforming plot...")
        acts = transform_plot(elements, world, mappings)
        console.print(f"  [green]✓[/green] {len(acts)} acts transformed\n")

        console.print("  [dim]5/5[/dim] Validating consistency...")
        report = run_consistency_check(elements, world, mappings, acts)
        console.print("  [green]✓[/green] Validation complete\n")

        # Assemble output
        console.print("[yellow]Assembling final document...[/yellow]\n")

        final_content = assemble_final_output(
            elements=elements,
            world=world,
            character_mappings=mappings,
            plot_acts=acts,
            consistency_report=report,
            target_world=target_world,
        )

        # Save to file
        output_path = save_output(final_content)

        console.print(
            Panel(
                f"[green]✓[/green] Document assembled successfully!\n\n"
                f"📄 Output saved to: [cyan]{output_path}[/cyan]\n"
                f"📊 Document length: [yellow]{len(final_content)}[/yellow] characters\n"
                f"📝 Sections: World-building, Characters, Plot, Rationale, Validation",
                title="Success",
                border_style="green",
            )
        )

        # Show preview
        console.print("\n[bold yellow]📖 Document Preview (first 500 chars):[/bold yellow]\n")
        console.print(Panel(final_content[:500] + "...", border_style="dim"))

        console.print("\n[bold green]✓ Output Assembler working correctly![/bold green]")
        console.print(f"[dim]Open {output_path} to see the complete reimagined story![/dim]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        import traceback

        console.print(traceback.format_exc())

if __name__ == "__main__":
    main()
