<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { globalSearch, sendCopilotMessage } from "./services/api";

interface MenuChild {
  label: string;
  path: string;
}

interface MenuItem {
  label: string;
  path?: string;
  icon: string;
  children?: MenuChild[];
}

const collapsed = ref(false);
const openGroups = ref<string[]>(["接口测试", "性能测试"]);
const searchKeyword = ref("");
const searchResults = ref<Array<{ type: string; title: string; path: string; description: string }>>([]);
const showSearchResults = ref(false);
const copilotOpen = ref(false);
const copilotInput = ref("帮我创建登录接口回归测试并分析失败风险");
const copilotAnswer = ref("");
const copilotOperations = ref<Array<Record<string, string>>>([]);
const copilotLoading = ref(false);

const menuItems: MenuItem[] = [
  { label: "首页", path: "/", icon: "⌂" },
  {
    label: "接口测试",
    icon: "⌁",
    children: [
      { label: "工作台", path: "/api-testing" },
      { label: "用例管理", path: "/test-cases" },
      { label: "环境配置", path: "/settings" },
    ],
  },
  {
    label: "Web测试",
    icon: "◎",
    children: [{ label: "脚本管理", path: "/web-testing" }],
  },
  {
    label: "APP测试",
    icon: "▯",
    children: [{ label: "脚本管理", path: "/app-testing" }],
  },
  {
    label: "性能测试",
    icon: "⚡",
    children: [
      { label: "场景管理", path: "/performance" },
      { label: "实时监控", path: "/performance" },
      { label: "结果分析", path: "/reports" },
    ],
  },
  { label: "测试报告", path: "/reports", icon: "▥" },
  { label: "CI/CD与定时任务", path: "/cicd", icon: "⌘" },
  { label: "测试文档", path: "/documents", icon: "▤" },
  {
    label: "AI 与知识库",
    icon: "AI",
    children: [
      { label: "AI 测试助手", path: "/assistant" },
      { label: "知识库管理", path: "/knowledge" },
    ],
  },
  { label: "系统设置", path: "/settings", icon: "⚙" },
];

const tourSteps = [
  {
    title: "欢迎来到 QualityPilot",
    content: "这是一个面向测试开发的自动化测试平台，布局参考常见测试平台工作台。",
  },
  {
    title: "先从接口测试开始",
    content: "进入接口测试 / 工作台，选择登录或上传用例，直接发送 Mock 请求。",
  },
  {
    title: "再看自动化和报告",
    content: "测试报告、CI/CD、Web 测试和性能测试用于展示测试开发完整能力。",
  },
  {
    title: "最后讲 AI + RAG + MCP",
    content: "AI 助手和知识库是你的差异化，不是单纯仿照别人的测试管理平台。",
  },
];

const tourIndex = ref(0);
const showTour = ref(false);

const currentTourStep = computed(() => tourSteps[tourIndex.value]);

function toggleGroup(label: string): void {
  if (collapsed.value) {
    collapsed.value = false;
  }
  openGroups.value = openGroups.value.includes(label)
    ? openGroups.value.filter((item) => item !== label)
    : [...openGroups.value, label];
}

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

async function submitGlobalSearch(): Promise<void> {
  if (!searchKeyword.value.trim()) {
    searchResults.value = [];
    showSearchResults.value = false;
    return;
  }
  const data = await globalSearch(searchKeyword.value);
  searchResults.value = data.items;
  showSearchResults.value = true;
}

async function submitCopilot(): Promise<void> {
  if (!copilotInput.value.trim()) {
    return;
  }
  copilotLoading.value = true;
  try {
    const data = await sendCopilotMessage(copilotInput.value);
    copilotAnswer.value = data.answer;
    copilotOperations.value = data.operations;
  } finally {
    copilotLoading.value = false;
  }
}

onMounted(() => {
  showTour.value = localStorage.getItem("qualitypilot-tour-dismissed") !== "true";
});
</script>

