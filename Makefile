# Documenthor - AI Repository Documentation Generator
# Makefile for easy setup and deployment with GPU acceleration

.PHONY: help install setup-minikube deploy test clean fine-tune list-models generate-docs

# Colors for output
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
NC := \033[0m # No Color

# Default target
help: ## Show this help message
	@echo -e "$(YELLOW)Documenthor - AI Repository Documentation Generator$(NC)"
	@echo -e "$(YELLOW)=================================================$(NC)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)GPU Requirements:$(NC)"
	@echo "  - NVIDIA GPU with Container Toolkit installed"
	@echo "  - Docker with GPU support"
	@echo "  - minikube with --driver=docker --gpus=all"

# Prerequisites check
check-prerequisites: ## Check if prerequisites are installed
	@ echo -e "$(YELLOW)Checking prerequisites...$(NC)"
	@command -v minikube >/dev/null 2>&1 || { echo "$(RED)minikube is required but not installed$(NC)"; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "$(RED)kubectl is required but not installed$(NC)"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)docker is required but not installed$(NC)"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)python3 is required but not installed$(NC)"; exit 1; }
	@ echo -e "$(GREEN)✅ All prerequisites found$(NC)"

# Check GPU support
check-gpu: ## Check GPU support and NVIDIA Container Toolkit
	@ echo -e "$(YELLOW)Checking GPU support...$(NC)"
	@nvidia-smi >/dev/null 2>&1 || { echo "$(RED)nvidia-smi not found - NVIDIA drivers may not be installed$(NC)"; exit 1; }
	@docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi >/dev/null 2>&1 || { echo "$(RED)Docker GPU support not working - install NVIDIA Container Toolkit$(NC)"; exit 1; }
	@ echo -e "$(GREEN)✅ GPU support available$(NC)"

# Python environment setup
install: check-prerequisites ## Install Python dependencies and setup virtual environment
	@ echo -e "$(YELLOW)Setting up Python environment...$(NC)"
	@python3 -m venv .venv || { echo "$(RED)Failed to create virtual environment$(NC)"; exit 1; }
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@ echo -e "$(GREEN)✅ Python environment ready$(NC)"

# Setup minikube with GPU support
setup-minikube: check-gpu ## Setup minikube with GPU acceleration
	@ echo -e "$(YELLOW)Setting up minikube with GPU support...$(NC)"
	@minikube status >/dev/null 2>&1 && echo "$(GREEN)minikube already running$(NC)" || { \
		echo "Starting minikube with GPU support..."; \
		minikube start --driver=docker --container-runtime=docker --gpus=all --memory=8192 --cpus=4; \
	}
	@kubectl cluster-info >/dev/null 2>&1 || { echo "$(RED)kubectl not connected to cluster$(NC)"; exit 1; }
	@ echo -e "$(GREEN)✅ minikube ready with GPU support$(NC)"

# Deploy Ollama to Kubernetes
deploy: setup-minikube ## Deploy Ollama with GPU acceleration to minikube
	@ echo -e "$(YELLOW)Deploying Ollama with GPU support...$(NC)"
	@kubectl apply -f k8s/
	@echo "Waiting for Ollama deployment to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment/ollama -n ollama
	@ echo -e "$(GREEN)✅ Ollama deployed successfully$(NC)"

# Setup port forwarding
port-forward: ## Setup port forwarding to access Ollama
	@ echo -e "$(YELLOW)Setting up port forwarding...$(NC)"
	@pkill -f "kubectl port-forward.*ollama.*11434" || true
	@kubectl port-forward -n ollama svc/ollama 11434:11434 &
	@echo $$! > /tmp/ollama-port-forward.pid
	@sleep 3
	@ echo -e "$(GREEN)✅ Port forwarding active (PID: $$(cat /tmp/ollama-port-forward.pid))$(NC)"

# Pull base model
pull-model: port-forward ## Pull the base model (llama3.2:3b)
	@ echo -e "$(YELLOW)Pulling base model llama3.2:3b...$(NC)"
	@curl -s http://localhost:11434/api/pull -d '{"name":"llama3.2:3b"}' | while read line; do \
		if echo "$$line" | jq -e '.status' > /dev/null 2>&1; then \
			status=$$(echo "$$line" | jq -r '.status'); \
			echo "Status: $$status"; \
		fi; \
	done
	@ echo -e "$(GREEN)✅ Base model pulled successfully$(NC)"

# Full setup (complete installation)
setup: install deploy pull-model ## Complete setup: install dependencies, deploy Ollama, pull model
	@ echo -e "$(GREEN)🎉 Complete setup finished!$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)Next steps:$(NC)"
	@echo "  make test          # Test the installation"
	@echo "  make fine-tune     # Create fine-tuned model"
	@echo "  make generate-docs # Generate documentation for a sample repo"

