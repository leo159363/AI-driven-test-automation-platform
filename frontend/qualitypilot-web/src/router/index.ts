import { createRouter, createWebHistory } from "vue-router";
import OverviewView from "../views/OverviewView.vue";
import ApiTestingView from "../views/ApiTestingView.vue";
import TestCasesView from "../views/TestCasesView.vue";
import AutomationView from "../views/AutomationView.vue";
import ReportsView from "../views/ReportsView.vue";
import LlmAssistantView from "../views/LlmAssistantView.vue";
import KnowledgeBaseView from "../views/KnowledgeBaseView.vue";
import WebTestingView from "../views/WebTestingView.vue";
import AppTestingView from "../views/AppTestingView.vue";
import PerformanceView from "../views/PerformanceView.vue";
import CicdView from "../views/CicdView.vue";
import DocumentsView from "../views/DocumentsView.vue";
import SettingsView from "../views/SettingsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "overview", component: OverviewView },
    { path: "/api-testing", name: "api-testing", component: ApiTestingView },
    { path: "/web-testing", name: "web-testing", component: WebTestingView },
    { path: "/app-testing", name: "app-testing", component: AppTestingView },
    { path: "/performance", name: "performance", component: PerformanceView },
    { path: "/test-cases", name: "test-cases", component: TestCasesView },
    { path: "/automation", name: "automation", component: AutomationView },
    { path: "/reports", name: "reports", component: ReportsView },
    { path: "/cicd", name: "cicd", component: CicdView },
    { path: "/documents", name: "documents", component: DocumentsView },
    { path: "/assistant", name: "assistant", component: LlmAssistantView },
    { path: "/knowledge", name: "knowledge", component: KnowledgeBaseView },
    { path: "/settings", name: "settings", component: SettingsView },
  ],
});

export default router;
