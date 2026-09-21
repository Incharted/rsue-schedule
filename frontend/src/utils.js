export const days = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
].map((title, i) => ({
  title,
  value: i + 1,
  short: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][i],
}));
export const time = (value) => value.slice(0, 5);
