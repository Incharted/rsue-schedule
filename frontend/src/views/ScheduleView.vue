<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, auth } from "../api";
import { days, time } from "../utils";
import { scheduleCategories, scheduleCategory } from "../scheduleCategories";

const route = useRoute(),
  router = useRouter();
const entries = ref([]),
  selected = ref(""),
  schedule = ref(null);
const week = ref(""),
  day = ref(0),
  loading = ref(false),
  error = ref("");
const stale = ref(false);
let requestId = 0;
const category = ref("full-time");
const filteredEntries = computed(() =>
  entries.value
    .filter((item) => scheduleCategory(item.name) === category.value)
    .sort((a, b) => a.name.localeCompare(b.name, "ru", { numeric: true })),
);
function changeCategory(value) {
  if (category.value === value) return;
  category.value = value;
  ++requestId;
  selected.value = "";
  schedule.value = null;
  week.value = "";
  error.value = "";
  loading.value = false;
  router.replace({ path: "/schedule", query: { category: value } });
}
function selectEntry() {
  load();
}
const weekOptions = computed(() =>
  (schedule.value?.weeks || []).map((item) => ({
    title: `${formatDate(item.start)} — ${formatDate(item.end)} · ${item.name}`,
    value: item.id,
  })),
);
const lessons = computed(() =>
  (
    schedule.value?.weeks.find((item) => item.id === week.value)?.lessons || []
  ).filter((item) => !day.value || item.day_of_week === day.value),
);
function formatDate(value) {
  return new Date(value + "T12:00:00").toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
  });
}
function today() {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Moscow" }).format(
    new Date(),
  );
}
async function load() {
  if (!selected.value) return;
  const id = ++requestId;
  loading.value = true;
  error.value = "";
  schedule.value = null;
  try {
    const result = await api(
      "university/?" + new URLSearchParams({ name: selected.value }),
    );
    if (id !== requestId) return;
    schedule.value = result.data;
    stale.value = result.stale;
    const current = today();
    const weeks = result.data.weeks;
    week.value =
      (
        weeks.find((item) => item.start <= current && item.end >= current) ||
        weeks.find((item) => item.start > current) ||
        weeks.at(-1)
      )?.id || "";
    router.replace({
      path: "/schedule",
      query: { name: selected.value, category: category.value },
    });
  } catch (e) {
    if (id === requestId) error.value = e.message;
  } finally {
    if (id === requestId) loading.value = false;
  }
}
async function initialize() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api("university/");
    entries.value = result.data;
    selected.value = String(
      route.query.name || auth.user?.university_group || "",
    );
    category.value = scheduleCategory(selected.value) || "full-time";
    if (
      !route.query.name &&
      scheduleCategories.some((item) => item.value === route.query.category)
    ) {
      category.value = route.query.category;
      selected.value = "";
      loading.value = false;
    } else {
      await load();
    }
  } catch (e) {
    error.value = e.message;
    loading.value = false;
  }
}
onMounted(initialize);
</script>
<template>
  <section
    class="real-schedule"
    :class="{ 'real-schedule--guest': !auth.user }"
  >
    <div class="page-heading">
      <div>
        <span class="eyebrow">РГЭУ (РИНХ) · ОФИЦИАЛЬНОЕ РАСПИСАНИЕ</span>
        <h1>Расписание<span class="accent">.</span></h1>
        <p>Настоящие занятия, преподаватели и аудитории университета.</p>
      </div>
      <v-btn
        href="https://rasp.rsue.ru"
        target="_blank"
        rel="noopener noreferrer"
        variant="outlined"
        color="primary"
        append-icon="mdi-open-in-new"
        >Сайт университета</v-btn
      >
    </div>
    <div class="schedule-filters surface">
      <div class="category-tabs" role="group" aria-label="Раздел расписания">
        <v-btn
          v-for="item in scheduleCategories"
          :key="item.value"
          :variant="category === item.value ? 'flat' : 'tonal'"
          color="primary"
          :aria-pressed="category === item.value"
          @click="changeCategory(item.value)"
          >{{ item.title }}</v-btn
        >
      </div>
      <div class="schedule-filters__selects">
        <v-autocomplete
          v-model="selected"
          :items="filteredEntries"
          item-title="name"
          item-value="name"
          :label="category === 'teacher' ? 'Преподаватель' : 'Учебная группа'"
          @update:model-value="selectEntry"
          variant="outlined"
          hide-details
          no-data-text="Ничего не найдено"
          :disabled="!entries.length"
        />
        <v-select
          v-model="week"
          :items="weekOptions"
          label="Неделя и даты"
          variant="outlined"
          hide-details
          :disabled="loading || !weekOptions.length"
        />
      </div>
      <div class="day-tabs" role="group" aria-label="День недели">
        <button
          :class="{ active: day === 0 }"
          :aria-pressed="day === 0"
          @click="day = 0"
        >
          Вся неделя</button
        ><button
          v-for="item in days"
          :key="item.value"
          :class="{ active: day === item.value }"
          :aria-pressed="day === item.value"
          @click="day = item.value"
        >
          {{ item.short }}
        </button>
      </div>
    </div>
    <v-alert
      v-if="stale && !loading && !error"
      type="warning"
      variant="tonal"
      class="mb-5"
      >Сайт университета сейчас недоступен. Показываем последнее сохранённое
      расписание.</v-alert
    >
    <v-alert
      v-if="
        !auth.user?.university_group && !route.query.name && !loading && !error
      "
      type="info"
      variant="tonal"
      class="mb-5"
      >Основная группа пока не выбрана. Укажите её в профиле или выберите группу
      только для просмотра.</v-alert
    >
    <v-alert v-if="error" type="error" variant="tonal" class="mb-5"
      >{{ error }}
      <v-btn variant="text" @click="entries.length ? load() : initialize()"
        >Повторить</v-btn
      ></v-alert
    >
    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate color="primary" /><span
        >Загружаем расписание университета…</span
      >
    </div>
    <div v-else-if="!error && !selected" class="empty-state surface">
      <v-icon size="32">mdi-magnify</v-icon>
      <h3>
        {{
          category === "teacher"
            ? "Выберите преподавателя"
            : "Выберите учебную группу"
        }}
      </h3>
      <p>
        В поиске только выбранный раздел · {{ filteredEntries.length }} записей.
      </p>
    </div>
    <template v-else-if="!error && schedule">
      <div class="section-heading">
        <h2>
          {{ schedule.instance }}
          <span class="count-badge">{{ lessons.length }}</span>
        </h2>
        <span>{{ day ? days[day - 1].title : "Вся неделя" }}</span>
      </div>
      <div v-if="!lessons.length" class="empty-state surface">
        <v-icon size="32">mdi-calendar-check-outline</v-icon>
        <h3>Занятия не указаны</h3>
        <p>Выберите другой день или неделю.</p>
      </div>
      <div v-else class="lesson-list">
        <article
          v-for="(lesson, index) in lessons"
          :key="lesson.id"
          class="lesson surface"
          :style="{ '--row-index': Math.min(index, 5) }"
        >
          <div class="lesson__time">
            <strong>{{ time(lesson.start_time) }}</strong
            ><span>{{ time(lesson.end_time) }}</span>
          </div>
          <div class="lesson__details">
            <span class="lesson__number"
              >{{ formatDate(lesson.date) }} ·
              {{ days[lesson.day_of_week - 1].short }} · {{ lesson.kind }}</span
            >
            <h3>{{ lesson.subject_name }}</h3>
            <p>
              <v-icon size="17">mdi-account-outline</v-icon
              >{{
                schedule.kind === "Teacher"
                  ? lesson.group_name
                  : lesson.teacher_name
              }}
            </p>
            <p v-if="lesson.subgroup && lesson.subgroup !== 'Нет подгруппы'">
              {{ lesson.subgroup }}
            </p>
          </div>
          <div class="lesson__location">
            <span class="location-icon"
              ><v-icon size="20">mdi-map-marker-outline</v-icon></span
            >
            <div>
              <strong>Аудитория {{ lesson.classroom_number }}</strong>
            </div>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>
<style scoped>
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.real-schedule--guest {
  width: min(1120px, 100%);
  margin: 0 auto;
  padding: 40px 20px;
}
</style>