# Create fine-tuned model
fine-tune: ## Create fine-tuned model for documentation
	@ echo -e "$(YELLOW)Creating fine-tuned model...$(NC)"
	@.venv/bin/python fine_tune.py --training-dir training --base-model llama3.2:3b --output-model documenthor-gpu:latest
	@ echo -e "$(GREEN)✅ Fine-tuned model created: documenthor-gpu:latest$(NC)"

# List available models
list-models: ## List available Ollama models
	@ echo -e "$(YELLOW)Available models:$(NC)"
	@.venv/bin/python documentator.py --list-models

# Test installation
test: ## Test the complete installation
	@ echo -e "$(YELLOW)Testing installation...$(NC)"
	@.venv/bin/python test_setup.py
	@ echo -e "$(GREEN)✅ Installation test completed$(NC)"

# Generate documentation for sample repository
generate-docs: ## Generate documentation for sample Express.js repository
	@ echo -e "$(YELLOW)Generating documentation for sample repository...$(NC)"
	@.venv/bin/python documentator.py --repo-path training/repositories/express-auth-service --model documenthor-gpu:latest --generate
	@ echo -e "$(GREEN)✅ Documentation generated$(NC)"
	@ echo -e "$(YELLOW)Check: training/repositories/express-auth-service/README.md$(NC)"

# Generate documentation for custom repository
generate-custom: ## Generate documentation for custom repository (usage: make generate-custom REPO=path/to/repo)
ifndef REPO
	@ echo -e "$(RED)Usage: make generate-custom REPO=path/to/repository$(NC)"
	@exit 1
endif
	@ echo -e "$(YELLOW)Generating documentation for $(REPO)...$(NC)"
	@.venv/bin/python documentator.py --repo-path $(REPO) --model documenthor-gpu:latest --generate
	@ echo -e "$(GREEN)✅ Documentation generated for $(REPO)$(NC)"

# Clean up
clean: ## Clean up deployments and stop services
	@ echo -e "$(YELLOW)Cleaning up...$(NC)"
	@pkill -f "kubectl port-forward.*ollama.*11434" || true
	@rm -f /tmp/ollama-port-forward.pid
	@kubectl delete namespace ollama --ignore-not-found=true
	@ echo -e "$(GREEN)✅ Cleanup completed$(NC)"

# Clean up training files (removes old/unused training data)
clean-training: ## Remove outdated training files
	@ echo -e "$(YELLOW)Cleaning up old training files...$(NC)"
	@rm -f training/examples.json training/simple_examples.json training/test_modelfile
	@ echo -e "$(GREEN)✅ Old training files removed$(NC)"

# Restart services
restart: clean deploy ## Restart all services (clean + deploy)
	@ echo -e "$(GREEN)✅ Services restarted$(NC)"

# Development mode - watch for changes and auto-restart
dev: ## Development mode with auto-restart
	@ echo -e "$(YELLOW)Starting development mode...$(NC)"
	@echo "Press Ctrl+C to stop"
	@while true; do \
		make port-forward; \
		sleep 30; \
	done

# Show status
status: ## Show status of all components
	@ echo -e "$(YELLOW)Documenthor Status$(NC)"
	@echo "=================="
	@echo ""
	@ echo -e "$(YELLOW)minikube:$(NC)"
	@minikube status || echo -e "$(RED)minikube not running$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)Kubernetes:$(NC)"
	@kubectl get pods -n ollama 2>/dev/null || echo -e "$(RED)Ollama namespace not found$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)Port forwarding:$(NC)"
	@if [ -f /tmp/ollama-port-forward.pid ] && kill -0 $$(cat /tmp/ollama-port-forward.pid) 2>/dev/null; then \
		echo -e "$(GREEN)✅ Active (PID: $$(cat /tmp/ollama-port-forward.pid))$(NC)"; \
	else \
		echo -e "$(RED)❌ Not active$(NC)"; \
	fi
	@echo ""
	@ echo -e "$(YELLOW)Ollama API:$(NC)"
	@if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo -e "$(GREEN)✅ Accessible$(NC)"; \
	else \
		echo -e "$(RED)❌ Not accessible$(NC)"; \
	fi

# Show logs
logs: ## Show Ollama deployment logs
	@kubectl logs -n ollama deployment/ollama --tail=50 -f

# Benchmark model performance
benchmark: ## Benchmark model performance (GPU vs CPU)
	@ echo -e "$(YELLOW)Benchmarking model performance...$(NC)"
	@echo "Testing with GPU acceleration..."
	@time .venv/bin/python documentator.py --repo-path training/repositories/express-auth-service --model documenthor-gpu:latest --generate
	@ echo -e "$(GREEN)✅ Benchmark completed$(NC)"

