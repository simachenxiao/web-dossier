## Context

卷宗 V5 当前主要是静态前端原型和设计文档，尚无真实后端工程。现有设计已经描述了七要素图谱、材料入池、缺口任务、矛盾分析、违法事实版本推进，以及办案 Agent、笔录 Agent、任务中心、领导审批、民警上传和系统文书生成之间的协作关系。

本变更改为真实后端优先落地：使用 Python FastAPI 承载 API、服务编排和 AI 调用，使用 SQLite 作为本地演示和早期开发数据库。前端原型不再直接维护核心业务状态，而是通过后端 API 读取案件、任务、材料、图谱、对话事件、确认草稿和事实版本。

## Backend Architecture

```text
Frontend Prototype
  - chat timeline
  - task board
  - graph view
  - material drawer
  - fact version history
        |
        | HTTP JSON API
        v
FastAPI Backend
  - routers
  - services
  - AI orchestrators
  - rule engine
  - persistence repositories
        |
        v
SQLite Database
  - cases
  - elements
  - materials
  - tasks
  - gaps
  - conflicts
  - conflict_checks
  - conversation_events
  - drafts
  - confirmation_decisions
  - fact_versions
  - task_execution_results
```

## Backend Module Layout

```text
backend/
  app/
    main.py
    database.py

    models/
      case.py
      element.py
      material.py
      task.py
      gap.py
      conflict.py
      conversation.py
      draft.py
      confirmation.py
      fact_version.py
      execution_result.py

    schemas/
      case.py
      material.py
      task.py
      conversation.py
      draft.py
      confirmation.py
      graph.py
      fact_version.py

    routers/
      cases.py
      conversations.py
      drafts.py
      tasks.py
      materials.py
      graph.py
      confirmations.py
      fact_versions.py

    services/
      conversation_service.py
      confirmation_service.py
      task_center_service.py
      task_driver_service.py
      agent_dispatch_service.py
      material_service.py
      graph_engine_service.py
      conflict_service.py
      fact_version_service.py

    ai/
      conversation_task_ai.py
      task_driven_ai.py
      conflict_check_ai.py
      fact_summary_ai.py
      prompts/

    rules/
      material_element_mapping.py
      universal_gaps.py
      dependencies.py
      priorities.py
      stage_blockers.py

    tests/
```

## Goals / Non-Goals

**Goals:**

- 建立 FastAPI 后端作为案件状态、任务状态和推导结果的唯一服务端来源。
- 用 SQLite 持久化案件、七要素、材料、任务、缺口、矛盾、对话事件、AI 草稿、确认决策和事实版本。
- 将办案对话、Agent 消息、材料上传通知和审批反馈统一写入 `ConversationEvent`。
- 从 `ConversationEvent` 生成待确认的任务草稿、材料绑定草稿、事实更新草稿和矛盾复核草稿。
- 通过确认墙把 AI 输出转成正式 Task、Material 绑定、FactVersion 触发或 Conflict 记录。
- 以 Task Center 为主状态源，由 Task Driven AI/规则服务决定任务派发、阻塞、审批和完成。
- 任务完成结果统一回流为材料、审批、确认或状态事件，再触发图谱更新、缺口关闭、矛盾检查和事实版本推进。
- 为前端原型提供清晰 API，使 UI 从后端状态渲染，而不是直接从静态 JS 数据推导。

**Non-Goals:**

- 不在第一阶段接入正式生产数据库；SQLite 只用于本地演示和开发验证。
- 不在第一阶段实现真实外部 Agent 网络调用；笔录 Agent、办案 Agent 和系统文书生成先用后端 mock executor 表达边界。
- 不在第一阶段实现完整大模型生产调用；AI 模块先提供规则/假实现接口，保留后续替换为真实 LLM 的位置。
- 不让 AI 直接修改已确认事实、已确认材料关系或已确认矛盾记录。
- 不新增案由专属硬编码流程；案由差异仍由 AI 补充或后续模板增强。

## Decisions

1. 后端优先，前端只做展示和交互。

   核心业务状态必须由 FastAPI 后端维护，包括任务、材料、图谱、确认草稿和事实版本。前端只调用 API 展示数据和提交用户动作。

   替代方案是在 `卷宗V5.html` 中继续扩展内存状态。该方案适合演示，但无法支撑审计、幂等、确认墙和多端一致性。

