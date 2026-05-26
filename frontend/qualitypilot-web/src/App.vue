<script setup lang="ts">
import { computed, h, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import {
  ApiOutlined,
  AppstoreOutlined,
  BookOutlined,
  BuildOutlined,
  CloudServerOutlined,
  CodeOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  GithubOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  QuestionCircleOutlined,
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
} from "@ant-design/icons-vue";
import {
  getPlatformProjects,
  globalSearch,
  sendCopilotMessage,
} from "./services/api";
import type { PlatformProject } from "./types";

interface SearchResult {
  type: string;
  title: string;
  path: string;
  description: string;
}

const route = useRoute();
const router = useRouter();

const collapsed = ref(false);
const openKeys = ref<string[]>(["api", "web", "app", "performance", "ai"]);
const projects = ref<PlatformProject[]>([]);
const selectedProjectId = ref("qualitypilot-demo");
const searchKeyword = ref("");
const searchResults = ref<SearchResult[]>([]);
const searchOpen = ref(false);
const searchLoading = ref(false);
const copilotOpen = ref(false);
const copilotInput = ref("帮我创建登录接口回归测试，并说明失败后如何生成 Bug 报告");
const copilotAnswer = ref("");
const copilotOperations = ref<Array<Record<string, string>>>([]);
const copilotLoading = ref(false);
const tourOpen = ref(false);
const logoRef = ref<HTMLElement | null>(null);
const menuRef = ref<HTMLElement | null>(null);
const searchRef = ref<HTMLElement | null>(null);
const statusRef = ref<HTMLElement | null>(null);

const selectedKeys = computed(() => [route.path]);
const selectedProject = computed(
  () => projects.value.find((item) => item.project_id === selectedProjectId.value) ?? projects.value[0],
);

const tourSteps = computed(() => [
  {
    title: "QualityPilot",
    description: "这是面向测试开发的全栈测试平台，不是单独的聊天页。",
    target: () => logoRef.value,
  },
  {
    title: "功能导航",
    description: "从接口测试、自动化执行、测试报告、AI 助手和知识库开始演示。",
    target: () => menuRef.value,
  },
  {
    title: "全局搜索",
    description: "可以搜索接口、用例、报告和文档，面试时用来展示平台化入口。",
    target: () => searchRef.value,
  },
  {
    title: "QualityPilot 特色",
    description: "MCP、RAG、pytest 和 Allure 是这个项目区别于普通测试管理平台的核心。",
    target: () => statusRef.value,
  },
]);

function menuLabel(path: string, text: string) {
  return h(RouterLink, { to: path }, () => text);
}

const menuItems = computed(() => [
  {
    key: "/",
    icon: () => h(DashboardOutlined),
    label: menuLabel("/", "工作台"),
  },
  {
    key: "api",
    icon: () => h(ApiOutlined),
    label: "接口测试",
    children: [
      { key: "/api-testing", label: menuLabel("/api-testing", "工作台") },
      { key: "/test-cases", label: menuLabel("/test-cases", "用例管理") },
      { key: "/api-environments", label: menuLabel("/api-environments", "环境配置") },
    ],
  },
  {
    key: "web",
    icon: () => h(CodeOutlined),
    label: "Web 测试",
    children: [{ key: "/web-testing", label: menuLabel("/web-testing", "脚本管理") }],
  },
  {
    key: "app",
    icon: () => h(AppstoreOutlined),
    label: "APP 测试",
    children: [{ key: "/app-testing", label: menuLabel("/app-testing", "脚本管理") }],
  },
  {
    key: "performance",
    icon: () => h(CloudServerOutlined),
    label: "性能测试",
    children: [
      { key: "/performance", label: menuLabel("/performance", "场景管理") },
      { key: "/reports", label: menuLabel("/reports", "结果分析") },
    ],
  },
  {
    key: "/reports",
    icon: () => h(FileSearchOutlined),
    label: menuLabel("/reports", "测试报告"),
  },
  {
    key: "/automation",
    icon: () => h(BuildOutlined),
    label: menuLabel("/automation", "自动化执行"),
  },
  {
    key: "/cicd",
    icon: () => h(GithubOutlined),
    label: menuLabel("/cicd", "CI/CD"),
  },
  {
    key: "/documents",
    icon: () => h(BookOutlined),
    label: menuLabel("/documents", "测试文档"),
  },
  {
    key: "ai",
    icon: () => h(RobotOutlined),
    label: "AI 与知识库",
    children: [
      { key: "/assistant", label: menuLabel("/assistant", "AI 测试助手") },
      { key: "/knowledge", label: menuLabel("/knowledge", "知识库管理") },
    ],
  },
  {
    key: "/settings",
    icon: () => h(SettingOutlined),
    label: menuLabel("/settings", "系统设置"),
  },
]);

async function submitGlobalSearch(value?: string): Promise<void> {
  const keyword = (value ?? searchKeyword.value).trim();
  if (!keyword) {
    searchResults.value = [];
    searchOpen.value = false;
    return;
  }
  searchLoading.value = true;
  try {
    const data = await globalSearch(keyword);
    searchResults.value = data.items;
    searchOpen.value = true;
  } finally {
    searchLoading.value = false;
  }
}

function openSearchResult(path: string): void {
  searchOpen.value = false;
  void router.push(path);
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

function handleTourClose(): void {
  localStorage.setItem("qualitypilot-tour-dismissed", "true");
}

onMounted(async () => {
  try {
    const data = await getPlatformProjects();
    projects.value = data.items;
    selectedProjectId.value = data.items[0]?.project_id ?? selectedProjectId.value;
  } catch {
    projects.value = [
      {
        project_id: "qualitypilot-demo",
        name: "QualityPilot Demo",
        description: "基于 MCP + RAG 的智能自动化测试平台演示项目。",
        modules: ["登录鉴权", "文件上传", "失败分析"],
        stack: ["Vue", "FastAPI", "MCP", "RAG", "pytest", "Allure"],
      },
    ];
  }
  tourOpen.value = localStorage.getItem("qualitypilot-tour-dismissed") !== "true";
});
</script>

<template>
  <a-layout class="qp-shell">
    <a-layout-sider
      v-model:collapsed="collapsed"
      class="qp-sider"
      :width="248"
      :collapsed-width="72"
      collapsible
      :trigger="null"
    >
      <div ref="logoRef" class="qp-logo">
        <div class="qp-logo-mark">QP</div>
        <div v-if="!collapsed">
          <strong>QualityPilot</strong>
          <span>AI 自动化测试平台</span>
        </div>
      </div>

      <a-menu
        ref="menuRef"
        v-model:openKeys="openKeys"
        class="qp-menu"
        mode="inline"
        :inline-collapsed="collapsed"
        :items="menuItems"
        :selected-keys="selectedKeys"
      />
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="qp-header">
        <div class="qp-header-left">
          <a-button type="text" class="qp-collapse" @click="collapsed = !collapsed">
            <MenuUnfoldOutlined v-if="collapsed" />
            <MenuFoldOutlined v-else />
          </a-button>

          <a-select
            v-model:value="selectedProjectId"
            class="qp-project-select"
            :options="projects.map((item) => ({ value: item.project_id, label: item.name }))"
          />

          <a-popover v-model:open="searchOpen" trigger="click" placement="bottomLeft">
            <template #content>
              <div class="qp-search-popover">
                <a-empty v-if="!searchResults.length" description="暂无搜索结果" />
                <button
                  v-for="item in searchResults"
                  v-else
                  :key="`${item.type}-${item.title}`"
                  class="qp-search-result"
                  type="button"
                  @click="openSearchResult(item.path)"
                >
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.type }} / {{ item.description }}</span>
                </button>
              </div>
            </template>
            <a-input-search
              ref="searchRef"
              v-model:value="searchKeyword"
              class="qp-global-search"
              placeholder="搜索接口、用例、报告"
              :loading="searchLoading"
              @search="submitGlobalSearch"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </a-popover>
        </div>

        <div ref="statusRef" class="qp-header-actions">
          <a-tag color="green">MCP</a-tag>
          <a-tag color="cyan">RAG</a-tag>
          <a-tag color="blue">pytest</a-tag>
          <a-tag color="gold">Allure</a-tag>
          <a-tooltip title="重新打开新手引导">
            <a-button shape="circle" @click="tourOpen = true">
              <QuestionCircleOutlined />
            </a-button>
          </a-tooltip>
          <a-avatar class="qp-avatar">QP</a-avatar>
        </div>
      </a-layout-header>

      <a-layout-content class="qp-content">
        <RouterView />
      </a-layout-content>
    </a-layout>

    <a-float-button type="primary" tooltip="平台级 Copilot" @click="copilotOpen = true">
      <template #icon><RobotOutlined /></template>
    </a-float-button>

    <a-drawer v-model:open="copilotOpen" width="420" title="平台级 Copilot">
      <a-space direction="vertical" size="middle" class="full-width">
        <a-alert
          message="这个入口用于生成操作计划，例如进入 API 工作台、生成用例、运行集合、查看报告。"
          type="info"
          show-icon
        />
        <a-textarea v-model:value="copilotInput" :rows="5" />
        <a-button type="primary" block :loading="copilotLoading" @click="submitCopilot">
          生成操作计划
        </a-button>
        <a-card v-if="copilotAnswer" size="small" title="建议">
          <p>{{ copilotAnswer }}</p>
        </a-card>
        <a-card v-if="copilotOperations.length" size="small" title="操作列表">
          <pre class="qp-mini-code">{{ JSON.stringify(copilotOperations, null, 2) }}</pre>
        </a-card>
      </a-space>
    </a-drawer>

    <a-tour
      v-model:open="tourOpen"
      :steps="tourSteps"
      @close="handleTourClose"
    />
  </a-layout>
</template>
