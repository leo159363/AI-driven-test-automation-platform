<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message as antMessage, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons-vue";
import {
  createPlatformSetting,
  deletePlatformSetting,
  getPlatformSettings,
  updatePlatformSetting,
} from "../services/api";
import type { PlatformSetting } from "../types";

interface SettingForm {
  setting_id: string;
  name: string;
  value: string;
  description: string;
}

const settings = ref<PlatformSetting[]>([]);
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const error = ref("");

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
    const data = await getPlatformSettings();
    settings.value = data.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
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
      await createPlatformSetting(payload);
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
        <p>管理 LLM、RAG、MCP Server、pytest 和 Allure 等平台级配置，不做复杂权限系统。</p>
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

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="系统设置模块错误"
      :description="error"
    />

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
          配置会立即保存到当前 FastAPI 进程内存中；本阶段不做复杂权限系统和数据库持久化。
        </div>
      </a-form>
    </a-modal>
  </section>
</template>
