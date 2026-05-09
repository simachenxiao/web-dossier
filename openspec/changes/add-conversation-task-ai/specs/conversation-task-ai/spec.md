## ADDED Requirements

### Requirement: Parse conversation into auditable events
The system SHALL parse办案对话、Agent消息、材料上传通知 and审批反馈 into structured conversation events before creating tasks or updating case facts.

#### Scenario: Agent message references a generated transcript task
- **WHEN** 笔录 Agent sends a message indicating that 李江《询问笔录》 has been completed
- **THEN** the system records a conversation event with the original message, source role, event type, related material title, related person, and timestamp

#### Scenario: User message requests a follow-up task
- **WHEN** a民警 sends a message asking the system to补齐医院诊断证明
- **THEN** the system records a conversation event with event type `task_intent` and preserves the original user text as evidence for later confirmation

### Requirement: Generate task drafts from conversation events
The system SHALL generate task drafts from conversation events when the event implies a new action that is not already covered by an open or completed task.

#### Scenario: Missing material is mentioned in conversation
- **WHEN** a conversation event indicates that 医院诊断证明 is missing and no active task exists for that material
- **THEN** the system creates a task draft bound to the后果 element with expected material 医院诊断证明 and status `pending_confirmation`

#### Scenario: Duplicate task already exists
- **WHEN** a conversation event requests 补齐烟灰缸证据保全材料 and an active task already expects 证据保全决定书、证据保全清单 or 证据保全审批表
- **THEN** the system does not create a duplicate task draft and links the conversation event to the existing task

### Requirement: Generate fact update drafts from conversation events
The system SHALL generate fact update drafts when conversation events contain new case facts from completed tasks, uploaded materials, Agent回写 or审批结论.

#### Scenario: Diagnosis material updates injury result
- **WHEN** a conversation event states that医院诊断证明 has been uploaded and confirms 头皮挫裂伤
- **THEN** the system creates a fact update draft for the后果 element and marks it as requiring confirmation before the违法事实版本 advances

#### Scenario: Punishment decision updates result
- **WHEN** a conversation event indicates that行政处罚决定书 has been confirmed
- **THEN** the system creates a fact update draft for处罚结果 and keeps it separate from confirmed fact summary until办案人 confirmation

### Requirement: Route AI extracted outputs through confirmation wall
The system SHALL keep AI-extracted task drafts, fact update drafts, material binding drafts and conflict review drafts inactive until confirmed by an authorized user.

#### Scenario: User confirms a task draft
- **WHEN** 办案人 confirms an AI-generated task draft for上传医院诊断证明
- **THEN** the system creates an active task in the task center and records the confirmation decision with the original conversation event reference

#### Scenario: User rejects a fact update draft
- **WHEN** 办案人 rejects an AI-generated fact update draft
- **THEN** the system does not update the element facts, does not advance the fact version, and records the rejection reason

### Requirement: Link conversation outputs to graph and material context
The system SHALL associate every generated draft with relevant case elements, materials, tasks, and source conversation events when such context is available.

#### Scenario: Transcript completion message links to victim element
- **WHEN** a completion message references 李江《询问笔录》
- **THEN** the system links the generated material draft to the受害人、工具/手段 and后果 elements according to task binding or material mapping rules

#### Scenario: Conflict clue appears in conversation
- **WHEN** a conversation event says 周枫自书描述与李江笔录不一致
- **THEN** the system creates a conflict review draft linked to the relevant materials and element instead of directly marking the element as conflict
