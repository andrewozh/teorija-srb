import type { AppState, Progress, QuestionProgress, ExamResult, Settings } from './types.js';

const STORAGE_KEY = 'driving-exam-app';
const CURRENT_VERSION = 1;

function defaultState(): AppState {
	return {
		version: CURRENT_VERSION,
		progress: {},
		bookmarks: [],
		exams: [],
		onboarded: false,
		settings: {
			theme: 'system',
			fontSize: 'medium',
			lang: 'sr',
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
	const prev = state.progress[section][key] || { correct: 0, wrong: 0, last: '' };
	if (correct) {
		prev.correct += 1;
	} else {
		prev.wrong += 1;
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
			// A mistake is a question that was answered wrong and hasn't been corrected enough
			if (prog.wrong > 0 && prog.correct < prog.wrong + 2) {
				keys.push(`${section}:${qId}`);
			}
		}
	}
	return keys;
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
