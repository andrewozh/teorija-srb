<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getRandomExamQuestions, questionKey, qText } from '$lib/data.js';
	import { addExamResult, getSettings, getExams, subscribe } from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Question, ExamResult, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionCarousel from '$lib/components/QuestionCarousel.svelte';

	type ExamPhase = 'intro' | 'active' | 'results';

	let phase = $state<ExamPhase>('intro');
	let questions = $state<Question[]>([]);
	let lang = $state<Lang>(getSettings().lang);
	let examHistory = $state<ExamResult[]>([...getExams()].reverse());

	// Results data
	let score = $state(0);
	let wrongIds = $state<string[]>([]);
	let passed = $derived(score >= 80);

	$effect(() => {
		const unsub = subscribe(() => {
			lang = getSettings().lang;
			examHistory = [...getExams()].reverse();
		});
		return unsub;
	});

	async function startExam() {
		const data = await loadQuestions();
		questions = getRandomExamQuestions(data, 41);
		score = 0;
		wrongIds = [];
		phase = 'active';
	}

	function finishExam() {
		// Calculate results from carousel state — we'll receive via onComplete
		const result: ExamResult = {
			date: new Date().toISOString(),
			score,
			total: questions.length,
			passed: score >= 80,
			wrong_ids: wrongIds,
			answers: {}
		};
		addExamResult(result);
		phase = 'results';
	}

	function formatDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('sr-Latn-RS', { day: 'numeric', month: 'short' });
	}
</script>

