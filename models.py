#!/usr/bin/env python3
"""
Ollama model management script
"""

import click
import requests
import json
import os

class OllamaManager:
    def __init__(self, host=None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    def list_models(self):
        """List available models"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            return []
    
    def pull_model(self, model_name):
        """Pull a model from the registry"""
        url = f"{self.host}/api/pull"
        payload = {"name": model_name}
        
        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "status" in data:
                        click.echo(f"Status: {data['status']}")
                        if "total" in data and "completed" in data:
                            progress = (data["completed"] / data["total"]) * 100
                            click.echo(f"Progress: {progress:.1f}%")
            
            click.echo(f"✅ Successfully pulled {model_name}")
            return True
            
        except Exception as e:
            click.echo(f"❌ Error pulling model: {e}", err=True)
            return False
    
    def delete_model(self, model_name):
        """Delete a model"""
        url = f"{self.host}/api/delete"
        payload = {"name": model_name}
        
        try:
            response = requests.delete(url, json=payload)
            response.raise_for_status()
            click.echo(f"✅ Successfully deleted {model_name}")
            return True
        except Exception as e:
            click.echo(f"❌ Error deleting model: {e}", err=True)
            return False

@click.group()
def cli():
    """Ollama Model Manager for Documenthor"""
    pass

@cli.command()
def list():
    """List all available models"""
    manager = OllamaManager()
    models = manager.list_models()
    
    if models:
        click.echo("Available models:")
        for model in models:
            click.echo(f"  - {model['name']} ({model['size']})")
    else:
        click.echo("No models found")

@cli.command()
@click.argument('model_name')
def pull(model_name):
    """Pull a model from the registry"""
    manager = OllamaManager()
    click.echo(f"Pulling {model_name}...")
    manager.pull_model(model_name)

@cli.command()
@click.argument('model_name')
@click.confirmation_option(prompt='Are you sure you want to delete this model?')
def delete(model_name):
    """Delete a model"""
    manager = OllamaManager()
    manager.delete_model(model_name)

@cli.command()
def recommended():
    """Show recommended models for documentation"""
    click.echo("Recommended models for documentation:")
    click.echo("  📝 codellama:7b - Code-focused model, good for technical docs")
    click.echo("  📝 llama2:7b - General purpose, good balance")
    click.echo("  📝 mistral:7b - Fast and efficient")
    click.echo("  📝 llama2:13b - Larger model, better quality (requires more RAM)")
    click.echo("")
    click.echo("To pull a model:")
    click.echo("  python models.py pull codellama:7b")

if __name__ == '__main__':
    cli()
