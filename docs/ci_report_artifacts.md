# CI Report Artifacts

This project uses GitHub Actions to run the core regression suite and publish
test report artifacts after every push, pull request, or manual workflow run.

## Artifacts

| Artifact | Contents | Interview value |
| --- | --- | --- |
| `ai-test-platform-reports` | Full `reports/` directory, including JUnit XML, Allure results, execution history, and generated report files. | Shows the platform keeps machine-readable test evidence. |
| `allure-html-report` | Static Allure HTML report generated from `reports/execution-plan-allure-results`. | Shows the platform can deliver human-readable automation reports in CI. |

## CI Flow

```text
pytest regression
  -> reports/ci-junit.xml
execution-plan demo
  -> reports/execution-plan-junit.xml
  -> reports/execution-plan-allure-results
Allure CLI generation
  -> reports/execution-plan-allure-report
artifact upload
  -> ai-test-platform-reports
  -> allure-html-report
```

## Local Equivalent

```powershell
.\.venv\Scripts\python.exe scripts\run_execution_plan.py `
  --scenario ui_login_smoke `
  --adapter browser `
  --dry-run `
  --junitxml reports\execution-plan-junit.xml `
  --allure-results reports\execution-plan-allure-results

.\.venv\Scripts\python.exe scripts\generate_allure_report.py `
  --results-dir reports\execution-plan-allure-results `
  --output-dir reports\execution-plan-allure-report `
  --json
```

If Allure CLI is not installed locally, `generate_allure_report.py` returns
`missing_cli`. In GitHub Actions, the workflow installs Java 17 and
`allure-commandline` before generating the HTML report.

## Interview Wording

```text
我在 CI 里不只是跑 pytest，还把执行计划结果导出为 JUnit XML 和 Allure results，
再生成 Allure HTML 报告并上传为 artifact。这样测试结果既能被机器消费，也能给
测试人员或面试官直接查看。
```
