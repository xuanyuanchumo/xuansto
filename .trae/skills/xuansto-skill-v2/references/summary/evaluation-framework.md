# 验证评估框架

## Core Points
- 参照ECC的eval模式建立多维度质量评估体系
- pass@k指标：k次尝试中至少一次成功的概率，pass@1=70%/pass@3=91%/pass@5=97%
- pass^k指标：k次尝试全部成功(一致性要求)，用于需要稳定输出的场景
- 检查点评估：每个工作流阶段设置质量检查点，评估通过率和一致性

## Applicable Scenarios
- Quality Monitor Agent度量项目质量指标
- 评估Agent输出质量和一致性
- 设计质量门禁的通过标准
