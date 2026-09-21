<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { auth, signOut } from "./api";
const route = useRoute(),
  router = useRouter();
const mobileMenu = ref(false),
  logoutError = ref(""),
  exiting = ref(false);
const navigation = [
  { path: "/", title: "Обзор", icon: "mdi-view-dashboard-outline" },
  {
    path: "/schedule",
    title: "Расписание",
    icon: "mdi-calendar-month-outline",
  },
  {
    path: "/teachers",
    title: "Преподаватели",
    icon: "mdi-account-school-outline",
  },
  { path: "/campus", title: "Корпуса", icon: "mdi-office-building-outline" },
];
const initials = computed(() =>
  auth.user?.full_name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase(),
);
const inPortal = computed(
  () => !!auth.user && !["/login", "/register"].includes(route.path),
);
const today = new Intl.DateTimeFormat("ru", {
  day: "numeric",
  month: "long",
  weekday: "long",
}).format(new Date());
async function logout() {
  exiting.value = true;
  logoutError.value = "";
  mobileMenu.value = false;
  try {
    await signOut();
    mobileMenu.value = false;
    await router.replace("/login");
  } catch (e) {
    logoutError.value = e.message;
  } finally {
    exiting.value = false;
  }
}
</script>
<template>
  <v-app>
    <div v-if="!auth.ready" class="boot">
      <v-progress-circular indeterminate color="primary" />
      <p>Открываем ваш портал…</p>
    </div>
    <template v-else>
      <aside v-if="inPortal" class="sidebar">
        <RouterLink to="/" class="brand"
          ><span class="brand__mark">Р</span
          ><span
            >РГЭУ <b>(РИНХ)</b><small>Университетский портал</small></span
          ></RouterLink
        >
        <p class="sidebar__label">УЧЕБНЫЙ ПРОЦЕСС</p>
        <nav aria-label="Основная навигация">
          <RouterLink
            v-for="item in navigation"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ 'nav-link--active': route.path === item.path }"
            ><v-icon size="21">{{ item.icon }}</v-icon
            >{{ item.title
            }}<span v-if="route.path === item.path" class="nav-link__dot"
          /></RouterLink>
        </nav>
        <div class="sidebar__bottom">
          <RouterLink
            to="/profile"
            class="nav-link"
            :class="{ 'nav-link--active': route.path === '/profile' }"
            ><v-icon size="21">mdi-account-circle-outline</v-icon>Личный
            кабинет</RouterLink
          ><a v-if="auth.user?.is_admin" href="/admin/" class="nav-link"
            ><v-icon size="21">mdi-shield-crown-outline</v-icon
            >Администрирование</a
          ><a v-if="auth.user?.is_admin" href="/api/export/" class="nav-link"
            ><v-icon size="21">mdi-download-outline</v-icon>Экспорт данных</a
          ><button
            class="nav-link nav-link--logout"
            :disabled="exiting"
            @click="logout"
          >
            <v-icon size="21">mdi-logout</v-icon
            >{{ exiting ? "Выходим…" : "Выйти" }}
          </button>
        </div>
      </aside>
      <div :class="inPortal ? 'portal' : 'entry'">
        <header v-if="inPortal" class="topbar">
          <div class="topbar__left">
            <v-btn
              class="mobile-toggle"
              icon="mdi-menu"
              variant="text"
              aria-label="Открыть меню"
              @click="mobileMenu = true"
            /><span class="topbar__breadcrumb"
              >Университет <v-icon size="15">mdi-chevron-right</v-icon>
              <b>{{ route.meta.title }}</b></span
            >
          </div>
          <div class="topbar__right">
            <span class="topbar__date">{{ today }}</span
            ><RouterLink
              to="/profile"
              class="user-badge"
              aria-label="Открыть личный кабинет"
              ><span class="avatar">{{ initials }}</span
              ><span
                >{{ auth.user?.full_name
                }}<small>{{
                  auth.user?.is_admin ? "Администратор" : "Пользователь"
                }}</small></span
              ></RouterLink
            >
          </div>
        </header>
        <v-main :class="inPortal ? 'portal__main' : 'entry__main'"
          ><v-alert
            v-if="logoutError"
            type="error"
            variant="tonal"
            class="mb-5"
            >{{ logoutError }}</v-alert
          >
          <RouterView v-slot="{ Component }"
            ><Transition name="page" mode="out-in"
              ><component :is="Component" :key="route.path" /></Transition
          ></RouterView>
          <footer v-if="inPortal" class="portal__footer">
            <span>РГЭУ (РИНХ) · Университетский портал</span
            ><RouterLink to="/profile"
              >Мой профиль
              <v-icon size="14">mdi-arrow-top-right</v-icon></RouterLink
            >
          </footer>
        </v-main>
      </div>
      <v-dialog v-if="inPortal" v-model="mobileMenu" max-width="380"
        ><v-card rounded="xl"
          ><v-card-title class="d-flex justify-space-between align-center"
            >Навигация<v-btn
              icon="mdi-close"
              variant="text"
              aria-label="Закрыть меню"
              @click="mobileMenu = false" /></v-card-title
          ><v-card-text
            ><nav class="mobile-nav">
              <RouterLink
                v-for="item in [
                  ...navigation,
                  {
                    path: '/profile',
                    title: 'Личный кабинет',
                    icon: 'mdi-account-circle-outline',
                  },
                ]"
                :key="item.path"
                :to="item.path"
                class="nav-link"
                @click="mobileMenu = false"
                ><v-icon>{{ item.icon }}</v-icon
                >{{ item.title }}</RouterLink
              ><a v-if="auth.user?.is_admin" href="/admin/" class="nav-link"
                ><v-icon>mdi-shield-crown-outline</v-icon>Администрирование</a
              ><a
                v-if="auth.user?.is_admin"
                href="/api/export/"
                class="nav-link"
                ><v-icon>mdi-download-outline</v-icon>Экспорт данных</a
              ><button class="nav-link" :disabled="exiting" @click="logout">
                <v-icon>mdi-logout</v-icon>Выйти
              </button>
            </nav></v-card-text
          ></v-card
        ></v-dialog
      >
    </template>
  </v-app>
</template>
