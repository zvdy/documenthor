#!/usr/bin/env python3
"""
Documenthor - Maintenance and cleanup utilities
"""

import os
import shutil
import json
import click
from pathlib import Path

@click.group()
def cli():
    """Documenthor maintenance utilities"""
    pass

@cli.command()
def clean_training():
    """Remove outdated training files"""
    obsolete_files = [
        "training/examples.json",
        "training/simple_examples.json", 
        "training/test_modelfile"
    ]
    
    removed_count = 0
    for file_path in obsolete_files:
        if Path(file_path).exists():
            os.remove(file_path)
            click.echo(f"✅ Removed: {file_path}")
            removed_count += 1
    
    if removed_count == 0:
        click.echo("✅ No obsolete files to remove")
    else:
        click.echo(f"✅ Removed {removed_count} obsolete files")

@cli.command()
def backup_config():
    """Backup current configuration"""
    backup_dir = Path("backups/config")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    config_files = [
        "requirements.txt",
        "Makefile",
        ".env.example",
        "k8s/"
    ]
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for config_file in config_files:
        src = Path(config_file)
        if src.exists():
            if src.is_dir():
                dst = backup_dir / f"{src.name}_{timestamp}"
                shutil.copytree(src, dst)
            else:
                dst = backup_dir / f"{src.name}_{timestamp}"
                shutil.copy2(src, dst)
            click.echo(f"✅ Backed up: {config_file}")

@cli.command()
def optimize_training():
    """Optimize training data for better performance"""
    training_file = Path("training/examples_detailed.json")
    
    if not training_file.exists():
        click.echo("❌ Training file not found")
        return
    
    with open(training_file, 'r') as f:
        data = json.load(f)
    
    optimized_data = []
    for example in data:
        # Truncate very long repository structures to prevent token overflow
        if 'repository_structure' in example:
            for key, value in example['repository_structure'].items():
                if len(value) > 8000:  # Limit file content length
                    lines = value.split('\n')
                    if len(lines) > 150:
                        example['repository_structure'][key] = '\n'.join(lines[:150]) + '\n... (truncated)'
        
        optimized_data.append(example)
    
    # Backup original
    backup_file = training_file.with_suffix('.json.backup')
    shutil.copy2(training_file, backup_file)
    
    # Save optimized version
    with open(training_file, 'w') as f:
        json.dump(optimized_data, f, indent=2)
    
    click.echo(f"✅ Optimized training data (backup saved as {backup_file})")

@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be removed without actually removing')
def clean_cache(dry_run):
    """Clean up cache and temporary files"""
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "**/*.tmp",
        "**/README.md.backup",
        ".pytest_cache"
    ]
    
    removed_count = 0
    for pattern in cache_patterns:
        for path in Path(".").glob(pattern):
            if dry_run:
                click.echo(f"Would remove: {path}")
            else:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                click.echo(f"✅ Removed: {path}")
            removed_count += 1
    
    if removed_count == 0:
        click.echo("✅ No cache files to remove")
    elif dry_run:
        click.echo(f"Would remove {removed_count} files (use without --dry-run to execute)")
    else:
        click.echo(f"✅ Removed {removed_count} cache files")

@cli.command()
def check_dependencies():
    """Check for outdated Python dependencies"""
    try:
        import subprocess
        result = subprocess.run(['.venv/bin/pip', 'list', '--outdated'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            click.echo("📦 Outdated packages:")
            click.echo(result.stdout)
            click.echo("\nTo update: .venv/bin/pip install --upgrade <package-name>")
        else:
            click.echo("✅ All packages are up to date")
    except Exception as e:
        click.echo(f"❌ Error checking dependencies: {e}")

if __name__ == '__main__':
    cli()