<template>
  <div class="fst-shell" :class="{ collapsed }">
    <aside class="fst-sidebar">
      <div class="fst-logo">
        <div class="fst-logo-mark">Q</div>
        <strong v-if="!collapsed">QualityPilot</strong>
      </div>

      <nav class="fst-menu">
        <template v-for="item in menuItems" :key="item.label">
          <RouterLink
            v-if="item.path"
            :to="item.path"
            class="fst-menu-item"
            :title="item.label"
          >
            <span class="fst-menu-icon">{{ item.icon }}</span>
            <span v-if="!collapsed">{{ item.label }}</span>
          </RouterLink>

          <div v-else class="fst-submenu">
            <button class="fst-menu-item fst-submenu-title" type="button" @click="toggleGroup(item.label)">
              <span class="fst-menu-icon">{{ item.icon }}</span>
              <span v-if="!collapsed">{{ item.label }}</span>
              <span v-if="!collapsed" class="fst-caret">
                {{ openGroups.includes(item.label) ? "⌃" : "⌄" }}
              </span>
            </button>
            <div v-if="!collapsed && openGroups.includes(item.label)" class="fst-submenu-list">
              <RouterLink
                v-for="child in item.children"
                :key="child.path + child.label"
                :to="child.path"
                class="fst-submenu-link"
              >
                {{ child.label }}
              </RouterLink>
            </div>
          </div>
        </template>
      </nav>
    </aside>

    <main class="fst-main">
      <header class="fst-header">
        <div class="fst-header-left">
          <button class="fst-icon-button" type="button" @click="collapsed = !collapsed">
            {{ collapsed ? "☰" : "☷" }}
          </button>
          <select class="fst-project-select" value="qualitypilot-demo">
            <option value="qualitypilot-demo">QualityPilot Demo</option>
          </select>
          <label class="fst-global-search">
            <span>⌕</span>
            <input
              v-model="searchKeyword"
              placeholder="搜索接口、用例、报告、文档"
              @focus="showSearchResults = searchResults.length > 0"
              @keydown.enter="submitGlobalSearch"
            />
          </label>
          <div v-if="showSearchResults" class="fst-search-popover">
            <RouterLink
              v-for="item in searchResults"
              :key="`${item.type}-${item.title}`"
              :to="item.path"
              class="fst-search-result"
              @click="showSearchResults = false"
            >
              <strong>{{ item.title }}</strong>
              <span>{{ item.type }} / {{ item.description }}</span>
            </RouterLink>
            <div v-if="!searchResults.length" class="empty-state">暂无搜索结果</div>
          </div>
        </div>

        <div class="fst-header-actions">
          <button class="fst-link-icon" type="button" @click="restartTour">引导</button>
          <span class="topbar-badge">MCP</span>
          <span class="topbar-badge">RAG</span>
          <span class="topbar-badge">pytest</span>
          <div class="user-avatar">QP</div>
        </div>
      </header>

      <section class="fst-content">
        <RouterView />
      </section>
    </main>

    <button class="fst-copilot-trigger" type="button" @click="copilotOpen = !copilotOpen">AI</button>
    <aside v-if="copilotOpen" class="fst-copilot-panel">
      <div class="item-title">
        <h3>平台级 Copilot</h3>
        <button class="tour-close" type="button" @click="copilotOpen = false">×</button>
      </div>
      <textarea v-model="copilotInput" class="assistant-textarea compact-textarea" rows="4" />
      <button class="primary-button full-width" :disabled="copilotLoading" @click="submitCopilot">
        {{ copilotLoading ? "规划中..." : "生成操作计划" }}
      </button>
      <p v-if="copilotAnswer" class="muted">{{ copilotAnswer }}</p>
      <div v-if="copilotOperations.length" class="stack">
        <pre
          v-for="(operation, index) in copilotOperations"
          :key="index"
          class="mini-code"
        >{{ JSON.stringify(operation, null, 2) }}</pre>
      </div>
    </aside>

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
