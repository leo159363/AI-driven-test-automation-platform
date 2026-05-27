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
  createPlatformConfig,
  deletePlatformConfig,
  getAiModelConfig,
  getPlatformConfigs,
  testAiModelConfig,
  updateAiModelConfig,
  updatePlatformConfig,
} from "../services/api";
import type {
  AiModelConfig,
  PlatformConfigItem,
  PlatformConfigStatus,
  PlatformConfigType,
} from "../types";

interface AiModelForm {
  enabled: boolean;
  base_url: string;
  model: string;
  api_key: string;
  vision_base_url: string;
  vision_model: string;
  vision_api_key: string;
}

interface SettingForm {
  key: string;
  name: string;
  type: PlatformConfigType;
  enabled: boolean;
  value: string;
  description: string;
}

interface CapabilitySetting {
  key: string;
  name: string;
  type: PlatformConfigType;
  builtin: boolean;
  enabled: boolean;
  status: PlatformConfigStatus;
  summary: string;
  value: string;
  rawValue: Record<string, unknown>;
  description: string;
}

const platformConfigs = ref<CapabilitySetting[]>([]);
const aiConfig = ref<AiModelConfig | null>(null);
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const aiSaving = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const editingBuiltin = ref(false);
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
  key: "",
  name: "",
  type: "custom",
  enabled: true,
  value: formatJson({ enabled: true }),
  description: "",
});

const filteredSettings = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return platformConfigs.value;
  return platformConfigs.value.filter((setting) =>
    [
      setting.key,
      setting.name,
      setting.type,
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
  total: platformConfigs.value.length,
  builtin: platformConfigs.value.filter((item) => item.builtin).length,
  custom: platformConfigs.value.filter((item) => !item.builtin).length,
}));

const aiConfigStatus = computed(() => {
  if (!aiConfig.value?.configured) return { color: "orange", text: "未配置文本模型" };
  if (!aiConfig.value.enabled) return { color: "blue", text: "已保存，未启用真实模型" };
  return { color: "green", text: "已启用真实模型" };
});

const modalTitle = computed(() => {
  if (modalMode.value === "create") return "新增自定义配置";
  return editingBuiltin.value ? "编辑平台能力配置" : "编辑自定义配置";
});

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function toCapabilitySetting(config: PlatformConfigItem): CapabilitySetting {
  return {
    key: config.key,
    name: config.name,
    type: config.type,
    builtin: config.builtin,
    enabled: config.enabled,
    status: config.status,
    summary: config.summary,
    value: formatJson(config.value),
    rawValue: config.value,
    description: config.description,
  };
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

function typeColor(type: PlatformConfigType): string {
  const colors: Record<PlatformConfigType, string> = {
    rag: "green",
    mcp: "cyan",
    runner: "blue",
    report: "gold",
    experimental: "purple",
    custom: "default",
  };
  return colors[type];
}

function statusColor(status: PlatformConfigStatus): string {
  const colors: Record<PlatformConfigStatus, string> = {
    enabled: "success",
    disabled: "default",
    experimental: "warning",
  };
  return colors[status];
}

function resetForm(): void {
  form.key = "";
  form.name = "";
  form.type = "custom";
  form.enabled = true;
  form.value = formatJson({ enabled: true });
  form.description = "";
  jsonError.value = "";
  editingBuiltin.value = false;
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(setting: CapabilitySetting): void {
  form.key = setting.key;
  form.name = setting.name;
  form.type = setting.type;
  form.enabled = setting.enabled;
  form.value = setting.value;
  form.description = setting.description;
  jsonError.value = "";
  editingBuiltin.value = setting.builtin;
  modalMode.value = "edit";
  modalOpen.value = true;
}

function parseConfigJson(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("value must be object");
    }
    jsonError.value = "";
    return parsed as Record<string, unknown>;
  } catch {
    jsonError.value = '配置值必须是合法 JSON，例如 {"enabled": true}';
    throw new Error(jsonError.value);
  }
}

