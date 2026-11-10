# ailevel-judgement

给候选人提交的 AI 工作材料定级，输出**每个人独立的 HTML 页面**，方便 HR 复制给面试官。

Skill 名称是 `ai-capability-evaluator`，仓库名称是 `ailevel-judgement`。使用标准 [Agent Skills 格式](https://agentskills.io/specification)，可供 Codex、Claude Code 以及支持该格式和独立上下文的 Agent 调用。版本：0.4.0。

## 安装

需要 Git、Python 3.10+，以及具有文件读取、独立评分上下文和本地输出能力的 Agent。文件盘点脚本使用 POSIX 文件保护，运行于 macOS / Linux；Windows 可用 WSL。图片、PDF、Office 和网页的读取依赖宿主已有工具；本仓库的 Python 脚本不包含 OCR、PDF 解析器或模型。

```bash
git clone https://github.com/1085995907ljh-hash/ailevel-judgement.git
cd ailevel-judgement
```

将 `skills/ai-capability-evaluator` **整个文件夹**复制到对应位置，已有同名安装时先备份再更新：

| Agent | 用户安装位置 | 当前项目安装位置 |
| --- | --- | --- |
| Codex | `~/.agents/skills/ai-capability-evaluator/` | `.agents/skills/ai-capability-evaluator/` |
| Claude Code | `~/.claude/skills/ai-capability-evaluator/` | `.claude/skills/ai-capability-evaluator/` |
| 其他 Agent | 其 Agent Skills 搜索目录 | 或直接让 Agent 读取完整 `SKILL.md` 并解析相对引用 |

例如，首次安装到 Claude Code：

```bash
mkdir -p ~/.claude/skills
test -e ~/.claude/skills/ai-capability-evaluator || cp -R skills/ai-capability-evaluator ~/.claude/skills/
```

首次安装到 Codex：

```bash
mkdir -p ~/.agents/skills
test -e ~/.agents/skills/ai-capability-evaluator || cp -R skills/ai-capability-evaluator ~/.agents/skills/
```

命令遇到已有同名目录会保留原安装。Codex 路径依据[官方说明](https://learn.chatgpt.com/docs/build-skills)；部分旧版或桌面环境仍使用 `~/.codex/skills`，应遵循该宿主实际配置，避免同名重复安装。重新启动宿主会话后调用：

```text
Codex：使用 $ai-capability-evaluator，评价这些候选人的 AI 材料。
Claude Code：/ai-capability-evaluator 评价这些候选人的 AI 材料。
其他 Agent：读取 skills/ai-capability-evaluator/SKILL.md，按其中流程评价。
```

平台调用与隔离规则见 [平台适配](skills/ai-capability-evaluator/references/platforms.md)。Claude 安装目录依据[官方说明](https://code.claude.com/docs/en/skills)。

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
python3 -m unittest discover -s skills/ai-capability-evaluator/tests -v
python3 skills/ai-capability-evaluator/scripts/report.py validate skills/ai-capability-evaluator/assets/example-report.json
python3 skills/ai-capability-evaluator/scripts/report.py render skills/ai-capability-evaluator/assets/example-report.json --output /tmp/ailevel-demo.html
```

打开 `/tmp/ailevel-demo.html` 查看虚构示例。示例不是实际候选人，也不是一次真实模型评分。截图、HTML、Git 等读取是 Agent 工作流能力，不是上述 Python 验证已经覆盖的端到端能力。

## 维护

owner：仓库维护者；review cadence：每次发布。output contract 为 [schema 2.0](skills/ai-capability-evaluator/references/output-contract.md)，`input_files` 是虚构 **file-backed fixture**。rollback boundary：恢复上一版 Skill 文件，独立保留候选人原始资料与历史报告；升级不自动改写旧结论。

验证、trust report 与 **missing evidence** 见 [发布验证说明](skills/ai-capability-evaluator/reports/verification.md)。本仓库不包含真实候选人材料、私人访问地址、登录状态或令牌。
