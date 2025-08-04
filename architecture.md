# Documenthor Enterprise Architecture

## Professional Automated Documentation Pipeline

This architecture enables secure, scalable, automated documentation generation for entire GitHub organizations.

```mermaid
graph TB
    subgraph "GitHub Actions Runner"
        A[GitHub Action Trigger] --> B[Load Private Key Secret]
        B --> C[Generate JWT Token]
        C --> D[Batch Repository List]
        D --> E[Send Request to Documenthor API]
    end
    
    subgraph "Kubernetes Ingress Layer"
        F[Ingress Controller] --> G[JWT Verification]
        G --> H{JWT Valid?}
        H -->|Yes| I[Forward to Documenthor Service]
        H -->|No| J[403 Forbidden]
    end
    
    subgraph "Authentication Service"
        K[JWK Endpoint] --> L[Public Key Store]
        L --> M[JWT Signature Validation]
        G --> K
    end
    
    subgraph "Documenthor Service"
        I --> N[Repository Processor]
        N --> O[Clone Repository]
        O --> P[AI Analysis Engine]
        P --> Q[GPU-Accelerated Model]
        Q --> R[Generate Documentation]
        R --> S[Commit Changes]
    end
    
    subgraph "GitHub Integration"
        T[Super GitHub PAT] --> U[Organization Access]
        U --> V[Repository Write Access]
        S --> T
        O --> T
        D --> W[GitHub API - List Repos]
        W --> T
    end
    
    subgraph "Security Components"
        X[Private Key Secret] --> B
        Y[Public Key] --> K
        Z[Super PAT Secret] --> T
    end
    
    E --> F
    S --> AA[Updated Repository]
    AA --> BB[Pull Request Created]
    BB --> CC[Review & Merge]
```

## Authentication Flow Detail

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant ING as Ingress
    participant JWK as JWK Endpoint
    participant DOC as Documenthor
    participant GH as GitHub API
    
    GHA->>GHA: Load Private Key Secret
    GHA->>GHA: Generate JWT Token (RS256)
    GHA->>GH: Fetch Org Repositories
    GH-->>GHA: Repository List
    GHA->>ING: POST /api/process-batch + JWT
    ING->>JWK: GET /.well-known/jwks.json
    JWK-->>ING: Public Key
    ING->>ING: Verify JWT Signature
    alt JWT Valid
        ING->>DOC: Forward Request
        DOC->>GH: Clone Repository (Super PAT)
        DOC->>DOC: AI Analysis + Documentation
        DOC->>GH: Commit + Create PR (Super PAT)
        DOC-->>ING: Success Response
        ING-->>GHA: 200 OK
    else JWT Invalid
        ING-->>GHA: 403 Forbidden
    end
```

## API Contract

```mermaid
graph LR
    subgraph "Request Payload"
        A["{
            organization: 'acme-corp',
            repositories: [
                'service-a',
                'service-b', 
                'lib-common'
            ],
            options: {
                model: 'documenthor-gpu:latest',
                update_existing: true,
                create_pr: true
            }
        }"]
    end
    
    subgraph "Response"
        B["{
            job_id: 'uuid-123',
            status: 'processing',
            repositories: [
                {
                    name: 'service-a',
                    status: 'completed',
                    pr_url: 'github.com/...'
                }
            ]
        }"]
    end
    
    A --> C[Documenthor API]
    C --> B
```
