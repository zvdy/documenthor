# Documenthor - AI Repository Documentation Generator

A GPU-accelerated AI tool that processes entire repositories and generates comprehensive README files using AI with Ollama. Designed to analyze "whole repos with many many documents and code" for complete documentation generation.

## Features

- 🚀 **GPU-Accelerated**: Lightning-fast documentation generation with NVIDIA GPU support
- 📁 **Comprehensive Analysis**: Processes entire repository structures, not just brief descriptions
- 🤖 **AI-Powered**: Uses fine-tuned Ollama models for intelligent documentation
- 🔄 **Update & Generate**: Creates new READMEs or updates existing ones with new features
- 🌐 **Multi-Language**: Supports multiple programming languages (Python, JavaScript, Go, etc.)
- 🏗️ **Local Infrastructure**: Runs entirely on local minikube + Ollama with GPU acceleration
- 🎯 **Fine-Tunable**: Custom models trained on your documentation style
- ⚡ **One-Command Setup**: Complete installation with `make setup`

## Prerequisites

- **NVIDIA GPU** with drivers installed
- **NVIDIA Container Toolkit** for Docker GPU support
- **minikube** with Docker driver support
- **kubectl** configured
- **Docker** with GPU acceleration
- **Python 3.8+**

## Quick Start

### Option 1: Complete Setup (Recommended)
```bash
# Clone and setup everything with GPU acceleration
git clone https://github.com/zvdy/documenthor
cd documenthor
make setup
```

This will:
- Install Python dependencies
- Setup minikube with GPU support
- Deploy Ollama with NVIDIA GPU acceleration
- Pull the base model (llama3.2:3b)
- Setup port forwarding

### Option 2: Manual Installation

#### 1. Check Prerequisites and GPU Support
```bash
make check-prerequisites
make check-gpu
```

#### 2. Install NVIDIA Container Toolkit (if needed)
```bash
# Ubuntu/Debian only
make install-nvidia-toolkit
```

#### 3. Setup Python Environment
```bash
make install
```

#### 4. Deploy with GPU Acceleration
```bash
make setup-minikube  # Start minikube with --gpus=all
make deploy          # Deploy Ollama with GPU support
make pull-model      # Pull llama3.2:3b model
```

## Usage

### Generate Documentation for Any Repository
```bash
# Generate for sample repository
make generate-docs

# Generate for your own repository
make generate-custom REPO=/path/to/your/repo

# Or use Python directly
.venv/bin/python documentator.py --repo-path /path/to/repo --model documenthor-gpu:latest --generate
```

### Create Fine-Tuned Model
```bash
# Create model optimized for your documentation style
make fine-tune
```

### Update Existing README
```bash
.venv/bin/python documentator.py --repo-path /path/to/repo --model documenthor-gpu:latest --update
```

### List Available Models
```bash
make list-models
```

## GPU Performance

With GPU acceleration, documentation generation is **nearly instantaneous**:
- **CPU-only**: 30-60 seconds per repository
- **GPU-accelerated**: 2-5 seconds per repository
- **Model**: llama3.2:3b with 4-bit quantization (Q4_K_M)
- **Memory**: ~2GB VRAM usage

## Configuration

### Environment Variables
```bash
# Ollama endpoint (auto-configured with port forwarding)
export OLLAMA_HOST="http://localhost:11434"

# Model selection
export OLLAMA_MODEL="documenthor-gpu:latest"  # Fine-tuned model
# export OLLAMA_MODEL="llama3.2:3b"           # Base model
```

### GPU Configuration
The system automatically detects and uses NVIDIA GPUs when available:
- **GPU Detection**: Automatic via NVIDIA Container Toolkit
- **Memory Management**: Dynamic VRAM allocation
- **Multi-GPU**: Uses first available GPU (nvidia.com/gpu: 1)

### Makefile Commands
```bash
make help          # Show all available commands
make status        # Check system status
make gpu-info      # Show GPU information
make logs          # View Ollama logs
make benchmark     # Test performance
make restart       # Restart all services
make clean         # Clean up everything
make health        # Comprehensive health check
make maintain      # Run maintenance tasks
make optimize      # Optimize system performance
make backup        # Backup configuration and models
```

## Fine-Tuning

The system includes comprehensive training data with real repository examples:

### Automatic Fine-Tuning
```bash
make fine-tune
```

This creates `documenthor-gpu:latest` optimized for:
- Repository structure analysis
- Multi-language code understanding
- Professional documentation formatting
- API endpoint documentation
- Installation and usage instructions

### Training Data
Located in `training/` directory:
- **Real Examples**: Complete Express.js and Go microservices
- **Full Context**: Entire codebases, not just snippets
- **Comprehensive**: Package files, source code, tests, Dockerfiles
- **Professional**: Production-quality documentation examples

### Custom Training
```bash
# Add your repositories to training/repositories/
# Then regenerate the model
.venv/bin/python fine_tune.py --training-dir training --base-model llama3.2:3b --output-model your-custom-model:latest
```

## Troubleshooting

### GPU Issues
```bash
# Check GPU support
make check-gpu
nvidia-smi

# View GPU usage in container
make gpu-info

# Install NVIDIA Container Toolkit
make install-nvidia-toolkit
```

### minikube Issues
```bash
# Restart with GPU support
minikube delete
make setup-minikube

# Check minikube GPU support
minikube ssh -- nvidia-smi
```

### Port Forwarding Issues
```bash
# Restart port forwarding
make port-forward

# Check status
make status
```

### Performance Issues
```bash
# Run comprehensive health check
make health

# Clean up unused models and cache
make optimize

# Check model performance
make perf-test
```

### Maintenance
```bash
# Regular maintenance
make maintain     # Cleanup, optimization, dependency checks

# Create backups
make backup       # Backup models and configuration

# Clean specific items
make clean-models # Remove unused models
```

## System Requirements

### Minimum Requirements
- **GPU**: NVIDIA GPU with 2GB+ VRAM
- **RAM**: 8GB system RAM
- **Storage**: 10GB free space
- **OS**: Linux with NVIDIA drivers

### Recommended Setup
- **GPU**: RTX 4070 or better (tested configuration)
- **RAM**: 16GB+ system RAM  
- **Storage**: 20GB+ SSD
- **minikube**: 8GB memory allocation (`--memory=8192`)

## License

MIT License
