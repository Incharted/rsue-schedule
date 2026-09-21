-- 1. Расписание ИСТ-311: понедельник, нечётная неделя.
SELECT l.start_time, l.end_time, s.name AS subject,
       t.full_name AS teacher, c.number AS classroom, b.name AS building
FROM schedule_lesson l
JOIN schedule_group g ON g.id = l.group_id
JOIN schedule_subject s ON s.id = l.subject_id
JOIN schedule_teacher t ON t.id = l.teacher_id
JOIN schedule_classroom c ON c.id = l.classroom_id
JOIN schedule_building b ON b.id = c.building_id
WHERE g.name = 'ИСТ-311' AND l.day_of_week = 1 AND l.week_type = 'odd'
ORDER BY l.start_time, l.id;

-- 2. Группы, занимающиеся в аудитории 212 главного корпуса в среду.
-- Тип недели не ограничиваем: учитываем обе недели.
SELECT DISTINCT g.name AS group_name
FROM schedule_lesson l
JOIN schedule_group g ON g.id = l.group_id
JOIN schedule_classroom c ON c.id = l.classroom_id
JOIN schedule_building b ON b.id = c.building_id
WHERE c.number = '212' AND b.name = 'Главный корпус' AND l.day_of_week = 3
ORDER BY g.name;

-- 3. Расписание Долженко А.И. на все недели.
SELECT l.week_type, l.day_of_week, l.start_time, l.end_time,
       g.name AS group_name, s.name AS subject,
       c.number AS classroom, b.name AS building
FROM schedule_lesson l
JOIN schedule_teacher t ON t.id = l.teacher_id
JOIN schedule_group g ON g.id = l.group_id
JOIN schedule_subject s ON s.id = l.subject_id
JOIN schedule_classroom c ON c.id = l.classroom_id
JOIN schedule_building b ON b.id = c.building_id
WHERE t.full_name = 'Долженко А.И.'
ORDER BY l.week_type, l.day_of_week, l.start_time, l.id;