2. SQLite 作为第一阶段数据库。

   SQLite 足够支撑单机演示、测试和快速迭代，降低部署成本。数据模型按关系型设计，后续迁移 PostgreSQL 时表结构和服务边界保持稳定。

   替代方案是直接上 PostgreSQL。该方案更接近生产，但会增加本地开发和演示门槛。

3. 使用 SQLAlchemy ORM + Pydantic schema。

   SQLAlchemy 负责持久化和关系建模，Pydantic 负责 API 输入输出契约。ORM model 和 API schema 分离，避免数据库字段直接泄漏到前端。

   替代方案是直接用 sqlite3。该方案依赖少，但后续表关系、测试和迁移成本更高。

4. 对话先转事件，再转草稿。

   原始消息不直接生成正式任务。后端先保存 `ConversationEvent`，再由 `ConversationTaskAI` 生成 `Draft`。Draft 必须确认后才产生正式业务状态。

   替代方案是把聊天消息直接写入任务中心。该方案无法支撑确认墙、决策日志和来源追溯。

5. 任务中心是任务状态唯一事实源。

   Agent 只能领取任务、提交结果或反馈阻塞原因，不能绕过 Task Center 直接推进案件阶段。任务驱动 AI 位于 Task Center 和 Agent Dispatch 之间，只做路由和调度决策。

   替代方案是由办案 Agent 内部维护流程状态。该方案会造成聊天、任务看板和图谱状态多源冲突。

6. AI 编排模块先定义接口，允许 mock 实现。

   第一阶段先把 AI 能力拆成可替换接口：`ConversationTaskAI`、`TaskDrivenAI`、`ConflictCheckAI`、`FactSummaryAI`。初版可使用规则/关键词实现，后续替换为真实 LLM 时不改变上层服务。

   替代方案是一开始直接接入 LLM。该方案更像最终效果，但会把业务建模、提示词、成本和异常处理耦合在一起。

7. 任务完成必须产生可回流结果。

   每个任务完成时必须至少产生一种结果：新材料、材料绑定、审批结论、人工确认结论、阻塞解除或案件状态更新。结果写入 `TaskExecutionResult` 后，统一进入材料入池和推导循环。

   替代方案是每种任务完成后各自更新页面状态。该方案会重复实现图谱重算、缺口关闭和事实推进逻辑。

## API Surface

第一阶段建议提供这些 API：

```text
POST   /api/cases
GET    /api/cases/{case_id}
GET    /api/cases/{case_id}/graph
GET    /api/cases/{case_id}/fact-versions

POST   /api/cases/{case_id}/conversations/messages
GET    /api/cases/{case_id}/conversations/events

GET    /api/cases/{case_id}/drafts
POST   /api/drafts/{draft_id}/confirm
POST   /api/drafts/{draft_id}/reject

GET    /api/cases/{case_id}/tasks
POST   /api/tasks/{task_id}/start
POST   /api/tasks/{task_id}/complete
POST   /api/tasks/{task_id}/block

GET    /api/cases/{case_id}/materials
POST   /api/cases/{case_id}/materials

POST   /api/cases/{case_id}/run-loop
```

`run-loop` 用于本地演示时手动触发一次推导循环：材料入池、缺口关闭、状态重算、任务驱动、事实版本判断。

## Risks / Trade-offs

- SQLite 不适合正式多人并发 → 第一阶段只定位本地演示；表结构保持可迁移，后续切 PostgreSQL。
- 后端工程会增加初始工作量 → 先做最小闭环 API，不一次性实现所有 UI 联动和真实 Agent。
- AI mock 与真实 LLM 行为可能不同 → AI 模块使用接口隔离，测试覆盖服务契约，不依赖具体模型输出。
- 任务、材料、事实版本重复生成 → 使用 `source_event_id`、`source_task_id`、`idempotency_key` 和 `fact_version_trigger` 做幂等。
- 业务状态跨模块流转复杂 → 坚持单向数据流：ConversationEvent → Draft → Confirmation → Task/Material/Fact/Conflict → Graph Loop。