function buildPayload(): {
  key: string;
  name: string;
  type: PlatformConfigType;
  enabled: boolean;
  value: Record<string, unknown>;
  description: string;
} {
  const parsedValue = parseConfigJson(form.value);
  return {
    key: form.key.trim(),
    name: form.name.trim(),
    type: form.type,
    enabled: form.enabled,
    value: { ...parsedValue, enabled: form.enabled },
    description: form.description.trim(),
  };
}

async function loadSettings(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const [modelData, configData] = await Promise.all([getAiModelConfig(), getPlatformConfigs()]);
    applyAiConfig(modelData.config);
    platformConfigs.value = configData.items.map(toCapabilitySetting);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    antMessage.error(error.value);
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
    antMessage.error(error.value);
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
    antMessage.error(error.value);
  } finally {
    testing.value = false;
  }
}

async function submitSetting(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = buildPayload();
    if (!payload.key) throw new Error("配置 Key 不能为空");
    if (!payload.name) throw new Error("配置名称不能为空");

    if (modalMode.value === "create") {
      await createPlatformConfig(payload);
      antMessage.success("自定义配置已创建");
    } else if (editingBuiltin.value) {
      await updatePlatformConfig(payload.key, {
        enabled: payload.enabled,
        value: payload.value,
      });
      antMessage.success("平台能力配置已更新");
    } else {
      await updatePlatformConfig(payload.key, {
        name: payload.name,
        type: payload.type,
        enabled: payload.enabled,
        value: payload.value,
        description: payload.description,
      });
      antMessage.success("自定义配置已更新");
    }

    modalOpen.value = false;
    await loadSettings();
  } catch (err) {
    if (!jsonError.value) {
      error.value = err instanceof Error ? err.message : String(err);
      antMessage.error(error.value);
    }
  } finally {
    saving.value = false;
  }
}

function confirmDelete(setting: CapabilitySetting): void {
  if (setting.builtin) {
    antMessage.warning("内置配置不允许删除");
    return;
  }
  Modal.confirm({
    title: `删除配置：${setting.name}`,
    content: "删除后该自定义配置会从系统设置列表移除。内置平台能力配置不会被删除。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      try {
        await deletePlatformConfig(setting.key);
        antMessage.success("自定义配置已删除");
        await loadSettings();
      } catch (err) {
        error.value = err instanceof Error ? err.message : String(err);
        antMessage.error(error.value);
      }
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
        <a-col v-for="setting in filteredSettings" :key="setting.key" :xs="24" :lg="12">
          <a-card class="setting-card capability-card" :bordered="false">
            <div class="item-title">
              <h3>{{ setting.name }}</h3>
              <a-space>
                <a-tag :color="typeColor(setting.type)">
                  {{ setting.type }}
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
                v-if="!setting.builtin"
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
      width="720px"
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
        <a-row :gutter="[16, 8]">
          <a-col :xs="24" :md="12">
            <a-form-item label="配置 Key" required>
              <a-input
                v-model:value="form.key"
                placeholder="例如 custom_report_path"
                :disabled="modalMode === 'edit'"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="配置名称" required>
              <a-input
                v-model:value="form.name"
                placeholder="例如 Custom Report Path"
                :disabled="editingBuiltin"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="配置类型">
              <a-select v-model:value="form.type" :disabled="editingBuiltin">
                <a-select-option value="custom">custom</a-select-option>
                <a-select-option value="rag">rag</a-select-option>
                <a-select-option value="mcp">mcp</a-select-option>
                <a-select-option value="runner">runner</a-select-option>
                <a-select-option value="report">report</a-select-option>
                <a-select-option value="experimental">experimental</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="启用配置">
              <a-switch v-model:checked="form.enabled" />
            </a-form-item>
          </a-col>
        </a-row>
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
            :disabled="editingBuiltin"
          />
        </a-form-item>
        <div class="field-tip">
          配置值必须是合法 JSON object，例如 {"enabled": true}。内置配置不允许删除；编辑内置配置时只会保存 enabled 和 value。
        </div>
      </a-form>
    </a-modal>
  </section>
</template>
