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

const settings = ref<PlatformSetting[]>([]);
const aiConfig = ref<AiModelConfig | null>(null);
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const aiSaving = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const error = ref("");
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

const filteredSettings = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return settings.value;
  return settings.value.filter((setting) =>
    `${setting.setting_id} ${setting.name} ${setting.value} ${setting.description}`
      .toLowerCase()
      .includes(keyword),
  );
});

const summary = computed(() => ({
  total: settings.value.length,
  builtin: settings.value.filter((item) => item.is_builtin).length,
  custom: settings.value.filter((item) => !item.is_builtin).length,
}));

const aiConfigStatus = computed(() => {
  if (!aiConfig.value?.configured) return { color: "orange", text: "未配置文本模型" };
  if (!aiConfig.value.enabled) return { color: "blue", text: "已保存，未启用真实模型" };
  return { color: "green", text: "已启用真实模型" };
});

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

function resetForm(): void {
  form.setting_id = "";
  form.name = "";
  form.value = "";
  form.description = "";
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(setting: PlatformSetting): void {
  form.setting_id = setting.setting_id;
  form.name = setting.name;
  form.value = setting.value;
  form.description = setting.description;
  modalMode.value = "edit";
  modalOpen.value = true;
}

function buildPayload() {
  return {
    name: form.name.trim(),
    value: form.value.trim(),
    description: form.description.trim(),
  };
}

async function loadSettings(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const [settingsData, modelData] = await Promise.all([getPlatformSettings(), getAiModelConfig()]);
    settings.value = settingsData.items;
    applyAiConfig(modelData.config);
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
    if (modalMode.value === "edit") {
      await updatePlatformSetting(form.setting_id, payload);
      antMessage.success("系统配置已更新");
    } else {
      await createGenericSetting(payload);
      antMessage.success("系统配置已创建");
    }
    modalOpen.value = false;
    await loadSettings();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

function confirmDelete(setting: PlatformSetting): void {
  Modal.confirm({
    title: `删除配置：${setting.name}`,
    content: "删除后该配置会从系统设置列表移除。这里是演示平台配置，重启服务后内置配置会恢复。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deletePlatformSetting(setting.setting_id);
      antMessage.success("系统配置已删除");
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
        <p class="qp-eyebrow">ADVANCED SETTINGS</p>
        <h1>高级配置</h1>
        <p>保留 RAG、MCP、pytest、Allure 等平台配置项，便于面试时说明平台集成点。</p>
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
          新建配置
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
          <a-card class="setting-card" :bordered="false">
            <div class="item-title">
              <h3>{{ setting.name }}</h3>
              <a-space>
                <a-tag>{{ setting.setting_id }}</a-tag>
                <a-tag v-if="setting.is_builtin" color="blue">内置</a-tag>
                <a-tag v-else color="green">自定义</a-tag>
              </a-space>
            </div>
            <pre class="mini-code">{{ setting.value }}</pre>
            <p class="muted">{{ setting.description }}</p>
            <a-space>
              <a-button size="small" type="primary" @click="openEditModal(setting)">
                <template #icon><EditOutlined /></template>
                修改
              </a-button>
              <a-button size="small" danger @click="confirmDelete(setting)">
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
      :title="modalMode === 'create' ? '新建配置' : '修改配置'"
      :confirm-loading="saving"
      width="620px"
      ok-text="保存"
      cancel-text="取消"
      @ok="submitSetting"
    >
      <a-form layout="vertical" class="env-form">
        <a-form-item label="配置名称" required>
          <a-input v-model:value="form.name" placeholder="例如 LLM Provider" />
        </a-form-item>
        <a-form-item label="配置值">
          <a-textarea v-model:value="form.value" class="code-editor" :rows="5" />
        </a-form-item>
        <a-form-item label="配置说明">
          <a-textarea v-model:value="form.description" placeholder="说明这个配置影响哪些功能" :rows="3" />
        </a-form-item>
        <div class="field-tip">
          高级配置会保存到当前 FastAPI 进程内存中；AI 模型接入请优先使用上方专门的 AI 助手配置。
        </div>
      </a-form>
    </a-modal>
  </section>
</template>
