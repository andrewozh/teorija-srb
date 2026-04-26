import { base } from '$app/paths';
import type { Question, QuestionsData, SectionMeta, Chunk, Lang, Option, Category } from './types.js';
import { getSettings, getQuestionProgress } from './store.js';

let cachedData: QuestionsData | null = null;

export async function loadQuestions(): Promise<QuestionsData> {
	if (cachedData) return cachedData;
	const res = await fetch(`${base}/questions.json`);
	cachedData = (await res.json()) as QuestionsData;
	return cachedData;
}

function matchesCategory(q: Question, cat: Category): boolean {
	// Empty categories = applies to all categories
	return !q.categories || q.categories.length === 0 || q.categories.includes(cat);
}

export function getActiveQuestions(data: QuestionsData): Question[] {
	const cat = getSettings().category;
	return data.questions.filter((q) => !q.is_removed && matchesCategory(q, cat));
}

export function getSections(data: QuestionsData): SectionMeta[] {
	return data.metadata.sections;
}

export function getQuestionsBySection(data: QuestionsData, sectionId: string): Question[] {
	const cat = getSettings().category;
	return data.questions.filter((q) => q.section === sectionId && !q.is_removed && matchesCategory(q, cat));
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

/**
 * Generate exam questions: 41 questions totaling exactly targetPoints,
 * distributed proportionally across sections.
 */
export function getRandomExamQuestions(data: QuestionsData, count = 41, targetPoints = 100): Question[] {
	const active = getActiveQuestions(data).filter((q) => q.correct_answers && q.correct_answers.length > 0);

	// Group by section
	const bySec: Record<string, Question[]> = {};
	for (const q of active) {
		if (!bySec[q.section]) bySec[q.section] = [];
		bySec[q.section].push(q);
	}

	// Proportional allocation per section
	const sectionIds = Object.keys(bySec).sort((a, b) => bySec[b].length - bySec[a].length);
	const total = active.length;
	const allocation: Record<string, number> = {};
	let allocated = 0;
	const remainders: [string, number][] = [];

	for (const s of sectionIds) {
		const exact = count * bySec[s].length / total;
		const base = Math.floor(exact);
		allocation[s] = Math.max(1, base); // at least 1 per section
		remainders.push([s, exact - base]);
		allocated += allocation[s];
	}
	// Distribute remaining slots by highest remainder
	remainders.sort((a, b) => b[1] - a[1]);
	for (const [s] of remainders) {
		if (allocated >= count) break;
		allocation[s]++;
		allocated++;
	}
	// If over-allocated (due to min 1), trim largest sections
	while (allocated > count) {
		for (const s of sectionIds) {
			if (allocation[s] > 1 && allocated > count) {
				allocation[s]--;
				allocated--;
			}
		}
	}

	// Pick random questions per section
	const shuffle = <T>(arr: T[]): T[] => [...arr].sort(() => Math.random() - 0.5);
	let selected: Question[] = [];
	const pools: Record<string, Question[]> = {};
	for (const s of sectionIds) {
		const pool = shuffle(bySec[s]);
		pools[s] = pool;
		selected.push(...pool.slice(0, allocation[s]));
	}

	// Adjust to hit exactly targetPoints — swap one point at a time
	for (let attempt = 0; attempt < 500; attempt++) {
		const currentPoints = selected.reduce((sum, q) => sum + q.points, 0);
		if (currentPoints === targetPoints) break;

		const needMore = currentPoints < targetPoints;
		// Find a question to replace with one that's 1 point more/less
		let swapped = false;
		const indices = shuffle(selected.map((_, i) => i));

		for (const idx of indices) {
			const oldQ = selected[idx];
			const wantedPts = needMore ? oldQ.points + 1 : oldQ.points - 1;
			if (wantedPts < 1 || wantedPts > 4) continue;

			// Try same section first, then any section
			const tryOrder = [oldQ.section, ...sectionIds.filter(s => s !== oldQ.section)];
			for (const s of tryOrder) {
				const replacement = pools[s].find(
					(q) => q.points === wantedPts && !selected.includes(q)
				);
				if (replacement) {
					selected[idx] = replacement;
					swapped = true;
					break;
				}
			}
			if (swapped) break;
		}

		if (!swapped) break;
	}

	return shuffle(selected);
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

// ─── SRS (Spaced Repetition) ─────────────────────────────────

// Intervals in days: after N consecutive correct answers, review after this many days
const SRS_INTERVALS = [0, 1, 3, 7, 21];

export type SrsStatus = 'new' | 'learning' | 'review' | 'learned';

export interface SrsInfo {
	status: SrsStatus;
	streak: number;
	daysSinceLastAnswer: number;
	dueForReview: boolean;
}

function daysBetween(dateStr: string): number {
	if (!dateStr) return Infinity;
	const [y, m, d] = dateStr.split('-').map(Number);
	const then = new Date(y, m - 1, d).getTime();
	const now = new Date().setHours(0, 0, 0, 0);
	return Math.floor((now - then) / (1000 * 60 * 60 * 24));
}

export function getQuestionSrs(q: Question): SrsInfo {
	const prog = getQuestionProgress(q.section, q.id);
	if (!prog || (prog.correct === 0 && prog.wrong === 0)) {
		return { status: 'new', streak: 0, daysSinceLastAnswer: Infinity, dueForReview: false };
	}

	const streak = prog.streak || 0;
	const days = daysBetween(prog.last);
	const interval = SRS_INTERVALS[Math.min(streak, SRS_INTERVALS.length - 1)];
	const dueForReview = days >= interval;

	let status: SrsStatus;
	if (streak >= SRS_INTERVALS.length) {
		status = dueForReview ? 'review' : 'learned';
	} else if (streak === 0 && prog.wrong > 0) {
		status = 'review';  // got it wrong last time — needs review
	} else {
		status = 'learning';
	}

	return { status, streak, daysSinceLastAnswer: days, dueForReview };
}

export interface SrsStats {
	learned: number;
	review: number;
	learning: number;
	newCount: number;
}

export function getSrsStats(data: QuestionsData): SrsStats {
	const active = getActiveQuestions(data);
	let learned = 0, review = 0, learning = 0, newCount = 0;
	for (const q of active) {
		const srs = getQuestionSrs(q);
		switch (srs.status) {
			case 'learned': learned++; break;
			case 'review': review++; break;
			case 'learning': learning++; break;
			case 'new': newCount++; break;
		}
	}
	return { learned, review, learning, newCount };
}

/**
 * Select questions for an SRS session.
 * Priority: 1) due reviews  2) learning (in progress)  3) new questions
 */
/**
 * Select questions for an SRS session.
 * Priority: 1) due reviews  2) learning (in progress)  3) new questions
 * New questions are selected progressively by section order:
 * - Start with section 1
 * - When ≥30% of a section is not "new", start mixing in the next section
 * - The more learned, the more from the next section
 */
export function getSrsSessionQuestions(data: QuestionsData, count: number): Question[] {
	const active = getActiveQuestions(data).filter(
		(q) => q.correct_answers && q.correct_answers.length > 0
	);

	const reviews: Question[] = [];
	const learningDue: Question[] = [];
	const newQs: Question[] = [];

	for (const q of active) {
		const srs = getQuestionSrs(q);
		if (srs.status === 'review' || (srs.status === 'learning' && srs.dueForReview)) {
			reviews.push(q);
		} else if (srs.status === 'learning') {
			learningDue.push(q);
		} else if (srs.status === 'new') {
			newQs.push(q);
		}
	}

	const shuffle = <T>(arr: T[]): T[] => [...arr].sort(() => Math.random() - 0.5);
	const selected: Question[] = [];

	// 1) Reviews first (shuffled)
	for (const q of shuffle(reviews)) {
		if (selected.length >= count) break;
		selected.push(q);
	}

	// 2) Learning in progress
	for (const q of shuffle(learningDue)) {
		if (selected.length >= count) break;
		selected.push(q);
	}

	// 3) New questions — progressive by section order
	if (selected.length < count) {
		const sectionOrder = data.metadata.sections.map(s => s.id);
		const newBySection: Record<string, Question[]> = {};
		for (const q of newQs) {
			if (!newBySection[q.section]) newBySection[q.section] = [];
			newBySection[q.section].push(q);
		}

		// Calculate progress per section (% that are NOT new)
		const sectionProgress: Record<string, number> = {};
		for (const sid of sectionOrder) {
			const sectionQs = active.filter(q => q.section === sid);
			if (sectionQs.length === 0) { sectionProgress[sid] = 1; continue; }
			const notNew = sectionQs.filter(q => getQuestionSrs(q).status !== 'new').length;
			sectionProgress[sid] = notNew / sectionQs.length;
		}

		// Build weighted pool of new questions
		// Sections that are ≥30% progressed unlock the next section
		const UNLOCK_THRESHOLD = 0.3;
		const pool: Question[] = [];

		for (let i = 0; i < sectionOrder.length; i++) {
			const sid = sectionOrder[i];
			const sectionNew = newBySection[sid] || [];
			if (sectionNew.length === 0) continue;

			if (i === 0) {
				// First section always available
				pool.push(...sectionNew);
			} else {
				// Check if previous section is progressed enough
				const prevProgress = sectionProgress[sectionOrder[i - 1]] || 0;
				if (prevProgress >= UNLOCK_THRESHOLD) {
					pool.push(...sectionNew);
				}
			}
		}

		for (const q of shuffle(pool)) {
			if (selected.length >= count) break;
			selected.push(q);
		}
	}

	return shuffle(selected);
}
