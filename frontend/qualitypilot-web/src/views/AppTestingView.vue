<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message as antMessage, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons-vue";
import {
  createAppTestScript,
  deleteAppTestScript,
  getAppTestScripts,
  runAppTestScript,
  updateAppTestScript,
} from "../services/api";
import type { AppTestScript, PlatformRunRecord } from "../types";

interface AppScriptForm {
  script_id: string;
  name: string;
  description: string;
  platform: string;
  automation_engine: string;
  case_set: string;
  priority: string;
  device: string;
  status: string;
  pytest_target: string;
  steps_text: string;
  assertions_text: string;
}

const scripts = ref<AppTestScript[]>([]);
const selectedScriptId = ref("");
const searchKeyword = ref("");
const caseSetFilter = ref("全部");
const error = ref("");
const loading = ref(false);
const saving = ref(false);
const runningScriptId = ref("");
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const runRecord = ref<PlatformRunRecord | null>(null);

const form = reactive<AppScriptForm>({
  script_id: "",
  name: "",
  description: "",
  platform: "Android",
  automation_engine: "UiAutomator2 (Android)",
  case_set: "登录鉴权",
  priority: "P2",
  device: "Mock Android 13",
  status: "draft",
  pytest_target: "",
  steps_text: "打开 App 登录页\n输入测试账号\n点击登录按钮",
  assertions_text: "登录成功返回 token\n错误密码返回 401\n不泄露敏感字段",
});

const platformOptions = ["Android", "iOS", "Android / iOS"];
const engineOptions = ["UiAutomator2 (Android)", "XCUITest (iOS)", "Espresso (Android)", "Appium"];
const priorityOptions = ["P0", "P1", "P2", "P3"];
const statusOptions = ["draft", "planned", "ready"];
const defaultCaseSets = ["登录鉴权", "文件上传", "用户中心", "订单流程", "支付回调"];
const deviceOptions = ["Mock Android 13", "iPhone 15 Simulator", "真机云 Android", "真机云 iOS", "接口 Mock"];

const selectedScript = computed(
  () => scripts.value.find((item) => item.script_id === selectedScriptId.value) ?? scripts.value[0],
);

const caseSetOptions = computed(() => {
  const caseSets = new Set(defaultCaseSets);
  for (const script of scripts.value) {
    if (script.case_set || script.module) {
      caseSets.add(script.case_set || script.module);
    }
  }
  return ["全部", ...Array.from(caseSets)];
});

const filteredScripts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  return scripts.value.filter((script) => {
    const caseSetMatched =
      caseSetFilter.value === "全部" || (script.case_set || script.module) === caseSetFilter.value;
    const keywordMatched =
      !keyword ||
      `${script.name} ${script.script_id} ${script.platform} ${script.automation_engine ?? ""} ${
        script.case_set ?? script.module
      }`
        .toLowerCase()
        .includes(keyword);
    return caseSetMatched && keywordMatched;
  });
});

const summary = computed(() => ({
  total: scripts.value.length,
  android: scripts.value.filter((script) => script.platform.includes("Android")).length,
  ready: scripts.value.filter((script) => ["ready", "demo"].includes(script.status)).length,
  custom: scripts.value.filter((script) => !script.is_builtin).length,
}));

function resetForm(): void {
  form.script_id = "";
  form.name = "";
  form.description = "";
  form.platform = "Android";
  form.automation_engine = "UiAutomator2 (Android)";
  form.case_set = "登录鉴权";
  form.priority = "P2";
  form.device = "Mock Android 13";
  form.status = "draft";
  form.pytest_target = "";
  form.steps_text = "打开 App 登录页\n输入测试账号\n点击登录按钮";
  form.assertions_text = "登录成功返回 token\n错误密码返回 401\n不泄露敏感字段";
}

