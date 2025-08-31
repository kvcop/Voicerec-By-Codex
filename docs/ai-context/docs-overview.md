# Documentation Architecture

This project uses a **3-tier documentation system** that organizes knowledge by stability and scope, enabling efficient AI context loading and scalable development.

## How the 3-Tier System Works

**Tier 1 (Foundation)**: Stable, system-wide documentation that rarely changes - architectural principles, technology decisions, cross-component patterns, and core development protocols.

**Tier 2 (Component)**: Architectural charters for major components - high-level design principles, integration patterns, and component-wide conventions without feature-specific details.

**Tier 3 (Feature-Specific)**: Granular documentation co-located with code - specific implementation patterns, technical details, and local architectural decisions that evolve with features.

This hierarchy allows AI agents to load targeted context efficiently while maintaining a stable foundation of core knowledge.

## Documentation Principles
- **Co-location**: Documentation lives near relevant code
- **Smart Extension**: New documentation files created automatically when warranted
- **AI-First**: Optimized for efficient AI context loading and machine-readable patterns

## Tier 1: Foundational Documentation (System-Wide)

- **[Master Context](/CLAUDE.md)** - *Essential for every session.* Coding standards, security requirements, MCP server integration patterns, and development protocols
- **[Project Structure](/docs/ai-context/project-structure.md)** - *REQUIRED reading.* Complete technology stack, file tree, and system architecture. Fully updated with Voicerec-By-Codex specifics
- **[System Integration](/docs/ai-context/system-integration.md)** - *For cross-component work.* Communication patterns, data flow, testing strategies, and performance optimization
- **[Deployment Infrastructure](/docs/ai-context/deployment-infrastructure.md)** - *Infrastructure patterns.* Containerization, monitoring, CI/CD workflows, and scaling strategies
- **[Task Management](/docs/ai-context/handoff.md)** - *Session continuity.* Current tasks, documentation system progress, and next session goals

## Tier 2: Component-Level Documentation

### Backend Components
- **[Backend Context](/backend/CONTEXT.md)** - *FastAPI server implementation.* Service layer architecture, repository pattern, gRPC integration, and async patterns
- **[Worker Services](/workers/CONTEXT.md)** - *Background processing.* Job queue patterns, scheduling, and async task management
- **[Shared Libraries](/shared/CONTEXT.md)** - *Reusable code.* Common utilities, shared types, and cross-component functionality

### Frontend Components
- **[Web Application](/frontend/CONTEXT.md)** - *React/TypeScript client.* Component patterns, Vite configuration, shadcn/ui integration, and i18n support
- **[Mobile Application](/mobile/CONTEXT.md)** - *Mobile implementation.* Platform-specific patterns, native integrations, and mobile optimizations
- **[Admin Dashboard](/admin/CONTEXT.md)** - *Administrative interface.* Permission patterns, admin workflows, and management tools

### Infrastructure Components
- **[Infrastructure Code](/infrastructure/CONTEXT.md)** - *IaC patterns.* Terraform/CloudFormation templates, resource definitions, and deployment automation
- **[Monitoring Setup](/monitoring/CONTEXT.md)** - *Observability patterns.* Metrics collection, alerting rules, and dashboard configurations

## Tier 3: Feature-Specific Documentation

Granular CONTEXT.md files co-located with code for minimal cascade effects:

### Backend Feature Documentation
- **[Core Services](/backend/app/core/CONTEXT.md)** - *Configuration and utilities.* Pydantic settings, GPU configuration, security utilities, logging, and validation
- **[API Layer](/backend/app/api/CONTEXT.md)** - *FastAPI endpoints.* RESTful patterns, SSE streaming, file uploads, error handling, and OpenAPI documentation
- **[Data Layer](/backend/src/data/CONTEXT.md)** - *Data patterns.* Database models, queries, migrations, and data access patterns
- **[Authentication](/backend/src/auth/CONTEXT.md)** - *Auth patterns.* Authentication flows, authorization rules, session management, and security
- **[Integrations](/backend/src/integrations/CONTEXT.md)** - *External services.* Third-party API clients, webhook handlers, and service adapters

### Frontend Feature Documentation
- **[UI Components](/frontend/src/components/CONTEXT.md)** - *React components.* Component architecture, CSS modules, accessibility patterns, and testing strategies
- **[State Management](/frontend/src/store/CONTEXT.md)** - *State patterns.* Global state, local state, data flow, and persistence strategies
- **[API Client](/frontend/src/api/CONTEXT.md)** - *Client patterns.* HTTP clients, error handling, caching, and data synchronization
- **[Routing](/frontend/src/routes/CONTEXT.md)** - *Navigation patterns.* Route definitions, guards, lazy loading, and deep linking
- **[Utilities](/frontend/src/utils/CONTEXT.md)** - *Helper functions.* Formatters, validators, transformers, and common utilities

### Shared Feature Documentation
- **[Common Types](/shared/src/types/CONTEXT.md)** - *Type definitions.* Shared interfaces, enums, and type utilities
- **[Validation Rules](/shared/src/validation/CONTEXT.md)** - *Validation patterns.* Schema definitions, custom validators, and error messages
- **[Constants](/shared/src/constants/CONTEXT.md)** - *Shared constants.* Configuration values, enums, and magic numbers
- **[Utilities](/shared/src/utils/CONTEXT.md)** - *Shared utilities.* Cross-platform helpers, formatters, and common functions



## Adding New Documentation

### New Component
1. Create `/new-component/CONTEXT.md` (Tier 2)
2. Add entry to this file under appropriate section
3. Create feature-specific Tier 3 docs as features develop

### New Feature
1. Create `/component/src/feature/CONTEXT.md` (Tier 3)
2. Reference parent component patterns
3. Add entry to this file under component's features

### Deprecating Documentation
1. Remove obsolete CONTEXT.md files
2. Update this mapping document
3. Check for broken references in other docs

---

*This documentation architecture template should be customized to match your project's actual structure and components. Add or remove sections based on your architecture.*