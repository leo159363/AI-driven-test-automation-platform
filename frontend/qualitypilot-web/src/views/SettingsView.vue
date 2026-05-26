<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message as antMessage, Modal } from "ant-design-vue";
import {
  ApiOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
} from "@ant-design/icons-vue";
import {
  createPlatformSetting as createGenericSetting,
  deletePlatformSetting,
  getAiModelConfig,
  getPlatformSettings,
  testAiModelConfig,
  updateAiModelConfig,
  updatePlatformSetting,
} from "../services/api";
import type { AiModelConfig, PlatformSetting } from "../types";

type CapabilityType = "rag" | "mcp" | "runner" | "report" | "experimental" | "custom";
type CapabilityStatus = "enabled" | "disabled" | "experimental";

interface SettingForm {
  setting_id: string;
  name: string;
  value: string;
  description: string;
}

interface AiModelForm {
  enabled: boolean;
  base_url: string;
  model: string;
  api_key: string;
  vision_base_url: string;
  vision_model: string;
  vision_api_key: string;
}

interface CapabilitySetting extends PlatformSetting {
  capability_type: CapabilityType;
  status: CapabilityStatus;
  summary: string;
  is_default_capability: boolean;
}

const DEFAULT_CAPABILITIES: CapabilitySetting[] = [
  {
    setting_id: "capability-rag-store",
    name: "RAG Knowledge Store",
    capability_type: "rag",
    status: "enabled",
    summary: "store=local · top_k=5 · chunk_size=800 · source_type_filter=5",
    value: formatJson({
      enabled: true,
      store: "local",
      top_k: 5,
      chunk_size: 800,
      source_type_filter: ["requirement", "api_doc", "bug", "log", "report"],
    }),
    description:
      "控制知识库检索参数。AI 生成测试用例、失败分析和 Bug 报告时，会优先从 RAG 知识库检索相关需求、接口文档、历史缺陷和日志。",
    is_builtin: true,
    is_default_capability: true,
  },
  {
    setting_id: "capability-mcp-server",
    name: "MCP Server",
    capability_type: "mcp",
    status: "enabled",
    summary: "transport=stdio · tools=6",
    value: formatJson({
      enabled: true,
      transport: "stdio",
      tools: [
        "retrieve_test_context",
        "generate_test_cases",
        "run_api_tests",
        "get_test_report",
        "analyze_failure",
        "generate_bug_report",
      ],
    }),
    description:
      "控制 MCP 工具服务。后续 Agent 编排中心会通过这些工具完成上下文检索、用例生成、测试执行、报告读取和失败分析。",
    is_builtin: true,
    is_default_capability: true,
  },
  {
    setting_id: "capability-test-runner",
    name: "Test Runner",
    capability_type: "runner",
    status: "enabled",
    summary: "framework=pytest · timeout=120s · artifacts=artifacts",
    value: formatJson({
      enabled: true,
      framework: "pytest",
      timeout_seconds: 120,
      artifacts_dir: "artifacts",
      junit_xml: "artifacts/junit.xml",
      allure_results_dir: "artifacts/allure-results",
    }),
    description:
      "控制自动化测试执行器参数。平台执行 API 测试、自动化用例和回归任务时，会使用这里的 pytest 和报告目录配置。",
    is_builtin: true,
    is_default_capability: true,
  },
  {
    setting_id: "capability-allure-report",
    name: "Allure Report",
    capability_type: "report",
    status: "enabled",
    summary: "results=artifacts/allure-results · report=artifacts/allure-report · auto_parse=true",
    value: formatJson({
      enabled: true,
      results_dir: "artifacts/allure-results",
      report_dir: "artifacts/allure-report",
      auto_parse: true,
    }),
    description:
      "控制 Allure 报告解析。测试执行完成后，平台会读取 Allure results 并生成报告摘要、失败用例列表和趋势数据。",
    is_builtin: true,
    is_default_capability: true,
  },
  {
    setting_id: "capability-agent-orchestration",
    name: "Agent Orchestration",
    capability_type: "experimental",
    status: "experimental",
    summary: "planner=rule-based · executor=mock · max_steps=8 · human_review=true",
    value: formatJson({
      enabled: false,
      planner: "rule-based",
      executor: "mock",
      max_steps: 8,
      human_review_required: true,
    }),
    description:
      "控制测试任务编排能力。当前可用于规则型测试计划生成，后续将接入 MCP tools，实现自然语言目标到测试执行链路的自动编排。",
    is_builtin: true,
    is_default_capability: true,
  },
];

