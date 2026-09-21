<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { facts } from "../facts";
import { api, auth } from "../api";
import { days, time } from "../utils";
import { scheduleCategory } from "../scheduleCategories";
const schedule = ref(null),
  teacherCount = ref(0),
  loading = ref(true),
  error = ref(""),
  stale = ref(false);
const greeting = computed(() => (auth.user?.full_name || "").split(" ")[0]);
const groupName = computed(
  () => auth.user?.university_group || "Группа не выбрана",
);
const today = () =>
  new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Moscow" }).format(
    new Date(),
  );
const currentWeek = computed(() => {
  const weeks = schedule.value?.weeks || [],
    now = today();
  return (
    weeks.find((w) => w.start <= now && w.end >= now) ||
    weeks.find((w) => w.start > now) ||
    null
  );
});
const lessons = computed(() => currentWeek.value?.lessons || []);
const preview = computed(() => {
  const now = today(),
    clock = new Intl.DateTimeFormat("sv-SE", {
      timeZone: "Europe/Moscow",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date());
  return (schedule.value?.weeks || [])
    .flatMap((w) => w.lessons)
    .filter(
      (x) =>
        x.date > now || (x.date === now && x.end_time.slice(0, 5) >= clock),
    )
    .sort((a, b) =>
      (a.date + a.start_time).localeCompare(b.date + b.start_time),
    )
    .slice(0, 3);
});
const factIndex = ref(Math.floor(Math.random() * facts.length)),
  fact = computed(() => facts[factIndex.value]),
  factsPaused = ref(false);
let factTimer;
function nextFact() {
  const choice = Math.floor(Math.random() * (facts.length - 1));
  factIndex.value = choice >= factIndex.value ? choice + 1 : choice;
}
onMounted(() => {
  factTimer = setInterval(() => {
    if (!factsPaused.value && !document.hidden) nextFact();
  }, 16000);
  load();
});
onUnmounted(() => clearInterval(factTimer));
async function load() {
  loading.value = true;
  error.value = "";
  if (!auth.user?.university_group) {
    loading.value = false;
    return;
  }
  try {
    const [result, directory] = await Promise.all([
      api(
        "university/?" +
          new URLSearchParams({ name: auth.user.university_group }),
      ),
      api("university/"),
    ]);
    schedule.value = result.data;
    stale.value = result.stale || directory.stale;
    teacherCount.value = directory.data.filter(
      (x) => scheduleCategory(x.name) === "teacher",
    ).length;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
const formatDate = (value) =>
  new Date(value + "T12:00:00").toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
</script>
<template>
  <section>
    <div class="page-heading">
      <div>
        <span class="eyebrow">ВАШЕ УЧЕБНОЕ ПРОСТРАНСТВО</span>
        <h1>Здравствуйте, {{ greeting }}<span class="accent">.</span></h1>
        <p>Настоящее расписание вашей основной группы.</p>
      </div>
      <span class="role-chip"
        ><span class="status-dot" />{{
          auth.user?.is_admin ? "Режим администратора" : "Личный портал"
        }}</span
      >
    </div>
    <v-alert v-if="stale" type="warning" variant="tonal" class="mb-5"
      >Источник РГЭУ недоступен. Показана последняя сохранённая версия.</v-alert
    ><v-alert v-if="error" type="error" variant="tonal" class="mb-5"
      >{{ error }}<v-btn variant="text" @click="load">Повторить</v-btn></v-alert
    ><v-alert
      v-if="!auth.user?.university_group && !loading"
      type="info"
      variant="tonal"
      class="mb-5"
      >Выберите основную группу в профиле, чтобы увидеть план.</v-alert
    >
    <div class="dashboard-hero">
      <div class="dashboard-hero__copy">
        <Transition name="fact" mode="out-in"
          ><div :key="factIndex" class="dashboard-fact">
            <span class="dashboard-hero__tag"
              ><v-icon size="16">mdi-sparkles</v-icon>А ВЫ ЗНАЛИ? ·
              {{ fact.category }}</span
            >
            <h2>{{ fact.title }}</h2>
            <p>{{ fact.text }}</p>
            <a
              :href="fact.source"
              target="_blank"
              rel="noopener noreferrer"
              class="fact-source"
              >Подробнее <v-icon size="13">mdi-arrow-top-right</v-icon></a
            >
          </div></Transition
        >
        <div class="fact-controls">
          <button @click="nextFact">
            <v-icon size="16">mdi-shuffle-variant</v-icon> Ещё факт</button
          ><button
            :aria-pressed="factsPaused"
            @click="factsPaused = !factsPaused"
          >
            <v-icon size="16">{{
              factsPaused ? "mdi-play" : "mdi-pause"
            }}</v-icon>
          </button>
        </div>
        <v-btn to="/schedule" color="white" append-icon="mdi-arrow-right"
          >Открыть расписание</v-btn
        >
      </div>
      <div class="week-preview">
        <div class="week-preview__heading">
          <span
            ><v-icon size="18">mdi-calendar-week-outline</v-icon>
            {{ groupName }}</span
          ><span>{{ currentWeek?.name || "Текущая неделя" }}</span>
        </div>
        <div class="week-preview__days">
          <div v-for="item in days.slice(0, 6)" :key="item.value">
            <span>{{ item.short }}</span>
            <div
              :class="{
                'has-lessons': lessons.some(
                  (x) => x.day_of_week === item.value,
                ),
              }"
            >
              {{
                loading
                  ? "—"
                  : lessons.filter((x) => x.day_of_week === item.value).length
              }}
            </div>
          </div>
        </div>
        <div class="week-preview__footer">
          <span class="status-dot" />
          {{ loading ? "Загружаем…" : lessons.length + " занятий на неделе" }}
        </div>
      </div>
    </div>
    <div class="stats-grid">
      <RouterLink to="/schedule" class="stat-card surface"
        ><span class="stat-card__icon stat-card__icon--purple"
          ><v-icon>mdi-calendar-check-outline</v-icon></span
        >
        <div>
          <strong>{{ loading ? "—" : lessons.length }}</strong
          ><span>Занятий · {{ currentWeek?.name || "нет недели" }}</span>
        </div></RouterLink
      ><RouterLink to="/teachers" class="stat-card surface"
        ><span class="stat-card__icon stat-card__icon--green"
          ><v-icon>mdi-account-school-outline</v-icon></span
        >
        <div>
          <strong>{{ loading ? "—" : teacherCount }}</strong
          ><span>Преподавателей в справочнике</span>
        </div></RouterLink
      ><RouterLink to="/profile" class="stat-card surface"
        ><span class="stat-card__icon stat-card__icon--orange"
          ><v-icon>mdi-account-check-outline</v-icon></span
        >
        <div>
          <strong>{{ auth.user?.university_group || "—" }}</strong
          ><span>Основная группа</span>
        </div></RouterLink
      >
    </div>
    <div class="dashboard-bottom">
      <div class="section-heading">
        <h2>Ближайшие занятия</h2>
        <RouterLink to="/schedule"
          >Всё расписание <v-icon size="17">mdi-arrow-right</v-icon></RouterLink
        >
      </div>
      <div class="surface plan-list">
        <div v-if="loading" class="loading-state">Загружаем занятия…</div>
        <p v-else-if="!preview.length" class="empty-inline">
          Ближайших занятий не найдено.
        </p>
        <RouterLink
          v-for="lesson in preview"
          :key="lesson.id"
          :to="{
            path: '/schedule',
            query: { name: auth.user?.university_group },
          }"
          class="plan-row"
          ><div class="plan-row__time">
            {{ time(lesson.start_time)
            }}<small>{{ formatDate(lesson.date) }}</small>
          </div>
          <div>
            <strong>{{ lesson.subject_name }}</strong
            ><small
              >{{ lesson.teacher_name }} · ауд.
              {{ lesson.classroom_number }}</small
            >
          </div>
          <v-icon size="20">mdi-chevron-right</v-icon></RouterLink
        >
      </div>
    </div>
  </section>
</template>
