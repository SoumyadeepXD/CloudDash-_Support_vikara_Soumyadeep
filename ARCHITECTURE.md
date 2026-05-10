# 🏛️ CloudDash System Architecture

This document provides a comprehensive technical overview of the CloudDash multi-agent support system, detailing the orchestration logic, data flow, and RAG integration.

---

## 1. High-Level System Design

The architecture is built on a **Modular Multi-Agent** pattern, where a central Orchestrator manages conversation state, security guardrails, and agent transitions.

```mermaid
flowchart TD
    Client[Web/Mobile Client] -->|REST API| API(FastAPI Backend)
    API --> ORCH[Orchestrator]
    
    subgraph Security_Layer [Guardrails]
        IN[Input Guard]
        OUT[Output Guard]
    end
    
    subgraph Persistence [State Management]
        STORE[(In-Memory State Store)]
    end
    
    subgraph Agent_Intelligence [Specialist Agents]
        TRIAGE(Triage Agent)
        TECH(Technical Agent)
        BILL(Billing Agent)
        ESC(Escalation Agent)
    end
    
    subgraph Governance [Handover Protocol]
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

---

## 2. Conversation & Handover Protocol

CloudDash utilizes a formal handover protocol to ensure context is preserved when a user is moved between specialists.

### Handover Sequence
```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant SourceAgent
    participant HandoverEngine
    participant TargetAgent
    participant AuditLog

    User->>Orchestrator: Message
    Orchestrator->>SourceAgent: process()
    SourceAgent->>SourceAgent: Identify limit/escalation
    SourceAgent-->>Orchestrator: AgentResponse(requires_handover=True)
    Orchestrator->>SourceAgent: Generate Context Summary (LLM)
    SourceAgent-->>Orchestrator: Summary
    Orchestrator->>HandoverEngine: create_handover(Source, Target, Summary)
    HandoverEngine-->>Orchestrator: HandoverPayload
    Orchestrator->>AuditLog: log_handover(HandoverPayload)
    Orchestrator->>TargetAgent: process()
    TargetAgent-->>Orchestrator: Final AgentResponse
    Orchestrator-->>User: Response + Notification
```

---

## 3. RAG Pipeline & Knowledge Ingestion

Our Retrieval-Augmented Generation pipeline ensures that agents provide grounded responses based on verified technical documentation.

| Phase | Description |
| :--- | :--- |
| **Ingestion** | Sliding-window chunking of JSON articles -> `all-MiniLM-L6-v2` embeddings -> ChromaDB. |
| **Retrieval** | LLM-based query rewriting -> Semantic search -> Cross-encoder re-ranking. |
| **Augmentation** | Top-K chunks are injected into the agent's system prompt as a "Grounding Context". |

```mermaid
flowchart LR
    subgraph Ingestion_Flow
        Docs[KB Articles] --> Chunk[Sliding Window]
        Chunk --> Embed1[Embedder]
        Embed1 --> VectorDB[(ChromaDB)]
    end
    
    subgraph Retrieval_Flow
        Query[User Query] --> Rewrite[Query Rewriter]
        Rewrite --> Embed2[Embedder]
        Embed2 --> VectorDB
        VectorDB -->|Candidates| Rerank[Re-ranking]
        Rerank -->|Filtered| Final[Context]
        Final --> Agent[Specialist Agent]
    end
```

---

## 4. Operational Guardrails

| Guardrail | Function | Implementation |
| :--- | :--- | :--- |
| **Input Guard** | Detects PII, injection attempts, and off-topic requests. | Regex + LLM Classifier |
| **Output Guard** | Ensures responses are professional, grounded, and free of sensitive internal data. | LLM Fact-Checker |
| **State Consistency** | Prevents agent loops and ensures a deterministic conversation path. | Finite State Machine |

---

## 5. Live Deployment Status

The system is currently operational in a distributed production environment:

- **Frontend Application**: [Streamlit Portal](https://clouddash-supportvikarasoumyadeep.streamlit.app/)
- **API Infrastructure**: [Render Backend Service](https://clouddash-backend.onrender.com/)
- **Monitoring**: [Health Endpoint](https://clouddash-backend.onrender.com/health)

---

## 6. Production Evolution Roadmap

To transition this architecture to a high-availability enterprise environment, the following migrations are planned:

1. **State Management**: Migration from local `state_store` to **Redis Cluster**.
2. **Authentication**: Integration of **Auth0/Okta** for multi-tenant isolation.
3. **Async Processing**: Decoupling the Orchestrator via **Celery/Redis** to handle long-running LLM tasks.
4. **Vector Scaling**: Transitioning ChromaDB to **managed Pinecone** for horizontal scalability.
