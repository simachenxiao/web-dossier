## 1. Backend Project Setup

- [x] 1.1 Create `backend/` FastAPI project structure
- [x] 1.2 Add Python dependency files for FastAPI, Uvicorn, SQLAlchemy, Pydantic and pytest
- [x] 1.3 Configure SQLite database connection and application settings
- [x] 1.4 Add FastAPI app entrypoint with health check endpoint
- [x] 1.5 Add test runner configuration for backend tests

## 2. Persistence Models

- [x] 2.1 Define SQLAlchemy models for Case, Element, Material, Task, Gap, Conflict and ConflictCheck
- [x] 2.2 Define SQLAlchemy models for ConversationEvent, Draft, ConfirmationDecision, FactVersion and TaskExecutionResult
- [x] 2.3 Add source event references, confirmation status, reviewer metadata and decision log fields
- [x] 2.4 Add idempotency keys for task results, material回写 and fact version triggers
- [x] 2.5 Implement database initialization for local SQLite development

## 3. API Schemas and Routers

- [x] 3.1 Define Pydantic schemas for cases, graph state, materials, tasks and fact versions
- [x] 3.2 Define Pydantic schemas for conversation messages, conversation events, drafts and confirmations
- [x] 3.3 Implement case and graph read APIs
- [x] 3.4 Implement conversation message ingest and event list APIs
- [x] 3.5 Implement draft list, confirm and reject APIs
- [x] 3.6 Implement task list, start, complete and block APIs
- [x] 3.7 Implement material list and material ingest APIs
- [x] 3.8 Implement `run-loop` API for local demo orchestration

## 4. Rule Engine and Graph Loop

- [x] 4.1 Implement material type to element mapping rules
- [x] 4.2 Implement universal gap generation rules
- [x] 4.3 Implement task dependency, priority and stage blocker rules
- [x] 4.4 Implement material入池 and element binding service
- [x] 4.5 Implement gap closure checks and element status recalculation
- [x] 4.6 Implement conflict candidate selection for new statement-material pairs
- [x] 4.7 Implement fact version trigger calculation and duplicate prevention

## 5. Conversation Task AI Backend Service

- [x] 5.1 Implement conversation message normalization for user,办案 Agent,笔录 Agent,系统 and审批 messages
- [x] 5.2 Implement event classification for task intent, material result, fact update, approval result and conflict clue
- [x] 5.3 Generate task drafts from task intent events with element binding and duplicate-task checks
- [x] 5.4 Generate fact update drafts from material result and审批 result events
- [x] 5.5 Generate material binding drafts from Agent回写 and material upload events
- [x] 5.6 Generate conflict review drafts from conversation events that mention inconsistent statements
- [x] 5.7 Persist AI outputs as pending confirmation records with original message references

## 6. Confirmation Wall Backend Service

- [x] 6.1 Implement confirm, modify-and-confirm and reject actions for AI-generated drafts
- [x] 6.2 On task draft confirmation, create active task center records
- [x] 6.3 On fact update confirmation, update element facts and trigger fact summary version evaluation
- [x] 6.4 On material binding confirmation, attach material to elements using task binding or material mapping rules
- [x] 6.5 On conflict review confirmation, create conflict records and linked P0复核 tasks
- [x] 6.6 Record every confirmation or rejection in ConfirmationDecision

## 7. Task-Driven AI Backend Service

- [x] 7.1 Implement task eligibility checks for dependencies, stage blockers, status and actor permissions
- [x] 7.2 Route笔录 tasks to mock笔录 Agent executor and handle completion callbacks
- [x] 7.3 Route文书生成 tasks to mock document generator and bind generated materials
- [x] 7.4 Route人工上传 tasks to民警 queue and wait for upload completion events
- [x] 7.5 Route审批 tasks to领导 queue and keep them pending until approval result arrives
- [x] 7.6 Mark blocked tasks with blocking dependency details and unblock them when materials or approvals arrive

## 8. Result回流 Loop

- [x] 8.1 Convert task completion results into material, approval, confirmation or status events
- [x] 8.2 Feed new materials through material入池, element mapping and gap closure checks
- [x] 8.3 Recalculate element statuses after every confirmed material or gap update
- [x] 8.4 Trigger conflict checks only for new eligible statement-material pairs
- [x] 8.5 Trigger fact summary generation only when the fact version trigger changes
- [x] 8.6 Complete tasks only after required result objects are persisted

## 9. Frontend API Integration

- [x] 9.1 Replace static task board data with backend task API data
- [x] 9.2 Replace static graph state with backend graph API data
- [x] 9.3 Show conversation-derived draft suggestions from backend in the chat timeline
- [x] 9.4 Wire confirm and reject UI actions to backend draft APIs
- [x] 9.5 Show material回写 results from backend in the材料抽屉
- [x] 9.6 Show违法事实 versions from backend fact version API

## 10. Verification

- [x] 10.1 Add backend tests for conversation event parsing and draft generation
- [x] 10.2 Add backend tests for duplicate task and duplicate material prevention
- [x] 10.3 Add backend tests for confirmation wall state transitions
- [x] 10.4 Add backend tests for task routing across Agent, system, human upload and leadership approval routes
- [x] 10.5 Add backend tests for task result回流 into graph status and fact version updates
- [x] 10.6 Run the FastAPI backend and manually verify the V5 prototype flow from固证完成 through发还清单 completion
