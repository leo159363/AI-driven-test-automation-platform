<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getLatestReport } from "../services/api";
import type { LatestReportResponse } from "../types";

const data = ref<LatestReportResponse | null>(null);
const error = ref("");

onMounted(async () => {
  try {
    data.value = await getLatestReport();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>测试报告</h2>
        <p>展示 JUnit XML、Allure results 和 Allure HTML report 的发现结果。</p>
      </div>
    </div>

    <div v-if="error" class="error-banner">报告加载失败：{{ error }}</div>

    <div v-if="data?.summary" class="metrics-grid">
      <div class="metric-card">
        <span>总数</span>
        <strong>{{ data.summary.total }}</strong>
      </div>
      <div class="metric-card">
        <span>通过</span>
        <strong>{{ data.summary.passed }}</strong>
      </div>
      <div class="metric-card">
        <span>失败</span>
        <strong>{{ data.summary.failed }}</strong>
      </div>
      <div class="metric-card">
        <span>跳过</span>
        <strong>{{ data.summary.skipped }}</strong>
      </div>
    </div>

    <div v-if="data?.warning" class="error-banner">{{ data.warning }}</div>

    <div class="panel">
      <h3>报告产物</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>类型</th>
            <th>路径</th>
            <th>状态</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="artifact in data?.artifacts ?? []" :key="artifact.path">
            <td>{{ artifact.label }}</td>
            <td class="path-text">{{ artifact.relative_path }}</td>
            <td>
              <span class="status-pill" :class="artifact.exists ? 'ok' : 'warn'">
                {{ artifact.exists ? "已发现" : "未生成" }}
              </span>
            </td>
            <td>{{ artifact.detail }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

