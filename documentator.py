#!/usr/bin/env python3
"""
Documenthor - AI Repository Documentation Generator using Ollama
"""

import os
import sys
import json
import click
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import git

# Load environment variables
load_dotenv()

class OllamaClient:
    def __init__(self, host: str = None, model: str = "llama3.2:3b"):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text using Ollama API"""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 4000
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            click.echo(f"Error communicating with Ollama: {e}", err=True)
            sys.exit(1)
    
    def list_models(self) -> List[str]:
        """List available models"""
        url = f"{self.host}/api/tags"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
        except requests.exceptions.RequestException as e:
            click.echo(f"Error listing models: {e}", err=True)
            return []

class RepositoryAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.ignore_patterns = [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.log",
            "target", "build", "dist", ".idea", ".vscode"
        ]
    
    def analyze(self) -> Dict:
        """Analyze repository structure and content"""
        analysis = {
            "structure": self._get_directory_structure(),
            "languages": self._detect_languages(),
            "key_files": self._find_key_files(),
            "dependencies": self._extract_dependencies(),
            "git_info": self._get_git_info(),
            "code_samples": self._extract_code_samples()
        }
        return analysis
    
    def _get_directory_structure(self) -> Dict:
        """Get repository directory structure"""
        structure = {}
        for root, dirs, files in os.walk(self.repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not any(d.startswith(pattern.rstrip('*')) for pattern in self.ignore_patterns)]
            
            rel_root = os.path.relpath(root, self.repo_path)
            if rel_root == ".":
                rel_root = ""
            
            structure[rel_root] = {
                "directories": dirs,
                "files": [f for f in files if not self._should_ignore_file(f)]
            }
        
        return structure
    
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored"""
        for pattern in self.ignore_patterns:
            if pattern.startswith("*."):
                if filename.endswith(pattern[1:]):
                    return True
            elif filename == pattern:
                return True
        return False
    
    def _detect_languages(self) -> Dict[str, int]:
        """Detect programming languages in the repository"""
        language_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".sh": "Shell",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".json": "JSON",
            ".md": "Markdown",
            ".dockerfile": "Docker",
            ".sql": "SQL"
        }
        
        language_counts = {}
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if self._should_ignore_file(file):
                    continue
                
                ext = Path(file).suffix.lower()
                if ext in language_extensions:
                    lang = language_extensions[ext]
                    language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return language_counts
    
    def _find_key_files(self) -> List[str]:
        """Find key configuration and documentation files"""
        key_files = []
        important_files = [
            "README.md", "readme.md", "README.txt",
            "package.json", "requirements.txt", "Cargo.toml",
            "go.mod", "pom.xml", "build.gradle", "composer.json",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".env.example", "config.yml", "config.yaml", "config.json"
        ]
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file in important_files:
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    key_files.append(rel_path)
        
        return key_files
    
    def _extract_dependencies(self) -> Dict:
        """Extract dependency information"""
        dependencies = {}
        
        # Python requirements
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                dependencies["python"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        # Node.js package.json
        package_file = self.repo_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    dependencies["node"] = {
                        "dependencies": package_data.get("dependencies", {}),
                        "devDependencies": package_data.get("devDependencies", {})
                    }
            except json.JSONDecodeError:
                pass
        
        return dependencies
    
    def _get_git_info(self) -> Dict:
        """Get git repository information"""
        try:
            repo = git.Repo(self.repo_path)
            return {
                "remote_url": next(iter(repo.remotes.origin.urls), ""),
                "current_branch": repo.active_branch.name,
                "last_commit": {
                    "hash": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": repo.head.commit.committed_datetime.isoformat()
                }
            }
        except:
            return {}
    
    def _extract_code_samples(self) -> Dict[str, str]:
        """Extract meaningful code samples and full content of key files"""
        samples = {}
        
        # Look for main entry points and configuration files
        important_files = [
            "main.py", "app.py", "index.js", "server.js", "main.go", "main.rs",
            "package.json", "requirements.txt", "go.mod", "Cargo.toml",
            "Dockerfile", "docker-compose.yml", ".env.example",
            "config.py", "config.js", "config.go"
        ]
        
        for file_name in important_files:
            file_path = self.repo_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # For configuration files, include full content
                        if file_name in ["package.json", "requirements.txt", "go.mod", "Cargo.toml", ".env.example"]:
                            samples[file_name] = content
                        else:
                            # For code files, limit to prevent token overflow
                            lines = content.split('\n')[:100]  # Increased from 50
                            samples[file_name] = '\n'.join(lines)[:5000]  # Increased from 2000
                except:
                    continue
        
        # Also scan for test files and important modules
        test_patterns = ["test", "spec", "__test__", "tests"]
        src_patterns = ["src", "lib", "internal", "pkg"]
        
        for pattern in src_patterns + test_patterns:
            pattern_dir = self.repo_path / pattern
            if pattern_dir.exists() and pattern_dir.is_dir():
                for file_path in pattern_dir.rglob("*"):
                    if file_path.is_file() and not self._should_ignore_file(file_path.name):
                        ext = file_path.suffix.lower()
                        if ext in [".py", ".js", ".ts", ".go", ".rs", ".java"]:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    rel_path = str(file_path.relative_to(self.repo_path))
                                    # Limit content but include more than before
                                    lines = content.split('\n')[:80]
                                    samples[rel_path] = '\n'.join(lines)[:4000]
                                    
                                    # Only include a few files to prevent overwhelming the context
                                    if len(samples) >= 10:
                                        break
                            except:
                                continue
        
        return samples

class DocumentationGenerator:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def generate_readme(self, analysis: Dict, existing_readme: str = None) -> str:
        """Generate or update README based on repository analysis"""
        
        system_prompt = """You are a technical documentation expert. Generate clear, comprehensive README files for software projects. 
        Focus on:
        - Clear project description and purpose
        - Installation instructions
        - Usage examples with code snippets
        - API documentation if applicable
        - Contributing guidelines
        - License information
        
        Use proper Markdown formatting and be concise but thorough."""
        
        if existing_readme:
            prompt = self._create_update_prompt(analysis, existing_readme)
        else:
            prompt = self._create_generation_prompt(analysis)
        
        return self.ollama.generate(prompt, system_prompt)
    
    def _create_generation_prompt(self, analysis: Dict) -> str:
        """Create prompt for generating new README"""
        prompt = f"""Analyze this complete repository and generate a comprehensive, professional README.md file.

REPOSITORY ANALYSIS:
==================

Programming Languages Detected:
{self._format_languages(analysis.get('languages', {}))}

Repository Structure:
{self._format_structure(analysis.get('structure', {}))}

Dependencies and Configuration:
{self._format_dependencies(analysis.get('dependencies', {}))}

Key Files Analysis:
{analysis.get('key_files', [])}

Complete Code Files Content:
{self._format_code_samples(analysis.get('code_samples', {}))}

Git Repository Information:
{self._format_git_info(analysis.get('git_info', {}))}

REQUIREMENTS:
=============
Generate a comprehensive README.md that includes:

1. **Project Title & Description**: Clear, compelling description of what this project does
2. **Features**: Bullet points of key capabilities
3. **Prerequisites**: System requirements, dependencies
4. **Installation**: Step-by-step setup instructions
5. **Usage**: Code examples and usage patterns
6. **API Documentation**: If applicable, document endpoints/functions
7. **Configuration**: Environment variables, config files
8. **Testing**: How to run tests
9. **Development**: Setup for contributors
10. **Deployment**: Production deployment instructions
11. **License**: License information

Make the documentation:
- **Professional** but accessible
- **Comprehensive** and accurate based on actual code
- **Well-structured** with clear Markdown formatting
- **Practical** with real examples from the codebase
- **Complete** so developers can understand, setup, and use the project immediately

Base all information on the actual code analysis provided above. Do not make assumptions."""
        
        return prompt
    
    def _create_update_prompt(self, analysis: Dict, existing_readme: str) -> str:
        """Create prompt for updating existing README"""
        prompt = f"""Update the following README.md file based on the current repository state.

Current README:
```markdown
{existing_readme}
```

Repository Analysis:
- Languages: {analysis.get('languages', {})}
- Key Files: {analysis.get('key_files', [])}
- Dependencies: {analysis.get('dependencies', {})}

Directory Structure:
{self._format_structure(analysis.get('structure', {}))}

Code Samples:
{self._format_code_samples(analysis.get('code_samples', {}))}

Tasks:
1. Update outdated information
2. Add documentation for new features/files
3. Update installation instructions if dependencies changed
4. Ensure all sections are current and accurate
5. Maintain the existing structure and tone

Return the complete updated README."""
        
        return prompt
    
    def _format_structure(self, structure: Dict) -> str:
        """Format directory structure for prompt"""
        formatted = []
        for path, contents in structure.items():
            if path:
                formatted.append(f"{path}/")
            for directory in contents.get('directories', []):
                formatted.append(f"  {directory}/")
            for file in contents.get('files', []):
                formatted.append(f"  {file}")
        return '\n'.join(formatted[:100])  # Increased limit
    
    def _format_code_samples(self, samples: Dict[str, str]) -> str:
        """Format code samples for prompt"""
        if not samples:
            return "No code samples available."
        
        formatted = []
        for filename, content in samples.items():
            formatted.append(f"\n--- {filename} ---")
            formatted.append(f"{content}")
            formatted.append("") # Empty line for separation
        return '\n'.join(formatted)
    
    def _format_languages(self, languages: Dict[str, int]) -> str:
        """Format programming languages for prompt"""
        if not languages:
            return "No programming languages detected."
        
        total_files = sum(languages.values())
        formatted = []
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files) * 100
            formatted.append(f"- {lang}: {count} files ({percentage:.1f}%)")
        return '\n'.join(formatted)
    
    def _format_dependencies(self, dependencies: Dict) -> str:
        """Format dependencies for prompt"""
        if not dependencies:
            return "No dependencies detected."
        
        formatted = []
        for lang, deps in dependencies.items():
            formatted.append(f"\n{lang.title()} Dependencies:")
            if isinstance(deps, dict):
                for dep_type, dep_list in deps.items():
                    if dep_list:
                        formatted.append(f"  {dep_type}:")
                        if isinstance(dep_list, dict):
                            for name, version in dep_list.items():
                                formatted.append(f"    - {name}: {version}")
                        else:
                            for dep in dep_list:
                                formatted.append(f"    - {dep}")
            elif isinstance(deps, list):
                for dep in deps:
                    formatted.append(f"  - {dep}")
        return '\n'.join(formatted)
    
    def _format_git_info(self, git_info: Dict) -> str:
        """Format git information for prompt"""
        if not git_info:
            return "No git information available."
        
        formatted = []
        if git_info.get('remote_url'):
            formatted.append(f"Repository URL: {git_info['remote_url']}")
        if git_info.get('current_branch'):
            formatted.append(f"Current Branch: {git_info['current_branch']}")
        if git_info.get('last_commit'):
            commit = git_info['last_commit']
            formatted.append(f"Latest Commit: {commit.get('hash', '')[:8]} - {commit.get('message', '')}")
        return '\n'.join(formatted)