function splitLines(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(script: AppTestScript): void {
  form.script_id = script.script_id;
  form.name = script.name;
  form.description = script.scope;
  form.platform = script.platform;
  form.automation_engine = script.automation_engine || "UiAutomator2 (Android)";
  form.case_set = script.case_set || script.module;
  form.priority = script.priority;
  form.device = script.device || "Mock Android 13";
  form.status = script.status === "demo" ? "ready" : script.status;
  form.pytest_target = script.pytest_target || "";
  form.steps_text = script.steps.join("\n");
  form.assertions_text = script.assertions.join("\n");
  modalMode.value = "edit";
  modalOpen.value = true;
}

function buildPayload() {
  return {
    name: form.name.trim(),
    description: form.description.trim(),
    platform: form.platform,
    automation_engine: form.automation_engine,
    case_set: form.case_set,
    priority: form.priority,
    device: form.device,
    status: form.status,
    pytest_target: form.pytest_target.trim(),
    steps: splitLines(form.steps_text),
    assertions: splitLines(form.assertions_text),
  };
}

async function loadScripts(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const data = await getAppTestScripts();
    scripts.value = data.items;
    selectedScriptId.value = data.items[0]?.script_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitScript(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = buildPayload();
    if (!payload.name) {
      throw new Error("脚本名称不能为空");
    }
    if (modalMode.value === "edit") {
      await updateAppTestScript(form.script_id, payload);
      antMessage.success("APP 自动化脚本已更新");
    } else {
      const result = await createAppTestScript(payload);
      selectedScriptId.value = result.script.script_id;
      antMessage.success("APP 自动化脚本已创建");
    }
    modalOpen.value = false;
    await loadScripts();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

async function submitRunScript(script: AppTestScript): Promise<void> {
  runningScriptId.value = script.script_id;
  error.value = "";
  try {
    runRecord.value = await runAppTestScript(script.script_id);
    selectedScriptId.value = script.script_id;
    antMessage.success("APP 脚本运行预览完成");
    await loadScripts();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    runningScriptId.value = "";
  }
}

function confirmDelete(script: AppTestScript): void {
  Modal.confirm({
    title: `删除脚本：${script.name}`,
    content: "删除后该自定义 APP 自动化脚本会从列表移除，内置脚本不能删除。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deleteAppTestScript(script.script_id);
      antMessage.success("APP 自动化脚本已删除");
      await loadScripts();
    },
  });
}

function statusColor(status: string): string {
  if (status === "ready" || status === "demo") return "green";
  if (status === "planned") return "blue";
  return "orange";
}

onMounted(loadScripts);
</script>

<template>
  <section class="qp-page app-script-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">APP AUTOMATION</p>
        <h1>APP 自动化测试</h1>
        <p>按脚本管理移动端自动化测试资产，支持平台、自动化引擎、用例集、设备和 pytest 目标维护。</p>
      </div>
      <a-space>
        <a-button @click="loadScripts">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          新建脚本
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="APP 自动化测试模块错误"
      :description="error"
    />

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>脚本总数</span>
          <strong>{{ summary.total }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>Android 覆盖</span>
          <strong>{{ summary.android }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>可运行脚本</span>
          <strong>{{ summary.ready }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>自定义脚本</span>
          <strong>{{ summary.custom }}</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-card class="section-gap env-table-card" :bordered="false">
      <template #title>
        <a-space wrap>
          <a-input-search
            v-model:value="searchKeyword"
            class="env-search"
            placeholder="搜索脚本名称"
            allow-clear
          />
          <a-select v-model:value="caseSetFilter" class="app-case-filter">
            <a-select-option v-for="item in caseSetOptions" :key="item" :value="item">
              {{ item === "全部" ? "按用例集筛选" : item }}
            </a-select-option>
          </a-select>
        </a-space>
      </template>

      <a-spin :spinning="loading">
        <table class="env-table">
          <thead>
            <tr>
              <th>脚本名称</th>
              <th>平台</th>
              <th>自动化引擎</th>
              <th>所属用例集</th>
              <th>设备</th>
              <th>状态</th>
              <th>最后执行</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="script in filteredScripts"
              :key="script.script_id"
              :class="{ 'selected-row': script.script_id === selectedScript?.script_id }"
              @click="selectedScriptId = script.script_id"
            >
              <td>
                <strong>{{ script.name }}</strong>
                <div class="muted">{{ script.script_id }}</div>
                <a-tag v-if="script.is_builtin" color="blue">内置</a-tag>
                <a-tag v-else color="green">自定义</a-tag>
              </td>
              <td>{{ script.platform }}</td>
              <td>{{ script.automation_engine || "-" }}</td>
              <td>{{ script.case_set || script.module }}</td>
              <td>{{ script.device || "-" }}</td>
              <td>
                <a-tag :color="statusColor(script.status)">{{ script.status }}</a-tag>
              </td>
              <td>{{ script.last_run_at ?? "-" }}</td>
              <td>
                <a-space @click.stop>
                  <a-button
                    size="small"
                    :loading="runningScriptId === script.script_id"
                    @click="submitRunScript(script)"
                  >
                    <template #icon><PlayCircleOutlined /></template>
                    运行
                  </a-button>
                  <a-button size="small" :disabled="script.is_builtin" @click="openEditModal(script)">
                    <template #icon><EditOutlined /></template>
                    编辑
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    :disabled="script.is_builtin"
                    @click="confirmDelete(script)"
                  >
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-space>
              </td>
            </tr>
          </tbody>
        </table>
        <a-empty v-if="!filteredScripts.length" description="暂无匹配脚本" />
      </a-spin>
    </a-card>

    <a-row :gutter="[16, 16]" class="section-gap" v-if="selectedScript">
      <a-col :xs="24" :lg="14">
        <a-card title="脚本详情" :bordered="false">
          <p class="muted">{{ selectedScript.scope }}</p>
          <a-descriptions bordered size="small" :column="2" class="section-gap-sm">
            <a-descriptions-item label="pytest 目标" :span="2">
              <span class="path-text">{{ selectedScript.pytest_target || "暂未绑定 pytest 脚本" }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="平台">{{ selectedScript.platform }}</a-descriptions-item>
            <a-descriptions-item label="引擎">
              {{ selectedScript.automation_engine || "-" }}
            </a-descriptions-item>
            <a-descriptions-item label="优先级">{{ selectedScript.priority }}</a-descriptions-item>
            <a-descriptions-item label="设备">{{ selectedScript.device || "-" }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="10">
        <a-card title="步骤与断言" :bordered="false">
          <ol class="number-list">
            <li v-for="step in selectedScript.steps" :key="step">{{ step }}</li>
          </ol>
          <a-space wrap>
            <a-tag v-for="assertion in selectedScript.assertions" :key="assertion">
              {{ assertion }}
            </a-tag>
          </a-space>
          <template v-if="runRecord">
            <h3 class="section-gap-sm">最近运行</h3>
            <a-tag :color="runRecord.status === 'passed' ? 'green' : 'red'">
              {{ runRecord.status }}
            </a-tag>
            <pre class="mini-code">{{ runRecord.command }}</pre>
          </template>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="modalOpen"
      :title="modalMode === 'create' ? '新建脚本' : '编辑脚本'"
      :confirm-loading="saving"
      width="660px"
      ok-text="确定"
      cancel-text="取消"
      @ok="submitScript"
    >
      <a-form layout="vertical" class="env-form">
        <a-form-item label="脚本名称" required>
          <a-input v-model:value="form.name" placeholder="请输入脚本名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入描述" :rows="3" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="平台">
              <a-select v-model:value="form.platform">
                <a-select-option v-for="item in platformOptions" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="自动化引擎">
              <a-select v-model:value="form.automation_engine">
                <a-select-option v-for="item in engineOptions" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="所属用例集">
              <a-select v-model:value="form.case_set">
                <a-select-option v-for="item in defaultCaseSets" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="优先级">
              <a-select v-model:value="form.priority">
                <a-select-option v-for="item in priorityOptions" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="设备">
              <a-select v-model:value="form.device">
                <a-select-option v-for="item in deviceOptions" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态">
              <a-select v-model:value="form.status">
                <a-select-option v-for="item in statusOptions" :key="item" :value="item">
                  {{ item }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="pytest 目标">
          <a-input
            v-model:value="form.pytest_target"
            placeholder="例如 tests/automation/test_app_login.py::test_app_login_smoke"
          />
        </a-form-item>
        <a-form-item label="步骤">
          <a-textarea v-model:value="form.steps_text" class="code-editor" :rows="4" />
        </a-form-item>
        <a-form-item label="断言">
          <a-textarea v-model:value="form.assertions_text" class="code-editor" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>
