<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, auth, refreshSession } from "../api";
const route = useRoute(),
  router = useRouter();
const registering = computed(() => route.path === "/register");
const form = ref({
  username: "",
  full_name: "",
  email: "",
  password: "",
  password2: "",
  remember: true,
});
const error = ref(""),
  busy = ref(false),
  showPassword = ref(false);
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    await refreshSession();
    const payload = registering.value
      ? {
          username: form.value.username,
          full_name: form.value.full_name,
          email: form.value.email,
          password1: form.value.password,
          password2: form.value.password2,
        }
      : {
          username: form.value.username,
          password: form.value.password,
          remember: form.value.remember,
        };
    await api(registering.value ? "auth/register/" : "auth/login/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const redirect = route.query.redirect;
    await router.replace(
      typeof redirect === "string" &&
        redirect.startsWith("/") &&
        !redirect.startsWith("//") &&
        !redirect.startsWith("/login") &&
        !redirect.startsWith("/register")
        ? redirect
        : "/",
    );
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <div class="auth-page">
    <section class="auth-story">
      <div class="brand brand--light">
        <span class="brand__mark">Р</span
        ><span>РГЭУ <b>(РИНХ)</b><small>Университетский портал</small></span>
      </div>
      <div class="auth-story__content">
        <span class="auth-story__eyebrow"
          ><span class="status-dot" />РИТМ УНИВЕРСИТЕТА</span
        >
        <h1>Ваш день.<br />Ваши планы.<br /><em>Ваш университет.</em></h1>
        <p>
          Расписание, преподаватели и аудитории —<br />в пространстве, созданном
          для учёбы.
        </p>
        <div class="auth-preview">
          <div class="auth-preview__top">
            <span
              ><v-icon size="19">mdi-calendar-outline</v-icon> Ваше
              расписание</span
            ><span class="auth-preview__tag">По данным РГЭУ</span>
          </div>
          <div class="auth-preview__lesson">
            <div>08:30<small>10:00</small></div>
            <span
              ><b>Математика</b
              ><small>доц. Иванова Е.А. · аудитория 311</small></span
            ><v-icon size="20">mdi-arrow-top-right</v-icon>
          </div>
          <div class="auth-preview__line" />
          <div class="auth-preview__bottom">
            <span class="auth-preview__avatars"
              ><i><v-icon size="15">mdi-account-school-outline</v-icon></i
              ><i><v-icon size="15">mdi-account-group-outline</v-icon></i></span
            ><span
              >Преподаватели и группы<br /><small
                >Актуальный университетский справочник</small
              ></span
            >
          </div>
        </div>
      </div>
      <div class="auth-story__footer">
        <span>Ростов-на-Дону</span><span>Учиться. Планировать. Успевать.</span>
      </div>
    </section>
    <main class="auth-panel">
      <div class="auth-panel__mobile-brand">РГЭУ <b>(РИНХ)</b></div>
      <div class="auth-panel__form">
        <div class="auth-tabs">
          <RouterLink to="/login" :class="{ active: !registering }"
            >Вход</RouterLink
          ><RouterLink to="/register" :class="{ active: registering }"
            >Регистрация</RouterLink
          >
        </div>
        <span class="eyebrow">{{
          registering ? "НАЧНИТЕ СВОЮ ИСТОРИЮ" : "РАДЫ ВАС ВИДЕТЬ"
        }}</span>
        <h2>
          {{ registering ? "Добро пожаловать" : "С возвращением"
          }}<span class="accent">.</span>
        </h2>
        <p class="auth-panel__intro">
          {{
            registering
              ? "Создайте аккаунт и соберите свой учебный день."
              : "Войдите, чтобы продолжить свой учебный день."
          }}
        </p>
        <v-alert
          v-if="error || auth.error"
          type="error"
          variant="tonal"
          class="mb-5 auth-error"
          >{{ error || auth.error }}</v-alert
        >
        <form @submit.prevent="submit" class="auth-form">
          <v-text-field
            v-if="registering"
            v-model="form.full_name"
            label="Имя и фамилия"
            autocomplete="name"
            variant="outlined"
            hide-details
            required
            maxlength="150"
          />
          <v-text-field
            v-model="form.username"
            label="Логин"
            autocomplete="username"
            variant="outlined"
            hide-details
            required
            maxlength="150"
            :hint="
              registering
                ? 'Латинские буквы, цифры и символы @ . + - _'
                : undefined
            "
          />
          <v-text-field
            v-if="registering"
            v-model="form.email"
            label="Электронная почта"
            type="email"
            autocomplete="email"
            variant="outlined"
            hide-details
            required
          />
          <v-text-field
            v-model="form.password"
            label="Пароль"
            :type="showPassword ? 'text' : 'password'"
            :autocomplete="registering ? 'new-password' : 'current-password'"
            variant="outlined"
            hide-details
            required
            :minlength="registering ? 8 : undefined"
            ><template #append-inner
              ><button
                type="button"
                class="password-toggle"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <v-icon size="20">{{
                  showPassword ? "mdi-eye-off-outline" : "mdi-eye-outline"
                }}</v-icon>
              </button></template
            ></v-text-field
          >
          <v-text-field
            v-if="registering"
            v-model="form.password2"
            label="Повторите пароль"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            variant="outlined"
            hide-details
            required
            minlength="8"
          />
          <p v-if="registering" class="field-note">
            От 8 символов. Используйте буквы, цифры и знаки.
          </p>
          <v-checkbox
            v-else
            v-model="form.remember"
            label="Запомнить меня на 90 дней"
            density="compact"
            hide-details
            color="primary"
          />
          <v-btn
            type="submit"
            color="primary"
            size="large"
            block
            :loading="busy"
            append-icon="mdi-arrow-right"
            >{{ registering ? "Создать аккаунт" : "Войти в портал" }}</v-btn
          >
        </form>
        <p class="auth-panel__switch">
          {{ registering ? "Уже есть аккаунт?" : "Ещё нет аккаунта?" }}
          <RouterLink :to="registering ? '/login' : '/register'">{{
            registering ? "Войти" : "Зарегистрироваться"
          }}</RouterLink>
        </p>
        <div class="auth-panel__hint">
          <v-icon size="18">mdi-shield-check-outline</v-icon
          ><span>Все права защищены</span>
        </div>
      </div>
      <footer class="auth-panel__footer">
        Расписание университета · РГЭУ (РИНХ)
      </footer>
    </main>
  </div>
</template>
