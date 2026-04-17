<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, getRandomExamQuestions, questionKey } from '$lib/data.js';
	import { recordAnswer, addExamResult } from '$lib/store.js';
	import type { Question, ExamResult } from '$lib/types.js';

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

	// Timer
	let timeRemaining = $state(45 * 60); // 45 minutes in seconds
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

	function pillState(index: number): string {
		if (index === currentIndex) return 'current';
		const q = questions[index];
		if (!q) return 'unanswered';
		const key = questionKey(q);
		if (wrongIds.includes(key)) return 'wrong';
		if (answers[key]) return 'correct';
		return 'unanswered';
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

<div class="exam-page">
	{#if phase === 'intro'}
		<header class="page-header">
			<a href="/" class="back-btn" aria-label="Назад">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</a>
			<h1>Испит</h1>
			<div style="width: 40px"></div>
		</header>

		<div class="intro-content">
			<div class="intro-card">
				<div class="intro-icon">📝</div>
				<h2>Пробни испит</h2>
				<ul class="intro-rules">
					<li>41 питање из свих области</li>
					<li>Време: 45 минута</li>
					<li>Пролаз: највише 5 грешака</li>
				</ul>
				<button class="start-btn" onclick={startExam}>
					Започни испит
				</button>
			</div>
		</div>

	{:else if phase === 'active' && currentQuestion}
		<header class="page-header">
			<button class="back-btn" onclick={() => { if (confirm('Прекинути испит?')) finishExam(); }} aria-label="Прекини">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</button>
			<span class="header-title">
				{currentIndex + 1} / {questions.length}
			</span>
			<span class="timer" class:warning={timeWarning}>
				⏱ {timeDisplay}
			</span>
		</header>

		<!-- Pills -->
		<div class="pills-scroll" bind:this={pillsContainer}>
			{#each questions as _, i}
				<div class="pill {pillState(i)}">
					{i + 1}
				</div>
			{/each}
		</div>

		<main class="question-content">
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="question-image">
					<img src="/images/{currentQuestion.image}" alt="Слика уз питање" />
				</div>
			{/if}

			<div class="question-text">
				<p>{currentQuestion.text}</p>
				{#if hasMultipleAnswers}
					<span class="multi-badge">Више одговора ({currentQuestion.correct_answers_count})</span>
				{/if}
			</div>

			<div class="options">
				{#each currentQuestion.options as option}
					<button
						class="option-card {optionClass(option.letter)}"
						onclick={() => selectAnswer(option.letter)}
						disabled={isAnswered}
					>
						<span class="option-letter">{option.letter})</span>
						<span class="option-text">{option.text}</span>
						{#if isAnswered && currentQuestion.correct_answers?.includes(option.letter)}
							<span class="option-icon">✓</span>
						{:else if isAnswered && selectedAnswers.has(option.letter) && !currentQuestion.correct_answers?.includes(option.letter)}
							<span class="option-icon">✗</span>
						{/if}
					</button>
				{/each}
			</div>

			{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
				<button class="confirm-btn" onclick={confirmMultiAnswer}>
					Потврди одговор ({selectedAnswers.size} изабрано)
				</button>
			{/if}

			{#if isAnswered}
				<button class="next-btn" onclick={nextQuestion}>
					{currentIndex < questions.length - 1 ? 'Следеће питање →' : 'Заврши испит'}
				</button>
			{/if}
		</main>

	{:else if phase === 'results'}
		<header class="page-header">
			<a href="/" class="back-btn" aria-label="Почетна">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</a>
			<h1>Резултат</h1>
			<div style="width: 40px"></div>
		</header>

		<div class="results-content">
			<div class="result-card" class:passed class:failed={!passed}>
				<div class="result-icon">{passed ? '🎉' : '😔'}</div>
				<h2>{passed ? 'Положио/ла!' : 'Није положено'}</h2>
				<div class="result-score">
					<span class="score-number">{score}</span>
					<span class="score-total">/ {questions.length}</span>
				</div>
				<p class="result-errors">{wrongIds.length} грешака (дозвољено: 5)</p>
			</div>

			{#if wrongIds.length > 0}
				<div class="wrong-list">
					<h3>Грешке:</h3>
					{#each wrongIds as wrongKey}
						{@const q = questions.find((q) => questionKey(q) === wrongKey)}
						{#if q}
							<div class="wrong-item">
								<p class="wrong-question">{q.text}</p>
								<p class="wrong-answer">
									Тачан одговор: {q.correct_answers?.join(', ')}
								</p>
							</div>
						{/if}
					{/each}
				</div>
			{/if}

			<div class="result-actions">
				<button class="start-btn" onclick={startExam}>Нови испит</button>
				<a href="/" class="home-link">← Почетна</a>
			</div>
		</div>
	{/if}
</div>

<style>
	.exam-page {
		display: flex;
		flex-direction: column;
		min-height: 100dvh;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 0.75rem;
		background: var(--card);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.page-header h1 {
		font-size: 1.1rem;
		font-weight: 600;
	}

	.header-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text-secondary);
	}

	.back-btn {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.timer {
		font-size: 0.85rem;
		font-weight: 700;
		color: var(--text);
		padding: 0.3rem 0.6rem;
		background: var(--bg-secondary);
		border-radius: var(--radius-pill);
	}

	.timer.warning {
		color: var(--danger);
		background: var(--danger-light);
		animation: pulse 1s infinite;
	}

	@keyframes pulse {
		50% { opacity: 0.7; }
	}

	/* Pills */
	.pills-scroll {
		display: flex;
		gap: 0.35rem;
		padding: 0.5rem 0.75rem;
		overflow-x: auto;
		scrollbar-width: none;
		background: var(--card);
		border-bottom: 1px solid var(--border);
	}

	.pills-scroll::-webkit-scrollbar {
		display: none;
	}

	.pill {
		min-width: 28px;
		height: 28px;
		border-radius: var(--radius-pill);
		font-size: 0.7rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		border: 2px solid transparent;
		background: var(--bg-secondary);
		color: var(--text-secondary);
	}

	.pill.current {
		background: var(--primary);
		color: white;
	}

	.pill.correct {
		background: var(--success-light);
		color: var(--success);
		border-color: var(--success);
	}

	.pill.wrong {
		background: var(--danger-light);
		color: var(--danger);
		border-color: var(--danger);
	}

	/* Intro */
	.intro-content {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem 1rem;
	}

	.intro-card {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow-lg);
		padding: 2rem;
		text-align: center;
		width: 100%;
	}

	.intro-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}

	.intro-card h2 {
		font-size: 1.3rem;
		margin-bottom: 1rem;
	}

	.intro-rules {
		list-style: none;
		margin-bottom: 1.5rem;
	}

	.intro-rules li {
		padding: 0.4rem 0;
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.intro-rules li::before {
		content: '• ';
		color: var(--primary);
	}

	.start-btn {
		width: 100%;
		padding: 0.85rem;
		background: var(--success);
		color: white;
		border-radius: var(--radius);
		font-weight: 600;
		font-size: 1rem;
		transition: opacity 0.2s;
	}

	.start-btn:active {
		opacity: 0.8;
	}

	/* Question content */
	.question-content {
		flex: 1;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.question-image {
		border-radius: var(--radius);
		overflow: hidden;
		background: var(--card);
		box-shadow: var(--shadow);
	}

	.question-text {
		background: var(--card);
		padding: 1rem;
		border-radius: var(--radius);
		box-shadow: var(--shadow);
	}

	.question-text p {
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.multi-badge {
		display: inline-block;
		margin-top: 0.5rem;
		padding: 0.2rem 0.6rem;
		background: var(--primary-light);
		color: var(--primary);
		border-radius: var(--radius-pill);
		font-size: 0.7rem;
		font-weight: 600;
	}

	.options {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.option-card {
		display: flex;
		align-items: flex-start;
		gap: 0.6rem;
		padding: 0.85rem 1rem;
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		text-align: left;
		transition: all 0.2s;
		border: 2px solid transparent;
	}

	.option-card.selected {
		border-color: var(--primary);
		background: var(--primary-light);
	}

	.option-card.correct {
		border-color: var(--success);
		background: var(--success-light);
	}

	.option-card.wrong {
		border-color: var(--danger);
		background: var(--danger-light);
	}

	.option-card.dimmed {
		opacity: 0.5;
	}

	.option-card:disabled {
		cursor: default;
	}

	.option-letter {
		font-weight: 700;
		color: var(--text-secondary);
		flex-shrink: 0;
	}

	.option-text {
		flex: 1;
		font-size: 0.9rem;
		line-height: 1.4;
	}

	.option-icon {
		flex-shrink: 0;
		font-weight: 700;
	}

	.option-card.correct .option-icon {
		color: var(--success);
	}

	.option-card.wrong .option-icon {
		color: var(--danger);
	}

	.confirm-btn {
		padding: 0.85rem;
		background: var(--primary);
		color: white;
		border-radius: var(--radius);
		font-weight: 600;
		font-size: 0.95rem;
	}

	.next-btn {
		padding: 0.85rem;
		background: var(--primary);
		color: white;
		border-radius: var(--radius);
		font-weight: 600;
		font-size: 0.95rem;
		text-align: center;
	}

	/* Results */
	.results-content {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.result-card {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow-lg);
		padding: 2rem;
		text-align: center;
	}

	.result-card.passed {
		border-top: 4px solid var(--success);
	}

	.result-card.failed {
		border-top: 4px solid var(--danger);
	}

	.result-icon {
		font-size: 3rem;
		margin-bottom: 0.5rem;
	}

	.result-card h2 {
		font-size: 1.3rem;
		margin-bottom: 0.75rem;
	}

	.result-card.passed h2 {
		color: var(--success);
	}

	.result-card.failed h2 {
		color: var(--danger);
	}

	.result-score {
		margin-bottom: 0.5rem;
	}

	.score-number {
		font-size: 2.5rem;
		font-weight: 800;
	}

	.score-total {
		font-size: 1.2rem;
		color: var(--text-secondary);
	}

	.result-errors {
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.wrong-list {
		background: var(--card);
		border-radius: var(--radius);
		padding: 1rem;
		box-shadow: var(--shadow);
	}

	.wrong-list h3 {
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
		color: var(--danger);
	}

	.wrong-item {
		padding: 0.75rem 0;
		border-bottom: 1px solid var(--border);
	}

	.wrong-item:last-child {
		border-bottom: none;
	}

	.wrong-question {
		font-size: 0.85rem;
		line-height: 1.4;
		margin-bottom: 0.3rem;
	}

	.wrong-answer {
		font-size: 0.8rem;
		color: var(--success);
		font-weight: 600;
	}

	.result-actions {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		align-items: center;
	}

	.home-link {
		color: var(--primary);
		font-size: 0.9rem;
		font-weight: 500;
	}
</style>