@click.command()
@click.option('--repo-path', required=True, help='Path to the repository to analyze')
@click.option('--output', default='README.md', help='Output README file path')
@click.option('--model', default=None, help='Ollama model to use')
@click.option('--generate', 'mode', flag_value='generate', help='Generate new README')
@click.option('--update', 'mode', flag_value='update', help='Update existing README')
@click.option('--list-models', is_flag=True, help='List available Ollama models')
def main(repo_path: str, output: str, model: str, mode: str, list_models: bool):
    """Documenthor - AI Repository Documentation Generator"""
    
    # Initialize Ollama client
    ollama = OllamaClient(model=model)
    
    if list_models:
        models = ollama.list_models()
        click.echo("Available models:")
        for m in models:
            click.echo(f"  - {m}")
        return
    
    if not mode:
        click.echo("Please specify --generate or --update", err=True)
        sys.exit(1)
    
    # Validate repository path
    repo_path = Path(repo_path)
    if not repo_path.exists() or not repo_path.is_dir():
        click.echo(f"Repository path does not exist: {repo_path}", err=True)
        sys.exit(1)
    
    click.echo(f"Analyzing repository: {repo_path}")
    
    # Analyze repository
    analyzer = RepositoryAnalyzer(repo_path)
    analysis = analyzer.analyze()
    
    click.echo(f"Found {len(analysis['languages'])} programming languages")
    click.echo(f"Detected {len(analysis['key_files'])} key files")
    
    # Generate documentation
    generator = DocumentationGenerator(ollama)
    
    existing_readme = None
    if mode == 'update':
        readme_path = repo_path / 'README.md'
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                existing_readme = f.read()
        else:
            click.echo("No existing README found, switching to generate mode")
            mode = 'generate'
    
    click.echo(f"Generating documentation using model: {ollama.model}")
    
    readme_content = generator.generate_readme(analysis, existing_readme)
    
    # Write output
    output_path = repo_path / output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    click.echo(f"Documentation {'updated' if mode == 'update' else 'generated'}: {output_path}")

if __name__ == '__main__':
    main()
