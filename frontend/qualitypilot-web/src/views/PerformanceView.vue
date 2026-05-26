<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getPerformanceScenarios, runPerformanceScenario } from "../services/api";
import type { PerformanceScenario, PlatformRunRecord } from "../types";

const scenarios = ref<PerformanceScenario[]>([]);
const selectedScenarioId = ref("");
const error = ref("");
const loading = ref(false);
const runRecord = ref<PlatformRunRecord | null>(null);

const selectedScenario = computed(
  () => scenarios.value.find((item) => item.scenario_id === selectedScenarioId.value) ?? scenarios.value[0],
);

onMounted(async () => {
  try {
    const data = await getPerformanceScenarios();
    scenarios.value = data.items;
    selectedScenarioId.value = data.items[0]?.scenario_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});

async function submitRunScenario(): Promise<void> {
  if (!selectedScenario.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    runRecord.value = await runPerformanceScenario(selectedScenario.value.scenario_id);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>性能测试</h2>
        <p>参考 Locust 压测模块，展示并发、阶梯压测、核心指标和风险分析。</p>
      </div>
      <button class="primary-button" :disabled="!selectedScenario || loading" @click="submitRunScenario">
        {{ loading ? "启动中..." : "启动压测" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">性能测试模块加载失败：{{ error }}</div>

    <div class="split-layout">
      <aside class="panel">
        <h3>压测场景</h3>
        <div class="stack">
          <button
            v-for="scenario in scenarios"
            :key="scenario.scenario_id"
            class="template-button"
            :class="{ active: scenario.scenario_id === selectedScenario?.scenario_id }"
            type="button"
            @click="selectedScenarioId = scenario.scenario_id"
          >
            <strong>{{ scenario.name }}</strong>
            <span>{{ scenario.module }} / {{ scenario.tool }} / {{ scenario.status }}</span>
          </button>
        </div>
      </aside>

      <main class="panel">
        <template v-if="selectedScenario">
          <div class="item-title">
            <h3>{{ selectedScenario.name }}</h3>
            <span class="status-pill ok">{{ selectedScenario.tool }}</span>
          </div>
          <div class="metrics-grid compact-metrics">
            <div class="metric-card">
              <span>并发用户</span>
              <strong>{{ selectedScenario.users }}</strong>
            </div>
            <div class="metric-card">
              <span>启动速率</span>
              <strong>{{ selectedScenario.spawn_rate }}/s</strong>
            </div>
            <div class="metric-card">
              <span>持续时间</span>
              <strong>{{ selectedScenario.duration }}</strong>
            </div>
            <div class="metric-card">
              <span>目标接口</span>
              <strong>{{ selectedScenario.target }}</strong>
            </div>
          </div>

          <h3>指标快照</h3>
          <table class="data-table">
            <tbody>
              <tr v-for="(value, key) in selectedScenario.metrics" :key="key">
                <td>{{ key }}</td>
                <td>{{ value }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </main>

      <aside class="panel">
        <h3>风险与命令</h3>
        <template v-if="selectedScenario">
          <p>{{ selectedScenario.risk }}</p>
          <pre class="code-block">{{ selectedScenario.command }}</pre>
          <template v-if="runRecord">
            <h3>运行结果</h3>
            <span class="status-pill ok">{{ runRecord.status }}</span>
            <pre class="mini-code">{{ JSON.stringify(runRecord.metrics, null, 2) }}</pre>
          </template>
          <p class="muted">面试时可以讲：性能测试不只看平均耗时，还要看 p95、错误率、吞吐和瓶颈定位。</p>
        </template>
      </aside>
    </div>
  </section>
</template>
