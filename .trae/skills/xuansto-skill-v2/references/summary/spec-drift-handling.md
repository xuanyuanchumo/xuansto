# 规格漂移处理（Spec Drift Handling）

## Core Points
- 规格漂移(Spec Drift)是SDD流程中实现与规格文档不一致的偏差
- 三级处理流程：Level 1(轻微漂移/自动修正)→Level 2(中度漂移/需确认)→Level 3(严重漂移/需审批)
- SPEC-CONSISTENCY质量门禁检测规格一致性，漂移未处理则门禁不通过
- 标记规范：代码中标记漂移位置和等级，规格文档中记录偏差原因和处理结果

## Applicable Scenarios
- Specification Keeper Agent检测和处理规格漂移
- quality_gate_check门禁检查规格一致性
- SDD流程中实现与规格偏差的管理
