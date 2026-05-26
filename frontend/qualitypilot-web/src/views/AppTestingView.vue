<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getAppTestScripts, runAppTestScript } from "../services/api";
import type { AppTestScript, PlatformRunRecord } from "../types";

const scripts = ref<AppTestScript[]>([]);
const selectedScriptId = ref("");
const error = ref("");
const loading = ref(false);
const runRecord = ref<PlatformRunRecord | null>(null);

const selectedScript = computed(
  () => scripts.value.find((item) => item.script_id === selectedScriptId.value) ?? scripts.value[0],
);

onMounted(async () => {
  try {
    const data = await getAppTestScripts();
    scripts.value = data.items;
    selectedScriptId.value = data.items[0]?.script_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});

async function submitRunScript(): Promise<void> {
  if (!selectedScript.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    runRecord.value = await runAppTestScript(selectedScript.value.script_id);
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
        <h2>App 测试</h2>
        <p>当前先做移动端接口契约和兼容性场景设计，后续可扩展 Appium / 真机云。</p>
      </div>
      <button class="primary-button" :disabled="!selectedScript || loading" @click="submitRunScript">
        {{ loading ? "运行中..." : "运行契约检查" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">App 测试模块加载失败：{{ error }}</div>

    <div class="two-column">
      <aside class="panel">
        <h3>App 场景</h3>
        <div class="stack">
          <button
            v-for="script in scripts"
            :key="script.script_id"
            class="template-button"
            :class="{ active: script.script_id === selectedScript?.script_id }"
            type="button"
            @click="selectedScriptId = script.script_id"
          >
            <strong>{{ script.name }}</strong>
            <span>{{ script.platform }} / {{ script.priority }}</span>
          </button>
        </div>
      </aside>

      <main class="panel">
        <template v-if="selectedScript">
          <div class="item-title">
            <h3>{{ selectedScript.name }}</h3>
            <span class="tag">{{ selectedScript.status }}</span>
          </div>
          <p>{{ selectedScript.scope }}</p>
          <h3>步骤</h3>
          <ol class="number-list">
            <li v-for="step in selectedScript.steps" :key="step">{{ step }}</li>
          </ol>
          <h3>断言</h3>
          <span v-for="assertion in selectedScript.assertions" :key="assertion" class="tag">
            {{ assertion }}
          </span>
          <h3>AI 能力</h3>
          <p class="muted">{{ selectedScript.ai_capability }}</p>
          <template v-if="runRecord">
            <h3>执行结果</h3>
            <span class="status-pill ok">{{ runRecord.status }}</span>
            <pre class="mini-code">{{ runRecord.command }}</pre>
          </template>
        </template>
      </main>
    </div>
  </section>
</template>
