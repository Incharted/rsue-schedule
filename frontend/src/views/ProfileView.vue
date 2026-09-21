<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { api, auth } from "../api";
import { scheduleCategories, scheduleCategory } from "../scheduleCategories";
const entries = ref([]),
  loading = ref(true),
  saving = ref(false),
  error = ref(""),
  notice = ref(false),
  sourceStale = ref(false);
const form = ref({
  full_name: auth.user?.full_name || "",
  email: auth.user?.email || "",
  study_form: auth.user?.study_form || "",
  university_group: auth.user?.university_group || "",
});
const studyForms = scheduleCategories.filter(
  (item) => item.value !== "teacher",
);
const groups = computed(() =>
  entries.value
    .filter((item) => scheduleCategory(item.name) === form.value.study_form)
    .sort((a, b) => a.name.localeCompare(b.name, "ru", { numeric: true })),
);
const initials = computed(() =>
  (auth.user?.full_name || "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase(),
);
watch(
  () => form.value.study_form,
  () => {
    if (
      form.value.university_group &&
      scheduleCategory(form.value.university_group) !== form.value.study_form
    )
      form.value.university_group = "";
  },
);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api("university/");
    entries.value = result.data;
    sourceStale.value = result.stale;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
async function save() {
  saving.value = true;
  error.value = "";
  try {
    auth.user = await api("auth/profile/", {
      method: "PATCH",
      body: JSON.stringify(form.value),
    });
    notice.value = true;
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
onMounted(load);
</script>
<template>
  <section>
    <div class="page-heading">
      <div>
        <span class="eyebrow">ВАШЕ ЛИЧНОЕ ПРОСТРАНСТВО</span>
        <h1>Личный кабинет<span class="accent">.</span></h1>
        <p>
          Основная группа хранится в аккаунте и доступна на всех устройствах.
        </p>
      </div>
    </div>
    <v-alert v-if="sourceStale" type="warning" variant="tonal" class="mb-5"
      >Справочник университета временно недоступен. Используется последняя
      сохранённая версия.</v-alert
    >
    <div class="profile-grid">
      <aside class="profile-summary surface">
        <span class="profile-avatar">{{ initials }}</span>
        <h2>{{ auth.user?.full_name }}</h2>
        <p>@{{ auth.user?.username }}</p>
        <span class="role-chip"
          ><v-icon size="17">{{
            auth.user?.is_admin
              ? "mdi-shield-account-outline"
              : "mdi-account-outline"
          }}</v-icon
          >{{ auth.user?.is_admin ? "Администратор" : "Пользователь" }}</span
        >
        <div class="profile-summary__group">
          <span class="mini-label">МОЯ ГРУППА</span
          ><strong>{{
            auth.user?.university_group || "Ещё не выбрана"
          }}</strong>
        </div>
      </aside>
      <div class="profile-form surface">
        <h2>Основная информация</h2>
        <p class="muted mb-7">Данные аккаунта и группа из справочника РГЭУ.</p>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-5"
          >{{ error
          }}<v-btn v-if="!entries.length" variant="text" @click="load"
            >Повторить</v-btn
          ></v-alert
        >
        <form class="lesson-form" @submit.prevent="save">
          <v-text-field
            v-model="form.full_name"
            label="Имя и фамилия"
            autocomplete="name"
            variant="outlined"
            hide-details
            required
            maxlength="150"
          /><v-text-field
            v-model="form.email"
            label="Электронная почта"
            autocomplete="email"
            type="email"
            variant="outlined"
            hide-details
            required
          /><v-select
            v-model="form.study_form"
            :items="studyForms"
            item-title="title"
            item-value="value"
            label="Форма обучения"
            variant="outlined"
            hide-details
            clearable
          /><v-autocomplete
            v-model="form.university_group"
            :items="groups"
            item-title="name"
            item-value="name"
            label="Основная учебная группа"
            variant="outlined"
            hide-details
            clearable
            :loading="loading"
            :disabled="!form.study_form || loading"
            no-data-text="Группы не найдены"
          />
          <p class="field-note">
            Расписание и главная будут открываться для этой группы.
          </p>
          <div class="profile-form__actions">
            <v-btn
              type="submit"
              color="primary"
              :loading="saving"
              :disabled="loading"
              prepend-icon="mdi-check"
              >Сохранить изменения</v-btn
            >
          </div>
        </form>
      </div>
    </div>
    <v-snackbar v-model="notice" color="primary" timeout="3000"
      >Профиль сохранён</v-snackbar
    >
  </section>
</template>
