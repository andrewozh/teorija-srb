import type { Lang } from './types.js';

const translations: Record<string, Record<Lang, string>> = {
	// App
	'app.title': { sr: 'Возачки испит', ru: 'Экзамен по вождению' },

	// Home
	'home.practice': { sr: 'Сва питања', ru: 'Все вопросы' },
	'home.practice.sub': { sr: 'питања', ru: 'вопросов' },
	'home.exam': { sr: 'Испит', ru: 'Экзамен' },
	'home.exam.passed': { sr: 'положених', ru: 'сдано' },
	'home.exam.of': { sr: 'од', ru: 'из' },
	'home.exam.attempts': { sr: 'покушаја', ru: 'попыток' },
	'home.mistakes': { sr: 'Моје грешке', ru: 'Мои ошибки' },
	'home.mistakes.sub': { sr: 'питања за понављање', ru: 'вопросов на повторение' },
	'home.stats': { sr: 'Статистика', ru: 'Статистика' },
	'home.stats.sub': { sr: 'Преглед напретка', ru: 'Обзор прогресса' },

	// Practice
	'practice.title': { sr: 'Сва питања', ru: 'Все вопросы' },
	'practice.questions': { sr: 'питања', ru: 'вопросов' },

	// Question
	'question.next': { sr: 'Даље', ru: 'Далее' },
	'question.confirm': { sr: 'Потврди', ru: 'Подтвердить' },
	'question.multi': { sr: 'Више одговора', ru: 'Несколько ответов' },
	'question.no_answer': { sr: 'Нема одговора', ru: 'Нет ответа' },
	'question.correct': { sr: 'Тачно!', ru: 'Верно!' },
	'question.wrong': { sr: 'Нетачно!', ru: 'Неверно!' },

	// Exam
	'exam.title': { sr: 'Испит', ru: 'Экзамен' },
	'exam.start': { sr: 'Започни испит', ru: 'Начать экзамен' },
	'exam.desc': { sr: '41 питање, 45 минута', ru: '41 вопрос, 45 минут' },
	'exam.max_errors': { sr: 'Дозвољено највише 5 грешака', ru: 'Допускается не более 5 ошибок' },
	'exam.finish': { sr: 'Заврши', ru: 'Завершить' },
	'exam.passed': { sr: 'Положен!', ru: 'Сдан!' },
	'exam.failed': { sr: 'Није положен', ru: 'Не сдан' },
	'exam.score': { sr: 'Резултат', ru: 'Результат' },
	'exam.errors': { sr: 'грешака', ru: 'ошибок' },
	'exam.review': { sr: 'Преглед грешака', ru: 'Обзор ошибок' },
	'exam.back': { sr: 'На почетну', ru: 'На главную' },

	// Mistakes
	'mistakes.title': { sr: 'Моје грешке', ru: 'Мои ошибки' },
	'mistakes.empty': { sr: 'Нема грешака! Свака част!', ru: 'Нет ошибок! Молодец!' },
	'mistakes.practice': { sr: 'Вежбај грешке', ru: 'Практика ошибок' },

	// Statistics
	'stats.title': { sr: 'Статистика', ru: 'Статистика' },
	'stats.overall': { sr: 'Укупан напредак', ru: 'Общий прогресс' },
	'stats.sections': { sr: 'По секцијама', ru: 'По разделам' },
	'stats.exams': { sr: 'Историја испита', ru: 'История экзаменов' },
	'stats.no_exams': { sr: 'Нема испита', ru: 'Нет экзаменов' },

	// Settings
	'settings.title': { sr: 'Подешавања', ru: 'Настройки' },
	'settings.theme': { sr: 'Тема', ru: 'Тема' },
	'settings.theme.light': { sr: 'Светла', ru: 'Светлая' },
	'settings.theme.dark': { sr: 'Тамна', ru: 'Тёмная' },
	'settings.theme.system': { sr: 'Систем', ru: 'Система' },
	'settings.font': { sr: 'Величина слова', ru: 'Размер шрифта' },
	'settings.export': { sr: 'Извоз напретка', ru: 'Экспорт прогресса' },
	'settings.import': { sr: 'Увоз напретка', ru: 'Импорт прогресса' },
	'settings.reset': { sr: 'Обриши напредак', ru: 'Сбросить прогресс' },
	'settings.reset.confirm': { sr: 'Да ли сте сигурни?', ru: 'Вы уверены?' },
	'settings.reset.yes': { sr: 'Да, обриши', ru: 'Да, сбросить' },
	'settings.about': { sr: 'О апликацији', ru: 'О приложении' },

	// Section names
	'section.pravila_saobracaja': { sr: 'Правила саобраћаја', ru: 'Правила дорожного движения' },
	'section.saobracajna_signalizacija': { sr: 'Саобраћајна сигнализација', ru: 'Дорожные знаки и сигналы' },
	'section.vozaci': { sr: 'Возачи', ru: 'Водители' },
	'section.vozila': { sr: 'Возила', ru: 'Транспортные средства' },
	'section.osnove_bezbednosti': { sr: 'Основе безбедности', ru: 'Основы безопасности' },
	'section.posebne_mere': { sr: 'Посебне мере', ru: 'Особые меры' },
	'section.posledice': { sr: 'Последице', ru: 'Последствия нарушений' },

	// Common
	'common.back': { sr: 'Назад', ru: 'Назад' },
	'common.of': { sr: 'од', ru: 'из' },
};

export function t(key: string, lang: Lang): string {
	return translations[key]?.[lang] ?? translations[key]?.['sr'] ?? key;
}

export function sectionName(sectionId: string, lang: Lang): string {
	return t(`section.${sectionId}`, lang);
}
