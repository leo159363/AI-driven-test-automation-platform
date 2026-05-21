import { createRouter, createWebHistory } from "vue-router";
import OverviewView from "../views/OverviewView.vue";
import ApiTestingView from "../views/ApiTestingView.vue";
import TestCasesView from "../views/TestCasesView.vue";
import AutomationView from "../views/AutomationView.vue";
import ReportsView from "../views/ReportsView.vue";
import LlmAssistantView from "../views/LlmAssistantView.vue";
import KnowledgeBaseView from "../views/KnowledgeBaseView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "overview", component: OverviewView },
    { path: "/api-testing", name: "api-testing", component: ApiTestingView },
    { path: "/test-cases", name: "test-cases", component: TestCasesView },
    { path: "/automation", name: "automation", component: AutomationView },
    { path: "/reports", name: "reports", component: ReportsView },
    { path: "/assistant", name: "assistant", component: LlmAssistantView },
    { path: "/knowledge", name: "knowledge", component: KnowledgeBaseView },
  ],
});

export default router;