<div class="page">
	{#if phase === 'intro'}
		<Header
			title={t('exam.title', lang)}
			home onback={() => goto(`${base}/`)}
			onsettings={() => goto(`${base}/settings`)}
		/>
		<div class="scroll-area">
			<div class="intro-label">{lang === 'sr' ? 'симулација' : 'симуляция'}</div>
			<div class="intro-title">
				{lang === 'sr' ? 'Полагање под' : 'Экзамен в'}<br/>
				{lang === 'sr' ? 'стварним условима.' : 'реальных условиях.'}
			</div>

			<div class="rules-card">
				{#each [['41', lang === 'sr' ? 'питање' : 'вопрос'], ['100', lang === 'sr' ? 'поена укупно' : 'баллов всего'], ['80', lang === 'sr' ? 'поена за пролаз' : 'баллов для сдачи'], ['45', lang === 'sr' ? 'минута' : 'минут']] as [num, label], i}
					<div class="rule-row" class:rule-last={i === 3}>
						<div class="rule-num">{num}</div>
						<div class="rule-label">{label}</div>
					</div>
				{/each}
			</div>

			{#if examHistory.length > 0}
				<div class="history-label">{lang === 'sr' ? 'Последњи покушаји' : 'Последние попытки'}</div>
				<div class="history-card">
					{#each examHistory.slice(0, 3) as h, i}
						<div class="history-row" class:history-last={i === Math.min(2, examHistory.length - 1)}>
							<div class="history-dot" style:background={h.passed ? 'var(--correct)' : 'var(--wrong)'}></div>
							<div class="history-score">{h.score}/{h.total}</div>
							<div class="history-date">{formatDate(h.date)}</div>
						</div>
					{/each}
				</div>
			{/if}

			<button class="exam-start-btn" onclick={startExam}>
				{t('exam.start', lang)}
			</button>
		</div>

	{:else if phase === 'active'}
		<QuestionCarousel
			{questions}
			headerTitle={lang === 'sr' ? 'ИСПИТ' : 'ЭКЗАМЕН'}
			showLangToggle={false}
			showBookmark={false}
			showFlag={false}
			showTimer={true}
			timerSeconds={2700}
			forceLang="sr"
			onBack={() => { if (confirm(t('exam.finish', lang) + '?')) finishExam(); }}
			onComplete={() => finishExam()}
			bind:score
			bind:wrongIds
		/>

	{:else if phase === 'results'}
		<Header
			title={t('exam.title', lang)}
			back={false}
			settings={false}
		/>
		<div class="scroll-area">
			<div class="result-card" class:result-pass={passed} class:result-fail={!passed}>
				<div class="result-icon">
					{#if passed}
						<Icon name="check" size={32} color="var(--correct)" stroke={2.5} />
					{:else}
						<Icon name="x" size={32} color="var(--wrong)" stroke={2.5} />
					{/if}
				</div>
				<div class="result-title" style:color={passed ? 'var(--correct)' : 'var(--wrong)'}>
					{passed ? t('exam.passed', lang) : t('exam.failed', lang)}
				</div>
				<div class="result-score">
					{score}<span class="result-total">/100</span>
				</div>
				<div class="result-errors">
					{wrongIds.length} {t('exam.errors', lang)} · {lang === 'sr' ? 'потребно' : 'нужно'} ≥80
				</div>
			</div>

			{#if wrongIds.length > 0}
				<div class="review-card">
					<div class="review-title">{t('exam.review', lang)}</div>
					{#each wrongIds as wrongKey, i}
						{@const q = questions.find((q) => questionKey(q) === wrongKey)}
						{#if q}
							<div class="review-item" class:review-last={i === wrongIds.length - 1}>
								<p class="review-text">{qText(q, lang)}</p>
								<p class="review-answer">{q.correct_answers?.join(', ')}</p>
							</div>
						{/if}
					{/each}
				</div>
			{/if}

			<button class="exam-start-btn" onclick={startExam}>{t('exam.start', lang)}</button>
			<a href="{base}/" class="back-link">← {t('exam.back', lang)}</a>
		</div>
	{/if}
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 20px 16px 24px; }

	.intro-label {
		font-family: var(--font-mono); font-size: 10px; color: var(--ink3);
		letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;
	}
	.intro-title {
		font-size: 26px; font-weight: 500; letter-spacing: -0.4px;
		margin-bottom: 22px; line-height: 1.15;
	}

	.rules-card {
		background: var(--surface); border-radius: 20px;
		border: 0.5px solid var(--hairline); overflow: hidden;
		margin-bottom: 18px;
	}
	.rule-row {
		display: flex; align-items: baseline; padding: 14px 18px;
		border-bottom: 0.5px solid var(--hairline); gap: 16px;
	}
	.rule-last { border-bottom: none; }
	.rule-num {
		font-family: var(--font-mono); font-size: 22px;
		color: var(--ink); letter-spacing: -0.4px; width: 52px;
	}
	.rule-label { flex: 1; font-size: 13px; color: var(--ink2); }

	.history-label {
		font-family: var(--font-mono); font-size: 10px; color: var(--ink3);
		letter-spacing: 1px; text-transform: uppercase; padding: 4px 4px 10px;
	}
	.history-card {
		background: var(--surface); border-radius: 18px;
		border: 0.5px solid var(--hairline); overflow: hidden;
		margin-bottom: 24px;
	}
	.history-row {
		display: flex; align-items: center; padding: 13px 16px; gap: 12px;
		border-bottom: 0.5px solid var(--hairline);
	}
	.history-last { border-bottom: none; }
	.history-dot { width: 6px; height: 6px; border-radius: 3px; flex-shrink: 0; }
	.history-score { flex: 1; font-family: var(--font-mono); font-size: 13px; color: var(--ink); }
	.history-date { font-size: 12px; color: var(--ink3); font-family: var(--font-mono); }

	.exam-start-btn {
		width: 100%; height: 54px; border-radius: 18px;
		background: var(--ink); color: var(--bg); border: none;
		font-family: var(--font-ui); font-size: 15px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
	}

	/* Results */
	.result-card {
		text-align: center; padding: 32px 24px;
		background: var(--surface); border-radius: 22px;
		border: 0.5px solid var(--hairline); margin-bottom: 20px;
	}
	.result-icon { margin-bottom: 12px; }
	.result-title { font-size: 22px; font-weight: 600; margin-bottom: 12px; }
	.result-score {
		font-family: var(--font-mono); font-size: 48px;
		font-weight: 700; color: var(--ink); letter-spacing: -1px;
	}
	.result-total { font-size: 24px; color: var(--ink3); }
	.result-errors { font-size: 13px; color: var(--ink3); margin-top: 8px; }

	.review-card {
		background: var(--surface); border-radius: 18px;
		border: 0.5px solid var(--hairline); padding: 16px;
		margin-bottom: 20px;
	}
	.review-title { font-size: 14px; font-weight: 600; color: var(--wrong); margin-bottom: 12px; }
	.review-item { padding: 8px 0; border-bottom: 0.5px solid var(--hairline); }
	.review-last { border-bottom: none; }
	.review-text { font-size: 13px; line-height: 1.4; margin-bottom: 4px; }
	.review-answer { font-size: 12px; color: var(--correct); font-weight: 600; }

	.back-link {
		display: block; text-align: center; margin-top: 16px;
		color: var(--accent); font-weight: 500; font-size: 14px;
	}

	/* Desktop */
	@media (min-width: 1024px) {
		.scroll-area { padding: 28px 40px 40px; max-width: 640px; }
	}
</style>
