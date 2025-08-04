#!/usr/bin/env python3
"""
Fine-tuning script for Ollama models to improve documentation generation
"""

import os
import json
import click
import requests
from pathlib import Path
from typing import List, Dict

class OllamaFineTuner:
    def __init__(self, host: str = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    def create_modelfile(self, base_model: str, training_data: List[Dict], output_model: str) -> str:
        """Create a Modelfile for fine-tuning"""
        
        system_prompt = """You are an expert technical documentation writer. You specialize in creating clear, comprehensive README files for software projects. Your documentation should be:

1. Clear and well-structured with proper Markdown formatting
2. Include practical examples and code snippets  
3. Cover installation, usage, and API documentation
4. Professional yet accessible tone
5. Based on actual code analysis, not assumptions

Always analyze the repository structure, dependencies, and code to provide accurate documentation."""

        # Start with the base model and system prompt
        modelfile_content = f"""FROM {base_model}

SYSTEM \"\"\"{system_prompt}\"\"\"

"""
        
        # Add training examples (limit to prevent token overflow)
        max_examples = 2
        for i, example in enumerate(training_data[:max_examples]):
            if 'input' in example and 'output' in example:
                # Simple format - limit sizes
                input_text = example['input'][:1500] + ("..." if len(example['input']) > 1500 else "")
                output_text = example['output'][:2000] + ("..." if len(example['output']) > 2000 else "")
                
                # Add as MESSAGE pairs
                modelfile_content += f"""MESSAGE user \"\"\"{input_text}\"\"\"
MESSAGE assistant \"\"\"{output_text}\"\"\"

"""
            elif 'repository_name' in example and 'repository_structure' in example:
                # Complex format - create simplified version
                repo_context = f"Repository: {example['repository_name']}\\n\\nKey Files:\\n"
                
                # Only include key files
                important_files = ['package.json', 'requirements.txt', 'app.py', 'index.js']
                for filename, content in example['repository_structure'].items():
                    if filename in important_files:
                        repo_context += f"\\n{filename}: {content[:400]}...\\n"
                
                prompt = f"Analyze this repository and generate a comprehensive README.md:\\n\\n{repo_context}"
                prompt = prompt[:1200] + ("..." if len(prompt) > 1200 else "")
                
                readme = example['expected_readme'][:1800] + ("..." if len(example['expected_readme']) > 1800 else "")
                
                modelfile_content += f"""MESSAGE user \"\"\"{prompt}\"\"\"
MESSAGE assistant \"\"\"{readme}\"\"\"

"""
        
        return modelfile_content
    
    def fine_tune(self, base_model: str, training_dir: Path, output_model: str) -> bool:
        """Fine-tune a model with training data"""
        
        # Load training data
        training_data = self._load_training_data(training_dir)
        if not training_data:
            click.echo("No training data found", err=True)
            return False
        
        click.echo(f"Loaded {len(training_data)} training examples")
        
        # Create Modelfile
        modelfile_content = self.create_modelfile(base_model, training_data, output_model)
        
        # Save Modelfile
        modelfile_path = training_dir / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        click.echo(f"Created Modelfile: {modelfile_path}")
        
        # Use kubectl and ollama CLI for model creation (more reliable)
        try:
            import subprocess
            
            # Get the Ollama pod name
            result = subprocess.run([
                "kubectl", "get", "pod", "-n", "ollama", 
                "-l", "name=ollama", 
                "-o", "jsonpath={.items[0].metadata.name}"
            ], capture_output=True, text=True, check=True)
            
            pod_name = result.stdout.strip()
            if not pod_name:
                # Fallback to deployment name
                result = subprocess.run([
                    "kubectl", "get", "pods", "-n", "ollama", 
                    "-o", "jsonpath={.items[0].metadata.name}"
                ], capture_output=True, text=True, check=True)
                pod_name = result.stdout.strip()
            
            click.echo(f"Using Ollama pod: {pod_name}")
            
            # Copy Modelfile to pod
            subprocess.run([
                "kubectl", "cp", str(modelfile_path), 
                f"ollama/{pod_name}:/tmp/Modelfile"
            ], check=True)
            
            # Create model using ollama CLI
            result = subprocess.run([
                "kubectl", "exec", "-n", "ollama", pod_name, "--",
                "ollama", "create", output_model, "-f", "/tmp/Modelfile"
            ], capture_output=True, text=True, check=True)
            
            click.echo("Model creation output:")
            click.echo(result.stdout)
            if result.stderr:
                click.echo(f"Warnings: {result.stderr}")
            
            click.echo(f"Successfully created fine-tuned model: {output_model}")
            return True
            
        except subprocess.CalledProcessError as e:
            click.echo(f"Error creating model with kubectl: {e}", err=True)
            if e.stdout:
                click.echo(f"Output: {e.stdout}")
            if e.stderr:
                click.echo(f"Error: {e.stderr}")
            return False
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            return False
    
    def _load_training_data(self, training_dir: Path) -> List[Dict]:
        """Load training data from directory"""
        training_data = []
        
        # Look for JSON training files
        for json_file in training_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        training_data.extend(data)
                    else:
                        training_data.append(data)
            except json.JSONDecodeError:
                click.echo(f"Error reading {json_file}", err=True)
                continue
        
        # Look for example repositories
        for repo_dir in training_dir.glob("*/"):
            if repo_dir.is_dir() and (repo_dir / "README.md").exists():
                example = self._create_training_example_from_repo(repo_dir)
                if example:
                    training_data.append(example)
        
        return training_data
    
    def _create_training_example_from_repo(self, repo_dir: Path) -> Dict:
        """Create training example from a repository"""
        try:
            # Read existing README
            readme_path = repo_dir / "README.md"
            with open(readme_path, 'r') as f:
                readme_content = f.read()
            
            # Analyze repository structure (simplified)
            structure = []
            for item in repo_dir.iterdir():
                if item.name.startswith('.'):
                    continue
                structure.append(item.name)
            
            # Create input prompt
            input_prompt = f"""Analyze this repository and generate a README:

Repository structure: {', '.join(structure)}

Generate a comprehensive README.md file."""

            return {
                "input": input_prompt,
                "output": readme_content
            }
        except Exception as e:
            click.echo(f"Error processing {repo_dir}: {e}", err=True)
            return None

@click.command()
@click.option('--training-dir', required=True, help='Directory containing training data')
@click.option('--base-model', default='llama3.2:3b', help='Base model to fine-tune')
@click.option('--output-model', required=True, help='Name for the fine-tuned model')
@click.option('--ollama-host', help='Ollama host URL')
def main(training_dir: str, base_model: str, output_model: str, ollama_host: str):
    """Fine-tune an Ollama model for documentation generation"""
    
    training_path = Path(training_dir)
    if not training_path.exists():
        click.echo(f"Training directory does not exist: {training_path}", err=True)
        return
    
    # Initialize fine-tuner
    tuner = OllamaFineTuner(host=ollama_host)
    
    click.echo(f"Fine-tuning {base_model} -> {output_model}")
    click.echo(f"Training data directory: {training_path}")
    
    # Start fine-tuning
    success = tuner.fine_tune(base_model, training_path, output_model)
    
    if success:
        click.echo("Fine-tuning completed successfully!")
        click.echo(f"You can now use the model: {output_model}")
    else:
        click.echo("Fine-tuning failed!")

if __name__ == '__main__':
    main()
