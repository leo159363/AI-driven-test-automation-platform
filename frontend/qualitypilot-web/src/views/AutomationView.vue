<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getAutomationScenarios } from "../services/api";
import type { AutomationScenario } from "../types";

const scenarios = ref<AutomationScenario[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    scenarios.value = (await getAutomationScenarios()).items;
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
        <p>当前阶段先展示可执行场景和命令，Stage 4 会接入后端执行接口。</p>
      </div>
      <button class="primary-button" disabled>执行选中场景</button>
    </div>

    <div v-if="error" class="error-banner">自动化场景加载失败：{{ error }}</div>

    <div class="stack">
      <article v-for="scenario in scenarios" :key="scenario.scenario_id" class="scenario-card">
        <div class="item-title">
          <strong>{{ scenario.name }}</strong>
          <span class="status-pill ok">{{ scenario.category }}</span>
        </div>
        <p class="muted">{{ scenario.description }}</p>
        <div>
          <span v-for="label in scenario.labels" :key="label" class="tag">{{ label }}</span>
        </div>
        <pre class="code-block">{{ scenario.runner_command }}</pre>
      </article>
    </div>
  </section>
</template>

