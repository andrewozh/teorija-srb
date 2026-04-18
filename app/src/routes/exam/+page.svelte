<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { loadQuestions, getRandomExamQuestions, questionKey, qText, oText } from '$lib/data.js';
	import { recordAnswer, addExamResult, getSettings, subscribe } from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t } from '$lib/i18n.js';
	import type { Question, ExamResult, Lang } from '$lib/types.js';

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

	$effect(() => {
		setPageTitle(t('exam.title', lang));
	});

	$effect(() => {
		const unsub = subscribe(() => { lang = getSettings().lang; });
		return unsub;
	});

	// Timer
	let timeRemaining = $state(45 * 60);
	let timerInterval: ReturnType<typeof setInterval> | undefined;

	let currentQuestion = $derived(questions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);
	let passed = $derived(wrongIds.length <= 5);

	let minutes = $derived(Math.floor(timeRemaining / 60));
	let seconds = $derived(timeRemaining % 60);
	let timeDisplay = $derived(`${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
	let timeWarning = $derived(timeRemaining < 5 * 60);

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
			if (timeRemaining <= 0) {
				finishExam();
			}
		}, 1000);
	}

	function selectAnswer(letter: string) {
		if (isAnswered) return;

		if (hasMultipleAnswers) {
			const newSet = new Set(selectedAnswers);
			if (newSet.has(letter)) {
				newSet.delete(letter);
			} else {
				newSet.add(letter);
			}
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

		if (isCorrect) {
			score++;
		} else {
			wrongIds.push(key);
		}

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
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = undefined;
		}

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

	function optionClass(letter: string): string {
		if (!isAnswered) {
			return selectedAnswers.has(letter) ? 'selected' : '';
		}
		const isCorrectAnswer = currentQuestion?.correct_answers?.includes(letter);
		const wasSelected = selectedAnswers.has(letter);
		if (isCorrectAnswer) return 'correct';
		if (wasSelected && !isCorrectAnswer) return 'wrong';
		return 'dimmed';
	}

	function optionBorderClass(letter: string): string {
		const cls = optionClass(letter);
		switch (cls) {
			case 'selected': return 'border-primary bg-primary-subtle';
			case 'correct': return 'border-success bg-success-subtle';
			case 'wrong': return 'border-danger bg-danger-subtle';
			case 'dimmed': return 'opacity-50';
			default: return '';
		}
	}

	function pillState(index: number): string {
		if (index === currentIndex) return 'current';
		const q = questions[index];
		if (!q) return 'unanswered';
		const key = questionKey(q);
		if (wrongIds.includes(key)) return 'wrong';
		if (answers[key]) return 'correct';
		return 'unanswered';
	}

	function pillClass(state: string): string {
		switch (state) {
			case 'current': return 'bg-primary text-white';
			case 'correct': return 'bg-success-subtle text-success border-success';
			case 'wrong': return 'bg-danger-subtle text-danger border-danger';
			default: return 'bg-body-secondary text-body-secondary';
		}
	}

	onMount(() => {
		return () => {
			if (timerInterval) clearInterval(timerInterval);
		};
	});

	let pillsContainer = $state<HTMLDivElement | undefined>(undefined);

	$effect(() => {
		if (pillsContainer && currentIndex >= 0 && phase === 'active') {
			const pill = pillsContainer.children[currentIndex] as HTMLElement;
			if (pill) {
				pill.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
			}
		}
	});
</script>

<div class="d-flex flex-column min-vh-100">
	{#if phase === 'intro'}
		<div class="flex-grow-1 d-flex align-items-center justify-content-center p-4">
			<div class="card border-0 shadow text-center w-100">
				<div class="card-body p-4">
					<div class="fs-1 mb-3">📝</div>
					<h2 class="h4 fw-bold mb-3">{t('exam.title', lang)}</h2>
					<ul class="list-unstyled text-body-secondary mb-4">
						<li class="py-1">• {t('exam.desc', lang)}</li>
						<li class="py-1">• {t('exam.max_errors', lang)}</li>
					</ul>
					<button class="btn btn-success btn-lg w-100" onclick={startExam}>
						{t('exam.start', lang)}
					</button>
				</div>
			</div>
		</div>

	{:else if phase === 'active' && currentQuestion}
		<!-- Active exam: timer bar -->
		<div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom bg-body">
			<button class="btn btn-link text-body p-2" onclick={() => { if (confirm(t('exam.finish', lang) + '?')) finishExam(); }} aria-label={t('exam.finish', lang)}>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</button>
			<span class="text-body-secondary fw-semibold small">
				{currentIndex + 1} / {questions.length}
			</span>
			<span class="badge rounded-pill {timeWarning ? 'text-bg-danger timer-pulse' : 'bg-body-secondary text-body'} px-3 py-2">
				⏱ {timeDisplay}
			</span>
		</div>

		<!-- Pills -->
		<div class="pills-scroll bg-body border-bottom" bind:this={pillsContainer}>
			{#each questions as _, i}
				<div class="pill-item rounded-pill border {pillClass(pillState(i))}">
					{i + 1}
				</div>
			{/each}
		</div>

		<main class="flex-grow-1 p-3 d-flex flex-column gap-3">
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="card border-0 shadow-sm overflow-hidden">
					<img src="{base}/images/{currentQuestion.image}" alt="Слика уз питање" class="card-img-top" />
				</div>
			{/if}

			<div class="card border-0 shadow-sm">
				<div class="card-body">
					<p class="mb-0" style="line-height:1.5;">{qText(currentQuestion, lang)}</p>
					{#if hasMultipleAnswers}
						<span class="badge text-bg-primary mt-2">{t('question.multi', lang)} ({currentQuestion.correct_answers_count})</span>
					{/if}
				</div>
			</div>

			<div class="d-flex flex-column gap-2">
				{#each currentQuestion.options as option}
					<button
						class="card border-2 shadow-sm text-start {optionBorderClass(option.letter)}"
						onclick={() => selectAnswer(option.letter)}
						disabled={isAnswered}
					>
						<div class="card-body py-2 px-3 d-flex align-items-start gap-2">
							<span class="fw-bold text-body-secondary flex-shrink-0">{option.letter})</span>
							<span class="flex-grow-1 small" style="line-height:1.4;">{oText(option, lang)}</span>
							{#if isAnswered && currentQuestion.correct_answers?.includes(option.letter)}
								<span class="fw-bold text-success flex-shrink-0">✓</span>
							{:else if isAnswered && selectedAnswers.has(option.letter) && !currentQuestion.correct_answers?.includes(option.letter)}
								<span class="fw-bold text-danger flex-shrink-0">✗</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
				<button class="btn btn-primary btn-lg w-100" onclick={confirmMultiAnswer}>
					{t('question.confirm', lang)} ({selectedAnswers.size})
				</button>
			{/if}

			{#if isAnswered}
				<button class="btn btn-primary btn-lg w-100" onclick={nextQuestion}>
					{currentIndex < questions.length - 1 ? t('question.next', lang) + ' →' : t('exam.finish', lang)}
				</button>
			{/if}
		</main>

	{:else if phase === 'results'}
		<div class="p-3 d-flex flex-column gap-3">
			<!-- Result card -->
			<div class="card border-0 shadow text-center border-top border-4 {passed ? 'border-success' : 'border-danger'}">
				<div class="card-body p-4">
					<div class="fs-1 mb-2">{passed ? '🎉' : '😔'}</div>
					<h2 class="h4 fw-bold {passed ? 'text-success' : 'text-danger'} mb-3">
						{passed ? t('exam.passed', lang) : t('exam.failed', lang)}
					</h2>
					<div class="mb-2">
						<span class="display-4 fw-bold">{score}</span>
						<span class="fs-5 text-body-secondary">/ {questions.length}</span>
					</div>
					<p class="text-body-secondary">{wrongIds.length} {t('exam.errors', lang)}</p>
				</div>
			</div>

			<!-- Wrong answers -->
			{#if wrongIds.length > 0}
				<div class="card border-0 shadow-sm">
					<div class="card-body">
						<h3 class="h6 text-danger mb-3">{t('exam.review', lang)}:</h3>
						{#each wrongIds as wrongKey, i}
							{@const q = questions.find((q) => questionKey(q) === wrongKey)}
							{#if q}
								<div class="py-2 {i < wrongIds.length - 1 ? 'border-bottom' : ''}">
									<p class="small mb-1" style="line-height:1.4;">{qText(q, lang)}</p>
									<p class="small text-success fw-semibold mb-0">
										{q.correct_answers?.join(', ')}
									</p>
								</div>
							{/if}
						{/each}
					</div>
				</div>
			{/if}

			<!-- Actions -->
			<div class="d-flex flex-column gap-2 align-items-center">
				<button class="btn btn-success btn-lg w-100" onclick={startExam}>{t('exam.start', lang)}</button>
				<a href="{base}/" class="text-primary fw-medium">← {t('exam.back', lang)}</a>
			</div>
		</div>
	{/if}
</div>

<style>
	.pills-scroll {
		display: flex;
		gap: 0.35rem;
		padding: 0.5rem 0.75rem;
		overflow-x: auto;
		scrollbar-width: none;
	}

	.pills-scroll::-webkit-scrollbar {
		display: none;
	}

	.pill-item {
		min-width: 28px;
		height: 28px;
		font-size: 0.7rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.timer-pulse {
		animation: pulse 1s infinite;
	}

	@keyframes pulse {
		50% { opacity: 0.7; }
	}
</style>
