<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getCicdJobs } from "../services/api";
import type { CicdJob } from "../types";

const jobs = ref<CicdJob[]>([]);
const selectedJobId = ref("");
const error = ref("");

const selectedJob = computed(() => jobs.value.find((item) => item.job_id === selectedJobId.value) ?? jobs.value[0]);

onMounted(async () => {
  try {
    const data = await getCicdJobs();
    jobs.value = data.items;
    selectedJobId.value = data.items[0]?.job_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>CI/CD 与定时任务</h2>
        <p>把 ruff、pytest、自动化执行、Allure 产物和 AI 失败分析串成质量门禁。</p>
      </div>
      <button class="primary-button">新建定时任务</button>
    </div>

    <div v-if="error" class="error-banner">CI/CD 模块加载失败：{{ error }}</div>

    <div class="two-column">
      <aside class="panel">
        <h3>流水线</h3>
        <div class="stack">
          <button
            v-for="job in jobs"
            :key="job.job_id"
            class="template-button"
            :class="{ active: job.job_id === selectedJob?.job_id }"
            type="button"
            @click="selectedJobId = job.job_id"
          >
            <strong>{{ job.name }}</strong>
            <span>{{ job.trigger }} / {{ job.status }}</span>
          </button>
        </div>
      </aside>

      <main class="panel">
        <template v-if="selectedJob">
          <div class="item-title">
            <h3>{{ selectedJob.name }}</h3>
            <span class="tag">{{ selectedJob.trigger }}</span>
          </div>
          <h3>执行阶段</h3>
          <div class="flow-list">
            <div v-for="stage in selectedJob.stages" :key="stage" class="flow-step">{{ stage }}</div>
          </div>
          <h3>质量门禁</h3>
          <p>{{ selectedJob.quality_gate }}</p>
          <h3>命令</h3>
          <pre class="code-block">{{ selectedJob.command }}</pre>
        </template>
      </main>
    </div>
  </section>
</template>
