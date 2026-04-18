import { base } from '$app/paths';
import type { Question, QuestionsData, SectionMeta, Chunk, Lang, Option } from './types.js';

let cachedData: QuestionsData | null = null;

export async function loadQuestions(): Promise<QuestionsData> {
	if (cachedData) return cachedData;
	const res = await fetch(`${base}/questions.json`);
	cachedData = (await res.json()) as QuestionsData;
	return cachedData;
}

export function getActiveQuestions(data: QuestionsData): Question[] {
	return data.questions.filter((q) => !q.is_removed);
}

export function getSections(data: QuestionsData): SectionMeta[] {
	return data.metadata.sections;
}

export function getQuestionsBySection(data: QuestionsData, sectionId: string): Question[] {
	return data.questions.filter((q) => q.section === sectionId && !q.is_removed);
}

export function getChunks(questions: Question[], chunkSize = 20): Chunk[] {
	const chunks: Chunk[] = [];
	for (let i = 0; i < questions.length; i += chunkSize) {
		const slice = questions.slice(i, i + chunkSize);
		chunks.push({
			index: Math.floor(i / chunkSize),
			start: i,
			end: Math.min(i + chunkSize, questions.length),
			questions: slice
		});
	}
	return chunks;
}

export function getRandomExamQuestions(data: QuestionsData, count = 41): Question[] {
	const active = getActiveQuestions(data).filter((q) => q.correct_answers && q.correct_answers.length > 0);
	const shuffled = [...active].sort(() => Math.random() - 0.5);
	return shuffled.slice(0, count);
}

export function questionKey(q: Question): string {
	return `${q.section}:${q.id}`;
}

export function parseQuestionKey(key: string): { section: string; id: number } {
	const [section, idStr] = key.split(':');
	return { section, id: parseInt(idStr, 10) };
}

export function sectionIcon(sectionId: string): string {
	const icons: Record<string, string> = {
		pravila_saobracaja: '🚦',
		saobracajna_signalizacija: '🪧',
		vozaci: '🧑‍✈️',
		vozila: '🚗',
		osnove_bezbednosti: '🛡️',
		posebne_mere: '⚖️',
		posledice: '⚠️'
	};
	return icons[sectionId] || '📋';
}

/** Get localized question text. Falls back to Serbian if translation missing. */
export function qText(q: Question, lang: Lang): string {
	if (lang === 'ru' && q.text_ru) return q.text_ru;
	return q.text;
}

/** Get localized option text. Falls back to Serbian if translation missing. */
export function oText(o: Option, lang: Lang): string {
	if (lang === 'ru' && o.text_ru) return o.text_ru;
	return o.text;
}

export function sectionColor(sectionId: string): string {
	const colors: Record<string, string> = {
		pravila_saobracaja: '#3b82f6',
		saobracajna_signalizacija: '#f59e0b',
		vozaci: '#8b5cf6',
		vozila: '#06b6d4',
		osnove_bezbednosti: '#10b981',
		posebne_mere: '#ef4444',
		posledice: '#f97316'
	};
	return colors[sectionId] || '#6b7280';
}