const builtinCapabilities = ref<CapabilitySetting[]>(cloneDefaultCapabilities());
const customSettings = ref<PlatformSetting[]>([]);
const aiConfig = ref<AiModelConfig | null>(null);
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const aiSaving = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const editingDefaultCapability = ref(false);
const error = ref("");
const jsonError = ref("");
const testResult = ref("");

const aiForm = reactive<AiModelForm>({
  enabled: false,
  base_url: "",
  model: "",
  api_key: "",
  vision_base_url: "",
  vision_model: "",
  vision_api_key: "",
});

const form = reactive<SettingForm>({
  setting_id: "",
  name: "",
  value: "",
  description: "",
});

const platformCapabilities = computed<CapabilitySetting[]>(() => [
  ...builtinCapabilities.value,
  ...customSettings.value.map(toCustomCapability),
]);

const filteredSettings = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return platformCapabilities.value;
  return platformCapabilities.value.filter((setting) =>
    [
      setting.setting_id,
      setting.name,
      setting.capability_type,
      setting.status,
      setting.summary,
      setting.value,
      setting.description,
    ]
      .join(" ")
      .toLowerCase()
      .includes(keyword),
  );
});

const summary = computed(() => ({
  total: builtinCapabilities.value.length + customSettings.value.length,
  builtin: builtinCapabilities.value.length,
  custom: customSettings.value.length,
}));

const aiConfigStatus = computed(() => {
  if (!aiConfig.value?.configured) return { color: "orange", text: "未配置文本模型" };
  if (!aiConfig.value.enabled) return { color: "blue", text: "已保存，未启用真实模型" };
  return { color: "green", text: "已启用真实模型" };
});

const modalTitle = computed(() => {
  if (modalMode.value === "create") return "新增自定义配置";
  return editingDefaultCapability.value ? "编辑平台能力配置" : "编辑自定义配置";
});

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function cloneDefaultCapabilities(): CapabilitySetting[] {
  return DEFAULT_CAPABILITIES.map((item) => ({ ...item }));
}

function applyAiConfig(config: AiModelConfig): void {
  aiConfig.value = config;
  aiForm.enabled = config.enabled;
  aiForm.base_url = config.base_url || "";
  aiForm.model = config.model || "";
  aiForm.api_key = "";
  aiForm.vision_base_url = config.vision_base_url || "";
  aiForm.vision_model = config.vision_model || "";
  aiForm.vision_api_key = "";
}

function toCustomCapability(setting: PlatformSetting): CapabilitySetting {
  const parsed = parseJsonSafely(setting.value);
  const status = inferStatus(parsed);
  return {
    ...setting,
    capability_type: "custom",
    status,
    summary: summarizeCustomConfig(parsed),
    is_builtin: false,
    is_default_capability: false,
  };
}

function parseJsonSafely(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function inferStatus(parsed: unknown): CapabilityStatus {
  if (parsed && typeof parsed === "object" && "enabled" in parsed) {
    return Boolean((parsed as { enabled?: unknown }).enabled) ? "enabled" : "disabled";
  }
  return "experimental";
}

function summarizeCustomConfig(parsed: unknown): string {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return "custom JSON config";
  }
  const entries = Object.entries(parsed as Record<string, unknown>).slice(0, 3);
  if (!entries.length) return "custom JSON config";
  return entries
    .map(([key, value]) => `${key}=${Array.isArray(value) ? `[${value.length}]` : String(value)}`)
    .join(" · ");
}

