// The search API has no category field. Classify only recognizable names;
// administrative entries and unknown formats do not enter the student search.
export const scheduleCategories = [
  { value: "full-time", title: "Очное" },
  { value: "part-time", title: "Заочное" },
  { value: "mixed", title: "Очно-заочное" },
  { value: "teacher", title: "Преподаватели" },
];

export function scheduleCategory(name) {
  const value = name.trim();
  const group = value.match(/^([А-ЯЁA-Z]+)-\d+$/iu);
  if (group) {
    const prefix = group[1].toUpperCase();
    if (/[OО][ZЗ]S?$/.test(prefix)) return "mixed";
    if (/[ZЗ]S?$/.test(prefix)) return "part-time";
    return "full-time";
  }
  if (/[А-ЯЁ][А-ЯЁа-яё-]+\s+[А-ЯЁA-Z]\s*\.\s*[А-ЯЁA-Z]\s*\.$/u.test(value))
    return "teacher";
  return null;
}
