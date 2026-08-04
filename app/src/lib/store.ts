import type { AppState, Progress, QuestionProgress, ExamResult, Settings } from './types.js';

const STORAGE_KEY = 'driving-exam-app';
const CURRENT_VERSION = 1;

function defaultState(): AppState {
	return {
		version: CURRENT_VERSION,
		progress: {},
		bookmarks: [],
		difficultTopics: [],
		exams: [],
		onboarded: false,
		settings: {
			theme: 'system',
			fontSize: 'medium',
			lang: 'sr',
			hintLang: 'sr',
			accent: 'gold',
			category: 'B',
			learnCount: 20
		}
	};
}

function loadState(): AppState {
	if (typeof localStorage === 'undefined') return defaultState();
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return defaultState();
		const parsed = JSON.parse(raw) as AppState;
		return { ...defaultState(), ...parsed };
	} catch {
		return defaultState();
	}
}

function saveState(state: AppState): void {
	if (typeof localStorage === 'undefined') return;
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
	} catch {
		// Storage full or unavailable
	}
}

// Singleton reactive state using module-level variables
// Components will import functions to read/mutate

let state: AppState = loadState();
let listeners: Array<() => void> = [];

function notify(): void {
	saveState(state);
	for (const fn of listeners) fn();
}

export function subscribe(fn: () => void): () => void {
	listeners.push(fn);
	return () => {
		listeners = listeners.filter((l) => l !== fn);
	};
}

export function getState(): AppState {
	return state;
}

export function getProgress(): Progress {
	return state.progress;
}

export function getSettings(): Settings {
	return state.settings;
}

export function getBookmarks(): string[] {
	return state.bookmarks;
}

export function getExams(): ExamResult[] {
	return state.exams;
}

// Progress operations
export function recordAnswer(section: string, questionId: number, correct: boolean): void {
	if (!state.progress[section]) {
		state.progress[section] = {};
	}
	const key = String(questionId);
	const prev = state.progress[section][key] || { correct: 0, wrong: 0, last: '', streak: 0 };
	if (correct) {
		prev.correct += 1;
		prev.streak = (prev.streak || 0) + 1;
	} else {
		prev.wrong += 1;
		prev.streak = 0;
	}
	prev.last = new Date().toISOString().split('T')[0];
	state.progress[section][key] = prev;
	notify();
}

export function getQuestionProgress(section: string, questionId: number): QuestionProgress | null {
	return state.progress[section]?.[String(questionId)] || null;
}

export function getSectionCompletedCount(section: string): number {
	const sp = state.progress[section];
	if (!sp) return 0;
	return Object.values(sp).filter((p) => p.correct > 0).length;
}

export function getTotalCompletedCount(): number {
	let count = 0;
	for (const section of Object.values(state.progress)) {
		count += Object.values(section).filter((p) => p.correct > 0).length;
	}
	return count;
}

export function getMistakeQuestionKeys(): string[] {
	const keys: string[] = [];
	for (const [section, questions] of Object.entries(state.progress)) {
		for (const [qId, prog] of Object.entries(questions)) {
			// streak < 2 means still a mistake:
			//   streak=0 → wrong (last answer was incorrect)
			//   streak=1 → recovering (1 correct after a wrong)
			//   streak≥2 → cleared
			if (prog.wrong > 0 && (prog.streak ?? 0) < 2) {
				keys.push(`${section}:${qId}`);
			}
		}
	}
	return keys;
}

/** Check if a question is in "recovering" state: was wrong, but streak=1 */
export function getMistakeStatus(section: string, questionId: number): 'none' | 'wrong' | 'recovering' {
	const prog = state.progress[section]?.[String(questionId)];
	if (!prog || prog.wrong === 0) return 'none';
	const streak = prog.streak ?? 0;
	if (streak >= 2) return 'none';
	if (streak === 1) return 'recovering';
	return 'wrong';
}

// Bookmark operations
export function isBookmarked(key: string): boolean {
	return state.bookmarks.includes(key);
}

export function toggleBookmark(key: string): void {
	const idx = state.bookmarks.indexOf(key);
	if (idx >= 0) {
		state.bookmarks.splice(idx, 1);
	} else {
		state.bookmarks.push(key);
	}
	notify();
}

// Difficult-topic operations
function topicKey(sectionId: string, topicId: string): string {
	return `${sectionId}:${topicId}`;
}

export function isTopicDifficult(sectionId: string, topicId: string): boolean {
	return state.difficultTopics.includes(topicKey(sectionId, topicId));
}

export function toggleDifficultTopic(sectionId: string, topicId: string): void {
	const key = topicKey(sectionId, topicId);
	const idx = state.difficultTopics.indexOf(key);
	if (idx >= 0) {
		state.difficultTopics.splice(idx, 1);
	} else {
		state.difficultTopics.push(key);
	}
	notify();
}

// Exam operations
export function addExamResult(result: ExamResult): void {
	state.exams.push(result);
	notify();
}

export function getPassedExamCount(): number {
	return state.exams.filter((e) => e.passed).length;
}

// Settings operations
export function updateSettings(partial: Partial<Settings>): void {
	state.settings = { ...state.settings, ...partial };
	notify();
}

// Export/Import/Reset
export function exportState(): string {
	return JSON.stringify(state, null, 2);
}

export function importState(json: string): boolean {
	try {
		const imported = JSON.parse(json) as AppState;
		if (imported.version && imported.progress) {
			state = { ...defaultState(), ...imported };
			notify();
			return true;
		}
		return false;
	} catch {
		return false;
	}
}

export function isOnboarded(): boolean {
	return state.onboarded;
}

export function setOnboarded(): void {
	state.onboarded = true;
	notify();
}

export function resetState(): void {
	state = defaultState();
	notify();
}