function typeColor(type: CapabilityType): string {
  const colors: Record<CapabilityType, string> = {
    rag: "green",
    mcp: "cyan",
    runner: "blue",
    report: "gold",
    experimental: "purple",
    custom: "default",
  };
  return colors[type];
}

function statusColor(status: CapabilityStatus): string {
  const colors: Record<CapabilityStatus, string> = {
    enabled: "success",
    disabled: "default",
    experimental: "warning",
  };
  return colors[status];
}

function resetForm(): void {
  form.setting_id = "";
  form.name = "";
  form.value = "";
  form.description = "";
  jsonError.value = "";
  editingDefaultCapability.value = false;
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(setting: CapabilitySetting): void {
  form.setting_id = setting.setting_id;
  form.name = setting.name;
  form.value = setting.value;
  form.description = setting.description;
  jsonError.value = "";
  editingDefaultCapability.value = setting.is_default_capability;
  modalMode.value = "edit";
  modalOpen.value = true;
}

function buildPayload(): { name: string; value: string; description: string } {
  const parsed = parseConfigJson(form.value);
  return {
    name: form.name.trim(),
    value: formatJson(parsed),
    description: form.description.trim(),
  };
}

function parseConfigJson(value: string): unknown {
  try {
    jsonError.value = "";
    return JSON.parse(value);
  } catch {
    jsonError.value = '配置值必须是合法 JSON，例如 {"enabled": true}';
    throw new Error(jsonError.value);
  }
}

async function loadSettings(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const modelData = await getAiModelConfig();
    applyAiConfig(modelData.config);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }

  try {
    const settingsData = await getPlatformSettings();
    customSettings.value = settingsData.items.filter((item) => !item.is_builtin);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitAiConfig(): Promise<boolean> {
  aiSaving.value = true;
  error.value = "";
  testResult.value = "";
  try {
    const result = await updateAiModelConfig({
      enabled: aiForm.enabled,
      base_url: aiForm.base_url.trim(),
      model: aiForm.model.trim(),
      api_key: aiForm.api_key.trim(),
      vision_base_url: aiForm.vision_base_url.trim(),
      vision_model: aiForm.vision_model.trim(),
      vision_api_key: aiForm.vision_api_key.trim(),
    });
    applyAiConfig(result.config);
    antMessage.success("AI 助手模型配置已保存");
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    return false;
  } finally {
    aiSaving.value = false;
  }
}

async function submitTestConnection(): Promise<void> {
  testing.value = true;
  error.value = "";
  testResult.value = "";
  try {
    const saved = await submitAiConfig();
    if (!saved) return;
    const result = await testAiModelConfig();
    testResult.value = result.ok
      ? `连接成功：${result.model} 返回 ${result.sample || "ok"}`
      : result.message;
    if (result.ok) {
      antMessage.success("模型连接测试成功");
    } else {
      antMessage.warning(result.message);
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    testing.value = false;
  }
}

async function submitSetting(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = buildPayload();
    if (!payload.name) {
      throw new Error("配置名称不能为空");
    }
    if (editingDefaultCapability.value) {
      builtinCapabilities.value = builtinCapabilities.value.map((item) =>
        item.setting_id === form.setting_id
          ? {
              ...item,
              name: payload.name,
              value: payload.value,
              description: payload.description || item.description,
              status: inferStatus(JSON.parse(payload.value)),
              summary: summarizeDefaultConfig(item.capability_type, JSON.parse(payload.value)),
            }
          : item,
      );
      antMessage.success("平台能力配置已更新");
    } else if (modalMode.value === "edit") {
      await updatePlatformSetting(form.setting_id, payload);
      antMessage.success("自定义配置已更新");
      await loadSettings();
    } else {
      await createGenericSetting(payload);
      antMessage.success("自定义配置已创建");
      await loadSettings();
    }
    modalOpen.value = false;
  } catch (err) {
    if (!jsonError.value) {
      error.value = err instanceof Error ? err.message : String(err);
    }
  } finally {
    saving.value = false;
  }
}

function summarizeDefaultConfig(type: CapabilityType, parsed: unknown): string {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return "invalid JSON";
  }
  const config = parsed as Record<string, unknown>;
  if (type === "rag") {
    return `store=${config.store ?? "-"} · top_k=${config.top_k ?? "-"} · chunk_size=${config.chunk_size ?? "-"}`;
  }
  if (type === "mcp") {
    return `transport=${config.transport ?? "-"} · tools=${Array.isArray(config.tools) ? config.tools.length : 0}`;
  }
  if (type === "runner") {
    return `framework=${config.framework ?? "-"} · timeout=${config.timeout_seconds ?? "-"}s · artifacts=${config.artifacts_dir ?? "-"}`;
  }
  if (type === "report") {
    return `results=${config.results_dir ?? "-"} · report=${config.report_dir ?? "-"} · auto_parse=${config.auto_parse ?? "-"}`;
  }
  if (type === "experimental") {
    return `planner=${config.planner ?? "-"} · executor=${config.executor ?? "-"} · max_steps=${config.max_steps ?? "-"}`;
  }
  return summarizeCustomConfig(parsed);
}

function confirmDelete(setting: CapabilitySetting): void {
  if (setting.is_default_capability) return;
  Modal.confirm({
    title: `删除配置：${setting.name}`,
    content: "删除后该自定义配置会从系统设置列表移除。内置平台能力配置不会被删除。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deletePlatformSetting(setting.setting_id);
      antMessage.success("自定义配置已删除");
      await loadSettings();
    },
  });
}

