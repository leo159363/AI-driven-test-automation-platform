<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getAutomationRuns, getAutomationScenarios, runAutomationScenario } from "../services/api";
import type { AutomationRunRecord, AutomationScenario } from "../types";

const scenarios = ref<AutomationScenario[]>([]);
const runs = ref<AutomationRunRecord[]>([]);
const selectedScenarioId = ref("");
const latestRun = ref<AutomationRunRecord | null>(null);
const running = ref(false);
const error = ref("");

const selectedScenario = computed(
  () =>
    scenarios.value.find((scenario) => scenario.scenario_id === selectedScenarioId.value) ??
    scenarios.value[0],
);

async function refreshRuns(): Promise<void> {
  runs.value = (await getAutomationRuns()).items;
}

async function runSelectedScenario(): Promise<void> {
  if (!selectedScenario.value) {
    return;
  }
  running.value = true;
  error.value = "";
  try {
    latestRun.value = await runAutomationScenario(selectedScenario.value.scenario_id);
    await refreshRuns();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    running.value = false;
  }
}

onMounted(async () => {
  try {
    const scenarioData = await getAutomationScenarios();
    scenarios.value = scenarioData.items;
    selectedScenarioId.value = scenarioData.items[0]?.scenario_id ?? "";
    await refreshRuns();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>自动化执行</h2>
        <p>选择内置 pytest 场景，触发后端执行并生成 JUnit / Allure 报告产物。</p>
      </div>
      <button class="primary-button" :disabled="running || !selectedScenario" @click="runSelectedScenario">
        {{ running ? "执行中..." : "执行选中场景" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">自动化场景加载失败：{{ error }}</div>

    <div class="split-layout">
      <div class="panel">
        <h3>执行场景</h3>
        <div class="stack">
          <article
            v-for="scenario in scenarios"
            :key="scenario.scenario_id"
            class="scenario-card"
            :class="{ selected: scenario.scenario_id === selectedScenarioId }"
            @click="selectedScenarioId = scenario.scenario_id"
          >
            <div class="item-title">
              <strong>{{ scenario.name }}</strong>
              <span class="status-pill ok">{{ scenario.category }}</span>
            </div>
            <p class="muted">{{ scenario.description }}</p>
            <div>
              <span v-for="label in scenario.labels" :key="label" class="tag">{{ label }}</span>
            </div>
          </article>
        </div>
      </div>

      <div class="panel">
        <h3>执行详情</h3>
        <template v-if="selectedScenario">
          <div class="item-title">
            <strong>{{ selectedScenario.name }}</strong>
            <span class="status-pill ok">{{ selectedScenario.category }}</span>
          </div>
          <p class="muted">{{ selectedScenario.description }}</p>
          <h3>pytest 目标</h3>
          <div class="stack">
            <span
              v-for="target in selectedScenario.pytest_targets"
              :key="target"
              class="path-text"
            >
              {{ target }}
            </span>
          </div>
          <h3>执行命令</h3>
          <pre class="code-block">{{ selectedScenario.runner_command }}</pre>
        </template>
      </div>

      <div class="panel">
        <h3>最新执行结果</h3>
        <template v-if="latestRun">
          <div class="item-title">
            <strong>{{ latestRun.run_id }}</strong>
            <span class="status-pill" :class="latestRun.status === 'passed' ? 'ok' : 'warn'">
              {{ latestRun.status }}
            </span>
          </div>
          <div class="metrics-grid compact-metrics">
            <div class="metric-card">
              <span>总数</span>
              <strong>{{ latestRun.summary?.total ?? "--" }}</strong>
            </div>
            <div class="metric-card">
              <span>通过</span>
              <strong>{{ latestRun.summary?.passed ?? "--" }}</strong>
            </div>
            <div class="metric-card">
              <span>失败</span>
              <strong>{{ latestRun.summary?.failed ?? "--" }}</strong>
            </div>
            <div class="metric-card">
              <span>耗时</span>
              <strong>{{ latestRun.duration_seconds }}s</strong>
            </div>
          </div>
          <h3>报告路径</h3>
          <pre class="code-block">{{ latestRun.paths.junitxml }}
{{ latestRun.paths.allure_results }}</pre>
        </template>
        <div v-else class="empty-state">点击执行后，这里会展示最新结果。</div>
      </div>
    </div>

    <div class="panel" style="margin-top: 14px;">
      <h3>执行历史</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>场景</th>
            <th>状态</th>
            <th>通过 / 总数</th>
            <th>JUnit</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.run_id">
            <td class="path-text">{{ run.run_id }}</td>
            <td>{{ run.scenario_name }}</td>
            <td>
              <span class="status-pill" :class="run.status === 'passed' ? 'ok' : 'warn'">
                {{ run.status }}
              </span>
            </td>
            <td>{{ run.summary?.passed ?? "--" }} / {{ run.summary?.total ?? "--" }}</td>
            <td class="path-text">{{ run.paths.junitxml }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="runs.length === 0" class="empty-state">暂无执行历史。</div>
    </div>
  </section>
</template>
