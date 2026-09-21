<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../api";
const buildings = ref([]),
  search = ref(""),
  loading = ref(true),
  error = ref("");
const displayName = (building) =>
  building.name === "Главный корпус" ? "РГЭУ (РИНХ)" : building.name;
const filtered = computed(() =>
  buildings.value.filter((building) =>
    (displayName(building) + " " + building.address)
      .toLowerCase()
      .includes(search.value.toLowerCase().trim()),
  ),
);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    buildings.value = await api("buildings/");
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
        <span class="eyebrow">ОРИЕНТИРУЙТЕСЬ ЛЕГКО</span>
        <h1>Кампус<span class="accent">.</span></h1>
        <p>Проверенные адреса учебных площадок РГЭУ (РИНХ).</p>
      </div>
      <span class="role-chip">Площадок: {{ buildings.length }}</span>
    </div>
    <v-text-field
      v-model="search"
      label="Найти площадку или адрес"
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
      <v-progress-circular indeterminate color="primary" />Загружаем кампус…
    </div>
    <div v-else-if="!error && !filtered.length" class="empty-state surface">
      <v-icon size="32">mdi-map-search-outline</v-icon>
      <h3>Площадка не найдена</h3>
      <p>Проверьте название или адрес.</p>
    </div>
    <div v-else class="campus-grid">
      <article
        v-for="(building, index) in filtered"
        :key="building.id"
        class="building-card surface"
      >
        <div
          class="building-card__art"
          :class="{ 'building-card__art--green': index % 2 }"
        >
          <v-icon size="72">mdi-office-building-outline</v-icon
          ><span>РГЭУ (РИНХ)</span>
          <div class="building-card__art-lines" />
        </div>
        <div class="building-card__content">
          <span class="eyebrow">УЧЕБНАЯ ПЛОЩАДКА</span>
          <h2>{{ displayName(building) }}</h2>
          <p class="building-card__address">
            <v-icon size="17">mdi-map-marker-outline</v-icon
            >{{ building.address }}
          </p>
          <a
            :href="
              'https://yandex.ru/maps/?text=' +
              encodeURIComponent(building.address)
            "
            target="_blank"
            rel="noopener noreferrer"
            >Показать на карте <v-icon size="15">mdi-arrow-top-right</v-icon></a
          >
        </div>
      </article>
    </div>
  </section>
</template>
