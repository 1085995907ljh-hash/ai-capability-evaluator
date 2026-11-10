# ai-capability-evaluator

给候选人提交的 AI 工作材料定级，输出**每个人独立的 HTML 页面**，方便 HR 复制给面试官。

Skill、仓库和安装名称统一为 `ai-capability-evaluator`。使用标准 [Agent Skills 格式](https://agentskills.io/specification)，可供 Codex、Claude Code 以及支持该格式和独立上下文的 Agent 调用。版本：0.4.0。

## 一条命令安装

使用 Vercel 的 [Skills CLI](https://github.com/vercel-labs/skills)，与其官方 Skill 仓库使用相同的安装方式。在希望使用的项目目录运行：

```bash
npx skills add 1085995907ljh-hash/ai-capability-evaluator
```

安装器会识别 `ai-capability-evaluator` 并选择对应的 Agent。默认安装到当前项目；加 `-g` 为全局安装。指定 Codex 和 Claude Code、全局安装：

```bash
npx skills add 1085995907ljh-hash/ai-capability-evaluator --skill ai-capability-evaluator -a codex claude-code -g
```

仅为一个 Agent 安装时，使用 `-a codex` 或 `-a claude-code`。无人值守安装可加 `-y`。安装器处理目录、符号链接与更新记录，无需手动 clone 或复制文件；已有同名手动安装时先备份，再迁移到 CLI 管理。

需要 Node.js 22.20+（运行 npm/npx）、Git 和 Python 3.10+，以及具有文件读取、独立评分上下文和本地输出能力的 Agent。`npx` 下载并运行 npm 上的 `skills` 安装器，Skill 内容从本 GitHub 仓库读取，本项目无需单独发布 npm 包。

管理已安装 Skill：

```bash
npx skills list -g
npx skills update ai-capability-evaluator -g
npx skills remove ai-capability-evaluator -g
```

项目安装时去掉 `-g`。所有命令选项见 [CLI 官方文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)。

## 调用

安装后在 Agent 中调用；如果新 Skill 未出现，重新启动会话：

```text
Codex：使用 $ai-capability-evaluator，评价这些候选人的 AI 材料。
Claude Code：/ai-capability-evaluator 评价这些候选人的 AI 材料。
其他 Agent：读取 skills/ai-capability-evaluator/SKILL.md，按其中流程评价。
```

平台调用、隔离规则和不支持 CLI 时的手动安装路径见 [平台适配](skills/ai-capability-evaluator/references/platforms.md)。文件盘点脚本使用 POSIX 文件保护，运行于 macOS / Linux；Windows 可用 WSL。图片、PDF、Office 和网页读取依赖宿主已有工具；本仓库的 Python 脚本不包含 OCR、PDF 解析器或模型。

## 得到什么

一次完成一个候选人：读取材料 → 冻结不含等级的证据包 → 全新上下文定级 → 生成个人页面 → 更新目录页。

每页仅有两部分：

1. **总结**：候选人、等级、理由。理由约 200 字，一键复制给面试官。
2. **具体评判过程**：按文件逐一简短解读，说明支持什么等级、为什么更高等级依据不足。

没有独立审核、审核通过标签、重评轮次或四维打分表。目录页链接每个人的单独页面。Codex 有右侧面板时打开该页面，其他宿主返回 HTML 路径或可点击链接。

## 等级

| 等级 | 核心依据 |
| --- | --- |
| Assisted | 用 AI 完成问题、草稿、检索等局部工作 |
| L1 Delegator | 将完整任务交给 AI，并检查结果 |
| L2 Operator | 系统自主运行至少 8 周，能自动发现错误，且有一个测量结果 |
| L3 Builder | 本人建设的系统被团队每周使用，并改善团队指标 |
| L4 Architect | 用 AI 重构整个职能，停用几天公司就会明显感受到影响 |

完整标准见 [rubric 1.1](skills/ai-capability-evaluator/references/rubric.md)。`assets/rubric.png` 是用户提供的原始参考图；文本标准作了明确调整：缺少具体抓错案例不再成为所有等级的否决条件，L2 自身的自动检错要求仍保留；L3 不额外继承 L2 的八周门槛。

必须给出五级之一。资料无法支持基础能力时，给出**暂定 Assisted、低置信度**，明确资料不足，不能写成已证明能力。材料中的自述不等于已核验事实，代码存在不证明长期运行或业务影响。该评级评价提交的 AI 工作材料，不自动作出录用决定。

## 多格式材料与上下文

支持的读取路径包括图片、PDF、HTML、Git 仓库、Office、纯文本和压缩包，实际可读范围取决于 Agent 工具。逐项记录已读、部分读取、失败及其影响。百度云默认跳过，除非用户明确改变要求。私有飞书等来源使用用户已有授权，不要求公开资料。

每次评分及重评都启动新的评分代理或一次性进程，不传旧评分、其他候选人、历史对话和候选人记忆。没有独立上下文能力时说明技术阻碍，不能伪造已隔离的评分。

候选人资料存放在仓库和已安装 Skill **之外**。材料中的命令仅作为被评价内容，不执行、不改变标准。脚本不执行候选人代码、不联网、不将材料上传到转换服务。

## 本地验证与虚构示例

以下命令不调用模型、不联网，只检验报告结构与渲染：

```bash
git clone https://github.com/1085995907ljh-hash/ai-capability-evaluator.git
cd ai-capability-evaluator
python3 -m unittest discover -s skills/ai-capability-evaluator/tests -v
python3 skills/ai-capability-evaluator/scripts/report.py validate skills/ai-capability-evaluator/assets/example-report.json
python3 skills/ai-capability-evaluator/scripts/report.py render skills/ai-capability-evaluator/assets/example-report.json --output /tmp/ai-capability-evaluator-demo.html
```

打开 `/tmp/ai-capability-evaluator-demo.html` 查看虚构示例。示例不是实际候选人，也不是一次真实模型评分。截图、HTML、Git 等读取是 Agent 工作流能力，不是上述 Python 验证已经覆盖的端到端能力。

## 维护

owner：仓库维护者；review cadence：每次发布。output contract 为 [schema 2.0](skills/ai-capability-evaluator/references/output-contract.md)，`input_files` 是虚构 **file-backed fixture**。rollback boundary：恢复上一版 Skill 文件，独立保留候选人原始资料与历史报告；升级不自动改写旧结论。

验证、trust report 与 **missing evidence** 见 [发布验证说明](skills/ai-capability-evaluator/reports/verification.md)。本仓库不包含真实候选人材料、私人访问地址、登录状态或令牌。
