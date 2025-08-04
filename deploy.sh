#!/bin/bash

#!/bin/bash
set -e
# Documenthor Deployment Script for minikube
# This script deploys Ollama with GPU support to minikube

echo "🚀 Deploying Documenthor to minikube..."

# Check if minikube is running
if ! minikube status | grep -q "Running"; then
    echo "❌ minikube is not running. Please start minikube first:"
    echo "   minikube start"
    exit 1
fi

echo "✅ minikube is running"

# Apply Kubernetes manifests
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f k8s/

# Wait for deployment to be ready
echo "⏳ Waiting for Ollama deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ollama -n ollama

echo "✅ Ollama deployment is ready"

# Port forward in background
echo "🔗 Setting up port forwarding..."
kubectl port-forward -n ollama svc/ollama 11434:11434 &
PORT_FORWARD_PID=$!

# Save PID for cleanup
echo $PORT_FORWARD_PID > /tmp/ollama-port-forward.pid

echo "✅ Port forwarding established (PID: $PORT_FORWARD_PID)"

# Wait a moment for port forward to establish
sleep 3

# Pull the base model
echo "📥 Pulling base model (this may take a while)..."
curl -s http://localhost:11434/api/pull -d '{"name":"codellama:7b"}' | while read line; do
    if echo "$line" | jq -e '.status' > /dev/null 2>&1; then
        status=$(echo "$line" | jq -r '.status')
        echo "Status: $status"
    fi
done

echo "✅ Base model pulled successfully"

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. Test the connection: python documentator.py --list-models"
echo "3. Generate documentation: python documentator.py --repo-path /path/to/repo --generate"
echo ""
echo "To stop port forwarding: kill \$(cat /tmp/ollama-port-forward.pid)"
echo "To cleanup deployment: kubectl delete namespace ollama"
