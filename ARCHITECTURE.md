# Architecture Documentation

## 1. Component Interaction Diagram

```mermaid
flowchart TD
    Client[Web/Mobile Client] -->|REST API| API(FastAPI Backend)
    API --> ORCH[Orchestrator]
    
    subgraph Guardrails
        IN[Input Guard]
        OUT[Output Guard]
    end
    
    subgraph State Management
        STORE[(In-Memory Store)]
    end
    
    subgraph Agents
        TRIAGE(Triage Agent)
        TECH(Technical Agent)
        BILL(Billing Agent)
        ESC(Escalation Agent)
    end
    
    subgraph Handover Protocol
        HANDOVER[Handover Logic]
        AUDIT[(Audit Log JSONL)]
    end
    
    ORCH --> IN
    IN --> STORE
    STORE --> TRIAGE
    
    TRIAGE -.->|Route| TECH
    TRIAGE -.->|Route| BILL
    TRIAGE -.->|Route| ESC
    
    TECH -.->|Handover Event| HANDOVER
    BILL -.->|Handover Event| HANDOVER
    
    HANDOVER --> AUDIT
    HANDOVER -.-> ESC
    
    TECH --> OUT
    BILL --> OUT
    TRIAGE --> OUT
    ESC --> OUT
    
    OUT --> API
```

## 2. Handover Protocol Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant SourceAgent
    participant Handover
    participant TargetAgent
    participant AuditLog

    User->>Orchestrator: Message
    Orchestrator->>SourceAgent: process()
    SourceAgent->>SourceAgent: Identify limit/escalation
    SourceAgent-->>Orchestrator: AgentResponse(requires_handover=True)
    Orchestrator->>SourceAgent: Generate Context Summary (LLM)
    SourceAgent-->>Orchestrator: Summary
    Orchestrator->>Handover: create_handover(Source, Target, Summary)
    Handover-->>Orchestrator: HandoverPayload
    Orchestrator->>AuditLog: log_handover(HandoverPayload)
    Orchestrator->>TargetAgent: process()
    TargetAgent-->>Orchestrator: Final AgentResponse
    Orchestrator-->>User: Response + Notification
```

## 3. RAG Pipeline Diagram

```mermaid
flowchart LR
    subgraph Ingestion
        Docs[KB JSON Articles] --> Chunk[Sliding Window Chunking]
        Chunk --> Embed1[Sentence Transformer]
        Embed1 --> VectorDB[(ChromaDB)]
    end
    
    subgraph Retrieval
        Query[User Query] --> Rewrite[LLM Query Rewriter]
        Rewrite --> Embed2[Sentence Transformer]
        Embed2 --> VectorDB
        VectorDB -->|Top K * 2| Rerank[Cross-Encoder Reranking]
        Rerank -->|Threshold Filter| Final[Retrieved Chunks]
        Final --> Agent[Specialist Agent]
    end
```

## 4. Data Flow for Test Scenarios

- **Scenario 1 (Technical routing):**
  - Input: Alert integration failing.
  - Triage extracts entities (Plan: Pro, Issue: integration). Routes to Technical.
  - Technical retrieves KB-005 and KB-007, grounds response, citations appended.
  
- **Scenario 2 (Technical to Billing):**
  - Input: Upgrade to Enterprise, check SSO issue.
  - Triage routes to Technical.
  - Technical processes SSO (KB-009). Detects "upgrade" (billing intent) and flags `suggested_next_agent = "billing"`.
  - Orchestrator catches flag, executes handover to Billing. Billing answers plan upgrade.

- **Scenario 3 (Auto-escalation):**
  - Input: Charged twice, immediate refund, manager.
  - Triage routes to Billing.
  - Billing detects "manager" keyword and refund request over safe thresholds.
  - Billing returns `requires_handover = True` (target: Escalation).
  - Escalation builds Operator payload.

- **Scenario 4 (KB Gap / Hallucination prevention):**
  - Input: Datadog integration.
  - Triage routes to Technical.
  - Technical retrieves KB chunks but finds no mention of Datadog.
  - Output Guard checks the response against the KB. Technical agent informs user it's unsupported and escalates.

## 5. Production Evolution Plan

To migrate this prototype to a fully scalable production environment:
1. **Multi-tenancy and Auth**: Implement OAuth2/OIDC. Embed `tenant_id` into all ChromaDB metadata. 
2. **State Persistence**: Replace the Python in-memory `state_store` dictionary with Redis.
3. **Queueing**: For high throughput, decouple the Orchestrator from the REST API using Celery or Kafka so long-running LLM inferences don't block web workers.
4. **Vector Database**: Upgrade ChromaDB to a managed cluster (e.g. Pinecone, Milvus) for horizontal scalability.
5. **Rate Limiting**: Enforce token-bucket rate limits per user API endpoint using Redis.

## 6. Live Deployment

The system is currently deployed and operational at the following endpoints:

- **Frontend Application (Streamlit)**: [https://clouddash-supportvikarasoumyadeep.streamlit.app/](https://clouddash-supportvikarasoumyadeep.streamlit.app/)
  - Hosts the user interface and communicates with the backend via REST.
- **Backend API (FastAPI)**: [https://clouddash-backend.onrender.com/](https://clouddash-backend.onrender.com/)
  - **Health Check**: [https://clouddash-backend.onrender.com/health](https://clouddash-backend.onrender.com/health)
  - Handles multi-agent logic, RAG retrieval, and state management on Render infrastructure.