# GPU info
gpu-info: ## Show GPU information
	@ echo -e "$(YELLOW)GPU Information:$(NC)"
	@nvidia-smi
	@echo ""
	@ echo -e "$(YELLOW)Docker GPU Test:$(NC)"
	@kubectl exec -n ollama deployment/ollama -- nvidia-smi

# Install NVIDIA Container Toolkit (Ubuntu/Debian)
install-nvidia-toolkit: ## Install NVIDIA Container Toolkit (Ubuntu/Debian only)
	@ echo -e "$(YELLOW)Installing NVIDIA Container Toolkit...$(NC)"
	@curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
	@curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
	@sudo apt-get update
	@sudo apt-get install -y nvidia-container-toolkit
	@sudo nvidia-ctk runtime configure --runtime=docker
	@sudo systemctl restart docker
	@ echo -e "$(GREEN)✅ NVIDIA Container Toolkit installed$(NC)"

# Model management
clean-models: ## Remove unused Ollama models to free space
	@ echo -e "$(YELLOW)Cleaning up unused models...$(NC)"
	@kubectl exec -n ollama deployment/ollama -- ollama list | grep -v "NAME" | awk '{print $$1}' | grep -v "llama3.2:3b\|documenthor-gpu:latest" | xargs -r -I {} kubectl exec -n ollama deployment/ollama -- ollama rm {}
	@ echo -e "$(GREEN)✅ Unused models removed$(NC)"

# Backup current models
backup-models: ## Backup current fine-tuned models
	@ echo -e "$(YELLOW)Backing up models...$(NC)"
	@mkdir -p backups/models/$(shell date +%Y-%m-%d)
	@kubectl exec -n ollama deployment/ollama -- ollama list | grep documenthor | awk '{print $$1}' > backups/models/$(shell date +%Y-%m-%d)/model-list.txt
	@ echo -e "$(GREEN)✅ Model list backed up to backups/models/$(shell date +%Y-%m-%d)/$(NC)"

# Health check
health: ## Comprehensive health check of the system
	@ echo -e "$(YELLOW)Running health checks...$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)1. GPU Status:$(NC)"
	@nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | head -1 || echo -e "$(RED)No GPU found$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)2. minikube Status:$(NC)"
	@minikube status | grep -E "(host|kubelet|apiserver)" || echo -e "$(RED)minikube issues$(NC)"
	@echo ""
	@ echo -e "$(YELLOW)3. Ollama API:$(NC)"
	@if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo -e "$(GREEN)✅ API responsive$(NC)"; \
	else \
		echo -e "$(RED)❌ API not responding$(NC)"; \
	fi
	@echo ""
	@ echo -e "$(YELLOW)4. Model Status:$(NC)"
	@if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		curl -s http://localhost:11434/api/tags | jq -r '.models[] | select(.name=="documenthor-gpu:latest" or .name=="llama3.2:3b") | .name + " (" + (.size/1024/1024/1024|tostring|.[0:4]) + "GB)"' 2>/dev/null || echo -e "$(YELLOW)Models found but jq not available$(NC)"; \
	else \
		echo -e "$(RED)Models not accessible$(NC)"; \
	fi

# Performance test
perf-test: ## Run performance tests with different repository sizes
	@ echo -e "$(YELLOW)Running performance tests...$(NC)"
	@echo "Small repo (Express auth service):"
	@time .venv/bin/python documentator.py --repo-path training/repositories/express-auth-service --model documenthor-gpu:latest --generate > /dev/null 2>&1
	@echo "Medium repo (Go product service):"
	@time .venv/bin/python documentator.py --repo-path training/repositories/go-product-service --model documenthor-gpu:latest --generate > /dev/null 2>&1
	@ echo -e "$(GREEN)✅ Performance tests completed$(NC)"

# Maintenance commands
maintain: ## Run comprehensive maintenance (cleanup, optimization, checks)
	@ echo -e "$(YELLOW)Running maintenance tasks...$(NC)"
	@.venv/bin/python maintenance.py clean-cache
	@.venv/bin/python maintenance.py optimize-training
	@.venv/bin/python maintenance.py check-dependencies
	@ echo -e "$(GREEN)✅ Maintenance completed$(NC)"

backup: ## Backup configuration and models
	@ echo -e "$(YELLOW)Creating backups...$(NC)"
	@.venv/bin/python maintenance.py backup-config
	@make backup-models
	@ echo -e "$(GREEN)✅ Backup completed$(NC)"

optimize: ## Optimize system performance and clean up
	@ echo -e "$(YELLOW)Optimizing system...$(NC)"
	@make clean-models
	@.venv/bin/python maintenance.py clean-cache
	@.venv/bin/python maintenance.py optimize-training
	@ echo -e "$(GREEN)✅ System optimized$(NC)"
