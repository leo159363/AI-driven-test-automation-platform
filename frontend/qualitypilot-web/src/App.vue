<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

const navItems = [
  { label: "首页", path: "/", icon: "home", group: "平台" },
  { label: "API 测试", path: "/api-testing", icon: "api", group: "测试工作台" },
  { label: "测试用例", path: "/test-cases", icon: "case", group: "测试工作台" },
  { label: "自动化执行", path: "/automation", icon: "run", group: "执行与报告" },
  { label: "测试报告", path: "/reports", icon: "report", group: "执行与报告" },
  { label: "AI 测试助手", path: "/assistant", icon: "ai", group: "AI 与知识库" },
  { label: "知识库管理", path: "/knowledge", icon: "kb", group: "AI 与知识库" },
];

const navGroups = computed(() => {
  const groups = new Map<string, typeof navItems>();
  for (const item of navItems) {
    groups.set(item.group, [...(groups.get(item.group) ?? []), item]);
  }
  return Array.from(groups.entries());
});

const tourSteps = [
  {
    title: "欢迎来到 QualityPilot",
    content: "这是一个测试开发平台原型。先看首页，再进入 API 测试、自动化执行、报告、知识库和 AI 助手。",
  },
  {
    title: "先从 API 测试开始",
    content: "API 测试页已经准备好登录成功、登录失败、文件上传成功和参数错误 4 个固定用例。",
  },
  {
    title: "再跑自动化和报告",
    content: "自动化执行页触发 pytest，测试报告页查看 JUnit / Allure 产物。",
  },
  {
    title: "最后讲 AI + RAG + MCP",
    content: "知识库和 AI 助手用于生成用例、失败分析和 Bug 报告，MCP tools 用于对接 Agent 工作流。",
  },
];

const tourIndex = ref(0);
const showTour = ref(false);

const currentTourStep = computed(() => tourSteps[tourIndex.value]);

function closeTour(): void {
  showTour.value = false;
  localStorage.setItem("qualitypilot-tour-dismissed", "true");
}

function nextTourStep(): void {
  if (tourIndex.value >= tourSteps.length - 1) {
    closeTour();
    return;
  }
  tourIndex.value += 1;
}

function previousTourStep(): void {
  tourIndex.value = Math.max(0, tourIndex.value - 1);
}

function restartTour(): void {
  tourIndex.value = 0;
  showTour.value = true;
}

onMounted(() => {
  showTour.value = localStorage.getItem("qualitypilot-tour-dismissed") !== "true";
});
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Q</div>
        <div>
          <strong>QualityPilot</strong>
          <span>AI 自动化测试平台</span>
        </div>
      </div>

      <nav class="nav-list">
        <div v-for="[group, items] in navGroups" :key="group" class="nav-group">
          <div class="nav-group-label">{{ group }}</div>
          <RouterLink
            v-for="item in items"
            :key="item.path"
            :to="item.path"
            class="nav-item"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
      </nav>

      <div class="sidebar-footer">
        <span>本地开发</span>
        <strong>Vue + FastAPI</strong>
      </div>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div class="topbar-left">
          <button class="topbar-icon" type="button" @click="restartTour">guide</button>
          <div class="project-selector">
            <span>当前项目</span>
            <strong>QualityPilot Demo</strong>
          </div>
          <label class="topbar-search">
            <span>search</span>
            <input placeholder="搜索接口、用例、报告" />
          </label>
        </div>
        <div class="topbar-actions">
          <span class="topbar-badge">MCP</span>
          <span class="topbar-badge">RAG</span>
          <span class="topbar-badge">pytest</span>
          <div class="user-avatar">QP</div>
        </div>
      </header>

      <RouterView />
    </main>

    <div v-if="showTour" class="tour-overlay">
      <div class="tour-popover">
        <button class="tour-close" type="button" @click="closeTour">×</button>
        <strong>{{ currentTourStep.title }}</strong>
        <p>{{ currentTourStep.content }}</p>
        <div class="tour-footer">
          <div class="tour-dots">
            <span
              v-for="(_, index) in tourSteps"
              :key="index"
              :class="{ active: index === tourIndex }"
            />
          </div>
          <div class="toolbar">
            <button class="ghost-button" :disabled="tourIndex === 0" @click="previousTourStep">上一步</button>
            <button class="primary-button" @click="nextTourStep">
              {{ tourIndex === tourSteps.length - 1 ? "开始使用" : "下一步" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
