# MetaQore LLM Gateway Blueprint

**Version**: 2.0.0
**Description**: Production LLM Gateway for MetaQore. Implements dynamic prompt injection, continuous batching, and hybrid KV caching to serve a unified, governed agentic workforce.

## Core Principles
1. **Decouple HTTP handling from GPU execution** via a queue-based architecture.
2. **Maximize GPU utilization** through continuous batching and cache-aware scheduling.
3. **Support dynamic prompt injection**: cache static agent profiles, inject task context at runtime.
4. **Maintain MetaQore governance**: all requests are auditable and must pass SecureGateway policy checks.

## Architecture

### 1. API Gateway & Request Ingestion
- **Governance Interceptor**: Validates request, attaches PSMP context, calls `SecureGateway.classify_task()`.
- **Request Queue**: Redis-backed persistent queue.

### 2. Prompt Assembly & Caching Engine
- **Prompt Assembly Engine**: Loads unified `agent_base_profile`, injects task directive/context.
- **Hierarchical KV Cache Manager**: Manages radix tree of `static_profile_hash` values.

### 3. Orchestration & Scheduling
- **Cache-Aware Batch Scheduler**: Groups requests by profile hash to maximize KV cache hits.
- **Cache-Aware Load Balancer**: Routes to workers with hot caches.

### 4. Model Worker Pool
- **vLLM/Ollama Worker**: Stateless containers executing inference.

### 5. Response & Audit Backchannel
- **Audit Logger**: Logs immutable record compatible with MetaQore's audit system.
- **Response Streamer**: WebSocket streaming back to client.

## Configuration Spec

```json
{
  "gateway": {
    "host": "0.0.0.0",
    "port": 8080,
    "request_queue_url": "redis://localhost:6379/0"
  },
  "caching": {
    "kv_cache_enabled": true,
    "static_prefix_caching": true,
    "radix_tree_ttl_seconds": 3600
  },
  "scheduling": {
    "strategy": "cache_aware_continuous",
    "max_batch_tokens": 8192
  }
}
```

## Implementation Phasing

1. **Phase 1 - Governed Gateway Foundation**: Basic queue, dynamic prompt assembly, audit log.
2. **Phase 2 - Hybrid Caching & Scaling**: Hierarchical KV Cache Manager, cache-aware scheduler.
3. **Phase 3 - Performance Optimization**: vLLM integration, multiple GPU workers.
