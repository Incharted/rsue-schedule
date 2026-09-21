import { createRouter, createWebHistory } from "vue-router";
import { auth, initializeSession } from "./api";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0, behavior: "smooth" }),
  routes: [
    {
      path: "/login",
      component: () => import("./views/AuthView.vue"),
      meta: { public: true, title: "Вход" },
    },
    {
      path: "/register",
      component: () => import("./views/AuthView.vue"),
      meta: { public: true, title: "Регистрация" },
    },
    {
      path: "/",
      component: () => import("./views/DashboardView.vue"),
      meta: { title: "Обзор" },
    },
    {
      path: "/schedule",
      component: () => import("./views/ScheduleView.vue"),
      meta: { title: "Расписание" },
    },
    {
      path: "/teachers",
      component: () => import("./views/TeachersView.vue"),
      meta: { title: "Преподаватели" },
    },
    {
      path: "/campus",
      component: () => import("./views/CampusView.vue"),
      meta: { title: "Корпуса" },
    },
    {
      path: "/profile",
      component: () => import("./views/ProfileView.vue"),
      meta: { title: "Личный кабинет" },
    },
    {
      path: "/:pathMatch(.*)*",
      component: () => import("./views/NotFoundView.vue"),
      meta: { title: "Страница не найдена" },
    },
  ],
});
router.beforeEach(async (to) => {
  await initializeSession();
  if (!to.meta.public && !auth.user)
    return { path: "/login", query: { redirect: to.fullPath } };
  if (["/login", "/register"].includes(to.path) && auth.user) return "/";
  document.title = to.meta.title + " · РГЭУ (РИНХ)";
});
window.addEventListener("session-expired", () =>
  router.replace({
    path: "/login",
    query: { redirect: router.currentRoute.value.fullPath },
  }),
);
export default router;
