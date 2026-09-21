<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../api";
import { scheduleCategory } from "../scheduleCategories";
const entries = ref([]),
  search = ref(""),
  loading = ref(true),
  error = ref(""),
  stale = ref(false);
const teachers = computed(() =>
  entries.value.filter((item) => scheduleCategory(item.name) === "teacher"),
);
const filtered = computed(() =>
  teachers.value
    .filter((item) =>
      item.name.toLowerCase().includes(search.value.toLowerCase().trim()),
    )
    .sort((a, b) => a.name.localeCompare(b.name, "ru")),
);
const visible = computed(() => filtered.value.slice(0, 30));
const initials = (name) =>
  name
    .split(" ")
    .slice(0, 2)
    .map((item) => item[0])
    .join("");
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api("university/");
    entries.value = result.data;
    stale.value = result.stale;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <section>
    <div class="page-heading">
      <div>
        <span class="eyebrow">СПРАВОЧНИК РГЭУ</span>
        <h1>Преподаватели<span class="accent">.</span></h1>
        <p>Преподаватели университета и их расписание.</p>
      </div>
      <span class="role-chip">{{ teachers.length }} в справочнике</span>
    </div>
    <v-alert v-if="stale" type="warning" variant="tonal" class="mb-5"
      >Источник недоступен. Показана сохранённая версия справочника.</v-alert
    ><v-text-field
      v-model="search"
      label="Найти по имени или фамилии"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      hide-details
      clearable
      class="search-field mb-7"
    />
    <v-alert v-if="error" type="error" variant="tonal"
      >{{ error }}<v-btn variant="text" @click="load">Повторить</v-btn></v-alert
    >
    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate color="primary" />Загружаем справочник…
    </div>
    <div v-else-if="!error && !filtered.length" class="empty-state surface">
      <v-icon size="32">mdi-account-search-outline</v-icon>
      <h3>Преподаватели не найдены</h3>
      <p>Измените поисковый запрос или повторите загрузку.</p>
    </div>
    <p
      v-if="!loading && !error && filtered.length > visible.length"
      class="muted mb-5"
    >
      Показано {{ visible.length }} из {{ filtered.length }}. Введите фамилию,
      чтобы уточнить поиск.
    </p>
    <div v-if="!loading && !error && visible.length" class="directory-grid">
      <article
        v-for="(teacher, index) in visible"
        :key="teacher.id"
        class="teacher-card surface"
      >
        <div class="teacher-card__top">
          <span
            class="teacher-avatar"
            :class="{ 'teacher-avatar--green': index % 2 }"
            >{{ initials(teacher.name) }}</span
          ><span class="mini-label">Преподаватель</span>
        </div>
        <h2>{{ teacher.name }}</h2>
        <p>РГЭУ (РИНХ)</p>
        <RouterLink
          class="card-action"
          :to="{
            path: '/schedule',
            query: { name: teacher.name, category: 'teacher' },
          }"
          >Настоящее расписание<v-icon size="19"
            >mdi-arrow-top-right</v-icon
          ></RouterLink
        >
      </article>
    </div>
  </section>
</template>
