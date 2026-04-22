export type Lang = 'sr' | 'ru';

export interface Option {
	letter: string;
	text: string;
	text_ru?: string;
}

export interface Question {
	id: number;
	text: string;
	text_ru?: string;
	options: Option[];
	points: number;
	correct_answers_count: number;
	has_image: boolean;
	image?: string;
	section: string;
	correct_answers?: string[];
	is_removed?: boolean;
	is_new?: boolean;
	is_changed?: boolean;
	categories?: string[];
}

export interface SectionMeta {
	id: string;
	name: string;
	questions: number;
}

export interface QuestionsData {
	metadata: {
		source: string;
		sections: SectionMeta[];
		total_questions: number;
		removed_questions: number;
	};
	questions: Question[];
}

export interface QuestionProgress {
	correct: number;
	wrong: number;
	last: string;
}

export interface SectionProgress {
	[questionId: string]: QuestionProgress;
}

export interface Progress {
	[sectionId: string]: SectionProgress;
}

export interface ExamResult {
	date: string;
	score: number;
	total: number;
	passed: boolean;
	wrong_ids: string[];
	answers: Record<string, string[]>;
}

export type Accent = 'gold' | 'clay' | 'sage' | 'azure' | 'plum';
export type Category = 'A' | 'B' | 'C' | 'D' | 'F' | 'M';

export interface Settings {
	theme: 'light' | 'dark' | 'system';
	fontSize: 'small' | 'medium' | 'large';
	lang: Lang;
	accent: Accent;
	category: Category;
}

export interface AppState {
	version: number;
	progress: Progress;
	bookmarks: string[];
	exams: ExamResult[];
	settings: Settings;
	onboarded: boolean;
}

export interface Chunk {
	index: number;
	start: number;
	end: number;
	questions: Question[];
}
