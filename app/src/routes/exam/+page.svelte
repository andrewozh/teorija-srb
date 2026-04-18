<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getRandomExamQuestions, questionKey, qText, oText } from '$lib/data.js';
	import { recordAnswer, addExamResult, getSettings, getExams, subscribe } from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Question, ExamResult, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionPills from '$lib/components/QuestionPills.svelte';
	import AnswerOption from '$lib/components/AnswerOption.svelte';

	type ExamPhase = 'intro' | 'active' | 'results';

	let phase = $state<ExamPhase>('intro');
	let questions = $state<Question[]>([]);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let answers = $state<Record<string, string[]>>({});
	let wrongIds = $state<string[]>([]);
	let score = $state(0);
	let lang = $state<Lang>(getSettings().lang);
	let examHistory = $state<ExamResult[]>([...getExams()].reverse());

	let timeRemaining = $state(45 * 60);
	let timerInterval: ReturnType<typeof setInterval> | undefined;

	let currentQuestion = $derived(questions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);
	let passed = $derived(wrongIds.length <= 5);

	let minutes = $derived(Math.floor(timeRemaining / 60));
	let seconds = $derived(timeRemaining % 60);
	let timeDisplay = $derived(`${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
	let timeWarning = $derived(timeRemaining < 5 * 60);

	let pillStates = $derived(questions.map((q, i) => {
		const key = questionKey(q);
		if (wrongIds.includes(key)) return 'wrong';
		if (answers[key]) return 'correct';
		return 'unanswered';
	}));

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
		currentIndex = 0;
		selectedAnswers = new Set();
		isAnswered = false;
		answers = {};
		wrongIds = [];
		score = 0;
		timeRemaining = 45 * 60;
		phase = 'active';

		timerInterval = setInterval(() => {
			timeRemaining--;
			if (timeRemaining <= 0) finishExam();
		}, 1000);
	}

	function selectAnswer(letter: string) {
		if (isAnswered) return;
		if (hasMultipleAnswers) {
			const newSet = new Set(selectedAnswers);
			if (newSet.has(letter)) newSet.delete(letter);
			else newSet.add(letter);
			selectedAnswers = newSet;
		} else {
			selectedAnswers = new Set([letter]);
			submitAnswer();
		}
	}

	function confirmMultiAnswer() {
		if (selectedAnswers.size === 0) return;
		submitAnswer();
	}

	function submitAnswer() {
		if (!currentQuestion || !currentQuestion.correct_answers) return;
		isAnswered = true;
		const correctSet = new Set(currentQuestion.correct_answers);
		isCorrect =
			selectedAnswers.size === correctSet.size &&
			[...selectedAnswers].every((a) => correctSet.has(a));
		const key = questionKey(currentQuestion);
		answers[key] = [...selectedAnswers];
		if (isCorrect) score++;
		else wrongIds.push(key);
		recordAnswer(currentQuestion.section, currentQuestion.id, isCorrect);
	}

	function nextQuestion() {
		if (currentIndex < questions.length - 1) {
			currentIndex++;
			selectedAnswers = new Set();
			isAnswered = false;
			isCorrect = false;
		} else {
			finishExam();
		}
	}

	function finishExam() {
		if (timerInterval) { clearInterval(timerInterval); timerInterval = undefined; }
		const result: ExamResult = {
			date: new Date().toISOString(),
			score,
			total: questions.length,
			passed: wrongIds.length <= 5,
			wrong_ids: wrongIds,
			answers
		};
		addExamResult(result);
		phase = 'results';
	}

	function optionState(letter: string): 'idle' | 'selected' | 'correct' | 'wrong' | 'muted' {
		if (!isAnswered) return selectedAnswers.has(letter) ? 'selected' : 'idle';
		const isCorrectAnswer = currentQuestion?.correct_answers?.includes(letter);
		const wasSelected = selectedAnswers.has(letter);
		if (isCorrectAnswer) return 'correct';
		if (wasSelected && !isCorrectAnswer) return 'wrong';
		return 'muted';
	}

	function formatDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('sr-Latn-RS', { day: 'numeric', month: 'short' });
	}

	onMount(() => {
		return () => { if (timerInterval) clearInterval(timerInterval); };
	});
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

			<!-- Rules -->
			<div class="rules-card">
				{#each [['41', lang === 'sr' ? 'питања' : 'вопрос'], ['45', lang === 'sr' ? 'минута' : 'минут'], ['37', lang === 'sr' ? 'за пролаз' : 'для сдачи'], ['2', lang === 'sr' ? 'казнена поена' : 'штрафных балла']] as [num, label], i}
					<div class="rule-row" class:rule-last={i === 3}>
						<div class="rule-num">{num}</div>
						<div class="rule-label">{label}</div>
					</div>
				{/each}
			</div>

			<!-- History -->
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

	{:else if phase === 'active' && currentQuestion}
		<!-- Active exam header -->
		<div class="exam-header">
			<button class="q-header-btn" onclick={() => { if (confirm(t('exam.finish', lang) + '?')) finishExam(); }}>
				<Icon name="back" size={20} />
			</button>
			<div class="exam-header-center">
				<div class="exam-counter">
					{String(currentIndex + 1).padStart(2, '0')}<span class="exam-total"> / {questions.length}</span>
				</div>
			</div>
			<div class="exam-timer" class:timer-warn={timeWarning}>
				⏱ {timeDisplay}
			</div>
		</div>

		<QuestionPills current={currentIndex} states={pillStates} />

		<div class="q-body">
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="q-image-wrap">
					<img src="{base}/images/{currentQuestion.image}" alt="" class="q-image" />
				</div>
			{/if}
			<div class="q-text">{qText(currentQuestion, lang)}</div>
			{#if hasMultipleAnswers}
				<div class="q-meta">{t('question.multi', lang)} ({currentQuestion.correct_answers_count})</div>
			{/if}
		</div>

		<div class="q-answers">
			{#each currentQuestion.options as option}
				<AnswerOption
					letter={option.letter}
					text={oText(option, lang)}
					state={optionState(option.letter)}
					multi={hasMultipleAnswers}
					onclick={() => selectAnswer(option.letter)}
				/>
			{/each}

			{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
				<button class="q-confirm-btn" onclick={confirmMultiAnswer}>
					{t('question.confirm', lang)} ({selectedAnswers.size})
				</button>
			{/if}

			{#if isAnswered}
				<div class="q-footer">
					<div class="q-footer-spacer"></div>
					<button class="q-next-btn" onclick={nextQuestion}>
						{currentIndex < questions.length - 1 ? (lang === 'sr' ? 'Следеће' : 'Далее') : t('exam.finish', lang)}
						<Icon name="chev-right" size={14} color="var(--accent-ink)" />
					</button>
				</div>
			{/if}
		</div>

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
					{score}<span class="result-total">/{questions.length}</span>
				</div>
				<div class="result-errors">
					{wrongIds.length} {t('exam.errors', lang)}
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

	/* Intro */
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

	/* Active exam */
	.exam-header {
		display: flex; align-items: center; gap: 8px;
		padding: 6px 16px 4px; height: 48px; flex-shrink: 0;
	}
	.q-header-btn {
		width: 36px; height: 36px; border-radius: 12px;
		border: none; background: transparent; color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer; flex-shrink: 0;
	}
	.exam-header-center { flex: 1; text-align: center; }
	.exam-counter {
		font-family: var(--font-mono); font-size: 13px;
		color: var(--ink); letter-spacing: 0.3px;
	}
	.exam-total { color: var(--ink4); }
	.exam-timer {
		font-family: var(--font-mono); font-size: 12px;
		color: var(--ink); padding: 6px 12px;
		background: var(--surface2); border-radius: 10px;
	}
	.timer-warn { background: var(--wrong-wash); color: var(--wrong); animation: pulse 1s infinite; }

	.q-body { flex: 1; overflow: auto; padding: 16px 16px 8px; }
	.q-image-wrap {
		width: 100%; border-radius: 16px; overflow: hidden;
		border: 0.5px solid var(--hairline); margin-bottom: 14px;
	}
	.q-image { width: 100%; display: block; }
	.q-text {
		font-size: 16px; font-weight: 500; line-height: 1.4;
		letter-spacing: -0.2px; color: var(--ink);
	}
	.q-meta {
		font-family: var(--font-mono); font-size: 11px;
		color: var(--ink3); margin-top: 6px; letter-spacing: 0.3px;
	}

	.q-answers {
		padding: 12px 14px 14px;
		display: flex; flex-direction: column; gap: 8px;
		background: var(--answer-zone-bg);
		border-top: 0.5px solid var(--hairline);
		flex-shrink: 0;
	}
	.q-confirm-btn {
		width: 100%; height: 48px; border-radius: 16px;
		background: var(--accent); color: var(--accent-ink);
		border: none; font-family: var(--font-ui);
		font-size: 15px; font-weight: 600; cursor: pointer;
	}
	.q-footer { display: flex; align-items: center; gap: 4px; margin-top: 6px; }
	.q-footer-spacer { flex: 1; }
	.q-next-btn {
		height: 44px; padding: 0 22px; border-radius: 14px;
		background: var(--accent); color: var(--accent-ink);
		border: none; font-family: var(--font-ui);
		font-size: 14px; font-weight: 600; cursor: pointer;
		display: flex; align-items: center; gap: 6px;
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

	@keyframes pulse { 50% { opacity: 0.7; } }
</style>