onMounted(loadSettings);
</script>

<template>
  <section class="qp-page settings-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">SYSTEM SETTINGS</p>
        <h1>系统设置</h1>
        <p>管理平台基础配置和第三方服务接入参数，AI 助手配置会影响用例生成、失败分析和 Bug 草稿。</p>
      </div>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="系统设置模块错误"
      :description="error"
    />

    <a-card class="section-gap ai-config-card" :bordered="false">
      <template #title>
        <a-space>
          <ApiOutlined />
          <span>AI 助手配置（全局）</span>
          <a-tag :color="aiConfigStatus.color">{{ aiConfigStatus.text }}</a-tag>
        </a-space>
      </template>

      <a-alert
        class="section-gap-sm"
        type="info"
        show-icon
        message="配置说明"
        description="这里配置的大模型参数会全局生效，包括 AI 测试助手、接口用例生成、失败原因分析、Bug 报告生成和后续 Web/App/性能测试智能生成。兼容 OpenAI API 格式，也可以填通义千问、DeepSeek、Kimi 等 OpenAI-compatible 服务地址。"
      />

      <a-form layout="vertical" class="section-gap-sm">
        <a-row :gutter="[24, 12]">
          <a-col :xs="24" :lg="12">
            <a-form-item label="Base URL" required>
              <a-input v-model:value="aiForm.base_url" placeholder="https://api.openai.com/v1" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="模型名称（Model）" required>
              <a-input v-model:value="aiForm.model" placeholder="gpt-4o-mini / deepseek-chat" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="API Key" required>
              <a-input-password
                v-model:value="aiForm.api_key"
                :placeholder="aiConfig?.has_api_key ? '已保存，留空表示不修改' : 'sk-...'"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="启用真实模型">
              <a-switch v-model:checked="aiForm.enabled" />
              <span class="setting-inline-tip">
                关闭时仍可保存配置，但 AI 助手会使用本地确定性 Demo。
              </span>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="视觉模型 Base URL">
              <a-input v-model:value="aiForm.vision_base_url" placeholder="https://api.openai.com/v1" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="视觉模型名称（Vision Model）">
              <a-input v-model:value="aiForm.vision_model" placeholder="gpt-4o-mini" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :lg="12">
            <a-form-item label="视觉模型 API Key">
              <a-input-password
                v-model:value="aiForm.vision_api_key"
                :placeholder="aiConfig?.has_vision_api_key ? '已保存，留空表示不修改' : 'sk-...'"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-space class="section-gap-sm">
          <a-button type="primary" :loading="aiSaving" @click="submitAiConfig">
            <template #icon><SaveOutlined /></template>
            保存设置
          </a-button>
          <a-button :loading="testing" @click="submitTestConnection">
            <template #icon><CheckCircleOutlined /></template>
            测试连接
          </a-button>
        </a-space>
        <a-alert
          v-if="testResult"
          class="section-gap-sm"
          :type="testResult.startsWith('连接成功') ? 'success' : 'warning'"
          show-icon
          :message="testResult"
        />
      </a-form>
    </a-card>

    <div class="qp-page-heading section-gap">
      <div>
        <p class="qp-eyebrow">PLATFORM CAPABILITY</p>
        <h1>平台能力配置</h1>
        <p>管理 RAG、MCP、pytest、Allure、Agent 编排等平台级能力的运行参数。</p>
      </div>
      <a-space>
        <a-input-search
          v-model:value="searchKeyword"
          class="env-search"
          placeholder="搜索配置..."
          allow-clear
        />
        <a-button @click="loadSettings">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          新增自定义配置
        </a-button>
      </a-space>
    </div>

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>配置总数</span>
          <strong>{{ summary.total }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>内置配置</span>
          <strong>{{ summary.builtin }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>自定义配置</span>
          <strong>{{ summary.custom }}</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-spin :spinning="loading">
      <a-row :gutter="[16, 16]" class="section-gap">
        <a-col v-for="setting in filteredSettings" :key="setting.setting_id" :xs="24" :lg="12">
          <a-card class="setting-card capability-card" :bordered="false">
            <div class="item-title">
              <h3>{{ setting.name }}</h3>
              <a-space>
                <a-tag :color="typeColor(setting.capability_type)">
                  {{ setting.capability_type }}
                </a-tag>
                <a-tag :color="statusColor(setting.status)">
                  {{ setting.status }}
                </a-tag>
              </a-space>
            </div>
            <p class="capability-summary">{{ setting.summary }}</p>
            <pre class="mini-code">{{ setting.value }}</pre>
            <p class="muted capability-description">{{ setting.description }}</p>
            <a-space>
              <a-button size="small" type="primary" @click="openEditModal(setting)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button
                v-if="!setting.is_default_capability"
                size="small"
                danger
                @click="confirmDelete(setting)"
              >
                <template #icon><DeleteOutlined /></template>
                删除
              </a-button>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="!filteredSettings.length" description="暂无匹配配置" />
    </a-spin>

    <a-modal
      v-model:open="modalOpen"
      :title="modalTitle"
      :confirm-loading="saving"
      width="680px"
      ok-text="保存"
      cancel-text="取消"
      @ok="submitSetting"
    >
      <a-alert
        v-if="modalMode === 'create'"
        class="section-gap-sm"
        type="info"
        show-icon
        message="自定义配置说明"
        description="自定义配置用于扩展平台运行参数，例如第三方服务地址、实验性功能开关或自定义报告路径。一般用户无需新增。"
      />
      <a-form layout="vertical" class="env-form section-gap-sm">
        <a-form-item label="配置名称" required>
          <a-input v-model:value="form.name" placeholder="例如 Custom Report Path" />
        </a-form-item>
        <a-form-item
          label="配置值 JSON"
          required
          :validate-status="jsonError ? 'error' : ''"
          :help="jsonError || undefined"
        >
          <a-textarea
            v-model:value="form.value"
            class="code-editor"
            :rows="8"
            placeholder='例如 {"enabled": true}'
            @change="jsonError = ''"
          />
        </a-form-item>
        <a-form-item label="配置说明">
          <a-textarea
            v-model:value="form.description"
            placeholder="说明这个配置影响哪些功能"
            :rows="3"
          />
        </a-form-item>
        <div class="field-tip">
          配置值必须是合法 JSON，例如 {"enabled": true}。内置平台能力配置只影响当前前端展示；自定义配置沿用现有 FastAPI 内存保存机制。
        </div>
      </a-form>
    </a-modal>
  </section>
</template>
