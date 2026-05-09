## ADDED Requirements

### Requirement: Drive execution from task center state
The system SHALL use task center records as the only source for deciding which Agent, system module, approver, or human actor should handle a task.

#### Scenario: Victim transcript task becomes actionable
- **WHEN** the任务中心 has a pending 制作受害人笔录 task with all dependencies satisfied
- **THEN** the task-driven AI assigns the task to 笔录 Agent and changes the task status to `in_progress`

#### Scenario: Task dependency is not satisfied
- **WHEN** a 嫌疑人供述 task requires 传唤证 and no confirmed 传唤证 material exists
- **THEN** the task-driven AI keeps the task blocked and records 传唤证 as the blocking dependency

### Requirement: Select execution route by task type
The system SHALL select the execution route for each task based on task type, bound element, dependencies, and required actor.

#### Scenario: Administrative filing task requires approval
- **WHEN** an 行政立案 task is created
- **THEN** the system generates 行政立案登记表、行政立案告知书 and 接报审批表, then routes the task to领导 with status `pending_approval`

#### Scenario: Evidence preservation task is system executable
- **WHEN** an 开具证据保全材料 task is active and the case contains a tool requiring preservation
- **THEN** the system generates 证据保全决定书、证据保全清单 and 证据保全审批表, then marks the task completed after material creation succeeds

#### Scenario: Diagnosis upload task requires human action
- **WHEN** an 上传医院诊断证明 task is active
- **THEN** the task-driven AI routes the task to民警 and waits for a material upload result before completing the task

### Requirement: Feed task results back into the dossier loop
The system SHALL convert completed task results into material, approval, confirmation, or status events and feed them into the existing graph update loop.

#### Scenario: Transcript task returns material
- **WHEN** 笔录 Agent completes 李江《询问笔录》 and returns the material metadata
- **THEN** the system adds the material to the evidence pool, closes matching gaps, recalculates element status, and evaluates whether the违法事实版本 can advance

#### Scenario: Punishment task is confirmed
- **WHEN** 人工 confirms the generated 行政处罚决定书、行政处罚告知笔录 and 行政处罚审批表
- **THEN** the system completes the行政处罚 task and emits a fact update candidate for处罚结果

### Requirement: Enforce idempotency across repeated task triggers
The system SHALL prevent repeated Agent messages, repeated material uploads, or repeated task status notifications from creating duplicate tasks, duplicate materials, or duplicate fact versions.

#### Scenario: Same Agent completion is received twice
- **WHEN** the task center receives the same 笔录 Agent completion callback twice for task T-003
- **THEN** the system keeps one completed task result and one material record linked to that task

#### Scenario: Same fact state is recalculated twice
- **WHEN** graph recalculation produces the same fact version trigger hash as the current case
- **THEN** the system does not create a new违法事实版本

### Requirement: Surface task-driven actions in UI
The system SHALL expose task-driven AI actions in the chat timeline, task board, graph node detail, material drawer and fact version history using the same underlying task and material records.

#### Scenario: AI creates a follow-up task
- **WHEN** the task-driven AI creates a confirmed follow-up task for补齐伤情检查结论
- **THEN** the chat timeline shows the action, the task board shows the task, and the后果 graph node shows the corresponding gap

#### Scenario: Task completion updates graph
- **WHEN** an evidence preservation task completes
- **THEN** the task board marks it completed, the material drawer lists generated preservation documents, and the工具/手段 graph node reflects the updated material count and status

### Requirement: Respect confirmation and approval boundaries
The system SHALL distinguish automatic task execution, user confirmation, and leadership approval, and MUST NOT treat one boundary as a substitute for another.

#### Scenario: AI suggests a conflict task
- **WHEN** AI detects a possible contradiction between 李江询问笔录 and 周枫自书
- **THEN** the system creates a pending confirmation conflict draft and does not create a P0 conflict task until办案人 confirms it

#### Scenario: Approval task is not auto-approved
- **WHEN** the system generates administrative filing documents
- **THEN** the task remains pending leadership approval and cannot be completed by task-driven AI alone
