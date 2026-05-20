# QualityPilot 面试 Demo 说明

本文档用于面试现场演示“基于 MCP + RAG 的智能自动化测试平台”核心闭环。

## 1. 一条命令运行

```powershell
.\.venv\Scripts\python.exe scripts\run_qualitypilot_demo.py
```

默认输出目录：

```text
reports/qualitypilot-demo/
```

生成内容：

- `junit.xml`：自动化执行后的 JUnit XML 报告。
- `allure-results/`：Allure 兼容结果目录。
- `demo_summary.json`：完整链路 JSON 输出。
- `bug_report.md`：可复制到缺陷平台的 Bug 草稿。

## 2. Demo 做了什么

脚本会启动一个本地 HTTP stub 服务，模拟登录接口：

- 请求 `POST /api/login` 返回 HTTP 200。
- 响应体故意不返回 `token` 字段。
- 自动化断言 `assert text token` 因此失败。

之后平台会继续执行完整测试开发链路：

```text
RAG 上下文准备
  -> 测试用例生成
  -> API 自动化执行
  -> JUnit / Allure 报告生成
  -> 测试报告解析
  -> 失败用例查询
  -> 失败原因分析
  -> Bug 报告生成
```

## 3. 面试时怎么讲

可以这样介绍：

> 这个 Demo 不是只生成一段 AI 文本，而是把测试开发常见工作流串起来。平台先根据登录接口需求生成测试用例，然后用执行适配器调用接口并生成 JUnit / Allure 报告。报告失败后，MCP 工具会解析失败用例，结合 RAG 上下文判断失败原因，最后生成结构化 Bug 草稿。

重点强调：

- RAG 上下文不是为了炫技，而是给测试用例和失败分析提供需求、接口文档、历史缺陷等证据。
- MCP tools 把每个测试开发动作拆成可编排工具：生成用例、执行测试、解析报告、查询失败、分析失败、生成 Bug。
- pytest / JUnit / Allure 体现自动化测试平台的工程落地能力。
- 失败分析和 Bug 生成是规则兜底实现，不依赖外部 LLM Key，所以面试现场稳定可跑。

## 4. 关键输出怎么看

运行后控制台会输出类似：

```text
QualityPilot demo completed
run_id=api-api_login-xxxx
execution_status=failed
report_status=failed
failed_case_count=1
bug_count=1
junitxml=reports/qualitypilot-demo/junit.xml
allure_results=reports/qualitypilot-demo/allure-results
summary_json=reports/qualitypilot-demo/demo_summary.json
bug_report_md=reports/qualitypilot-demo/bug_report.md
```

其中：

- `execution_status=failed`：说明自动化测试真实执行失败。
- `report_status=failed`：说明 JUnit 报告被成功解析。
- `failed_case_count=1`：说明失败用例被筛选出来。
- `bug_count=1`：说明失败分析后生成了一个缺陷草稿。

## 5. 可以打开哪些文件

推荐按这个顺序展示：

1. `reports/qualitypilot-demo/junit.xml`
   - 说明平台能生成标准测试报告，CI/CD 和报告平台都能消费。

2. `reports/qualitypilot-demo/demo_summary.json`
   - 说明每个阶段都是结构化输出，不是散乱文本。

3. `reports/qualitypilot-demo/bug_report.md`
   - 说明平台能把失败结果转成缺陷报告草稿。

## 6. 面试官可能追问

### 这个失败是怎么来的？

本地 stub 登录接口返回了成功响应，但缺少需求要求的 `token` 字段，所以自动化断言失败。

### 为什么不直接用 LLM 判断失败原因？

当前版本先做规则兜底，因为面试 Demo 和 CI 要稳定。后续可以把 `analyze_failure` 升级为“规则初筛 + LLM 总结”，但即使没有 LLM Key，平台也能跑通。

### 这个和普通 pytest 有什么区别？

普通 pytest 主要解决“执行”。QualityPilot 把执行前后的测试开发动作也串起来：RAG 检索、用例生成、执行、报告解析、失败分析、Bug 草稿生成。

### Allure 是否完整集成？

当前阶段生成的是 Allure compatible results，并能发现结果目录。后续可以接 `allure generate` 输出 HTML 报告，但这不是当前 MVP 的重点。

### 这能写进简历吗？

可以写，但要准确：

```text
实现基于 MCP tools 的自动化测试闭环：支持测试上下文检索、用例生成、API 自动化执行、JUnit/Allure 报告解析、失败用例查询、失败原因分析和 Bug 草稿生成，并提供可运行的端到端 Demo 脚本。
```
## 7. Dashboard Visualization

The Dashboard now includes a `QualityPilot Demo` page for showing the command-line
demo artifacts in an interview-friendly UI.

Start the Dashboard:
```powershell
.\.venv\Scripts\python.exe scripts\start_dashboard.py --port 8501
```

The page shows:
- MCP workflow: `generate_test_cases -> run_api_tests -> get_test_report -> query_failed_cases -> analyze_failure -> generate_bug_report`.
- RAG contexts used by case generation and failure analysis.
- Generated test cases with dimensions, priorities, and suggested automation files.
- Failed cases parsed from JUnit XML.
- Failure analysis with root-cause type, confidence, and bug-candidate flag.
- Bug report draft as structured rows plus Markdown.

Interview demo order:
1. Run `scripts/run_qualitypilot_demo.py` to generate artifacts.
2. Open the Dashboard and choose `QualityPilot Demo`.
3. Explain the page from top to bottom, emphasizing that every stage has structured JSON output instead of only free-form AI text.

## 8. Allure HTML Report

Stage 32 adds static Allure HTML report generation on top of the existing
Allure-compatible result files.

After running the QualityPilot demo, generate the HTML report:

```powershell
.\.venv\Scripts\python.exe scripts\generate_allure_report.py
```

Default input and output:

```text
results_dir=reports/qualitypilot-demo/allure-results
output_dir=reports/qualitypilot-demo/allure-report
index_path=reports/qualitypilot-demo/allure-report/index.html
```

If the local machine does not have the Allure commandline installed, the script
returns `missing_cli`. This is expected and means the platform has generated
Allure-compatible results, but the external HTML generator is not available.

## 9. GitHub Actions Allure Artifact

Stage 33 makes CI generate and upload a static Allure HTML report.

In GitHub Actions, the workflow now:

1. Runs the core pytest regression and writes `reports/ci-junit.xml`.
2. Runs the execution-plan demo and writes `reports/execution-plan-allure-results`.
3. Installs Java 17 and Allure commandline.
4. Runs:

```bash
python scripts/generate_allure_report.py \
  --results-dir reports/execution-plan-allure-results \
  --output-dir reports/execution-plan-allure-report \
  --json
```

5. Uploads `reports/execution-plan-allure-report/` as the `allure-html-report`
artifact, and also keeps the full `reports/` folder as `ai-test-platform-reports`.

Interview wording:

```text
CI 会在每次 push/PR 后运行核心回归，生成 JUnit XML、Allure results 和 Allure HTML 报告，并把报告作为 GitHub Actions artifact 上传。这样项目不是只在本地跑 pytest，而是具备持续集成和报告交付能力。
```
