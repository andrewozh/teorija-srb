<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey, questionKey, sectionIcon } from '$lib/data.js';
	import {
		getMistakeQuestionKeys,
		recordAnswer,
		getQuestionProgress,
		subscribe
	} from '$lib/store.js';
	import type { Question, QuestionsData } from '$lib/types.js';

	let data = $state<QuestionsData | null>(null);
	let mistakeKeys = $state<string[]>([]);
	let mistakeQuestions = $state<Question[]>([]);

	// Practice mode
	let practicing = $state(false);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);

	let currentQuestion = $derived(mistakeQuestions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	onMount(async () => {
		data = await loadQuestions();
		refreshMistakes();

		const unsub = subscribe(() => {
			if (!practicing) refreshMistakes();
		});
		return unsub;
	});

	function refreshMistakes() {
		if (!data) return;
		mistakeKeys = getMistakeQuestionKeys();
		mistakeQuestions = mistakeKeys
			.map((key) => {
				const { section, id } = parseQuestionKey(key);
				return data!.questions.find((q) => q.section === section && q.id === id);
			})
			.filter((q): q is Question => !!q);
	}

	function startPractice() {
		if (mistakeQuestions.length === 0) return;
		practicing = true;
		currentIndex = 0;
		resetState();
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
			checkAnswer();
		}
	}

	function confirmMultiAnswer() {
		if (selectedAnswers.size === 0) return;
		checkAnswer();
	}

	function checkAnswer() {
		if (!currentQuestion || !currentQuestion.correct_answers) return;
		isAnswered = true;
		const correctSet = new Set(currentQuestion.correct_answers);
		isCorrect =
			selectedAnswers.size === correctSet.size &&
			[...selectedAnswers].every((a) => correctSet.has(a));
		recordAnswer(currentQuestion.section, currentQuestion.id, isCorrect);
	}

	function nextQuestion() {
		if (currentIndex < mistakeQuestions.length - 1) {
			currentIndex++;
			resetState();
		} else {
			practicing = false;
			refreshMistakes();
		}
	}

	function resetState() {
		selectedAnswers = new Set();
		isAnswered = false;
		isCorrect = false;
	}

	function optionClass(letter: string): string {
		if (!isAnswered) return selectedAnswers.has(letter) ? 'selected' : '';
		const isCorrectAnswer = currentQuestion?.correct_answers?.includes(letter);
		const wasSelected = selectedAnswers.has(letter);
		if (isCorrectAnswer) return 'correct';
		if (wasSelected && !isCorrectAnswer) return 'wrong';
		return 'dimmed';
	}

	// Group by section for list view
	let groupedMistakes = $derived.by(() => {
		const groups: Record<string, Question[]> = {};
		for (const q of mistakeQuestions) {
			if (!groups[q.section]) groups[q.section] = [];
			groups[q.section].push(q);
		}
		return groups;
	});

	function sectionName(sectionId: string): string {
		if (!data) return sectionId;
		const meta = data.metadata.sections.find((s) => s.id === sectionId);
		return meta?.name || sectionId;
	}
</script>

<div class="mistakes-page">
	<header class="page-header">
		{#if practicing}
			<button class="back-btn" onclick={() => { practicing = false; refreshMistakes(); }} aria-label="Назад">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</button>
			<span class="header-title">{currentIndex + 1} / {mistakeQuestions.length}</span>
			<div style="width: 40px"></div>
		{:else}
			<a href="/" class="back-btn" aria-label="Назад">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</a>
			<h1>Моје грешке</h1>
			<div style="width: 40px"></div>
		{/if}
	</header>

	{#if practicing && currentQuestion}
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
					{currentIndex < mistakeQuestions.length - 1 ? 'Следеће питање →' : '✓ Завршено'}
				</button>
			{/if}
		</main>

	{:else}
		<main class="list-content">
			{#if mistakeQuestions.length === 0}
				<div class="empty-state">
					<div class="empty-icon">🎉</div>
					<h2>Нема грешака!</h2>
					<p>Одлично, немате питања за понављање.</p>
					<a href="/" class="home-link">← Почетна</a>
				</div>
			{:else}
				<div class="practice-header">
					<p>{mistakeQuestions.length} питања за понављање</p>
					<button class="practice-btn" onclick={startPractice}>
						Вежбај грешке
					</button>
				</div>

				{#each Object.entries(groupedMistakes) as [sectionId, questions]}
					<div class="section-group">
						<h3 class="section-title">
							{sectionIcon(sectionId)} {sectionName(sectionId)}
							<span class="section-count">({questions.length})</span>
						</h3>
						{#each questions as q}
							{@const prog = getQuestionProgress(q.section, q.id)}
							<div class="mistake-item">
								<p class="mistake-text">{q.text}</p>
								{#if prog}
									<div class="mistake-stats">
										<span class="stat correct">✓ {prog.correct}</span>
										<span class="stat wrong">✗ {prog.wrong}</span>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			{/if}
		</main>
	{/if}
</div>

<style>
	.mistakes-page {
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

	/* List view */
	.list-content {
		padding: 1rem;
	}

	.practice-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	.practice-header p {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.practice-btn {
		padding: 0.5rem 1rem;
		background: var(--danger);
		color: white;
		border-radius: var(--radius-pill);
		font-weight: 600;
		font-size: 0.85rem;
	}

	.section-group {
		margin-bottom: 1rem;
	}

	.section-title {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
		padding: 0.25rem 0;
	}

	.section-count {
		font-weight: 400;
	}

	.mistake-item {
		background: var(--card);
		padding: 0.75rem;
		border-radius: var(--radius-sm);
		margin-bottom: 0.5rem;
		box-shadow: var(--shadow);
		border-left: 3px solid var(--danger);
	}

	.mistake-text {
		font-size: 0.85rem;
		line-height: 1.4;
		margin-bottom: 0.3rem;
	}

	.mistake-stats {
		display: flex;
		gap: 0.75rem;
	}

	.stat {
		font-size: 0.75rem;
		font-weight: 600;
	}

	.stat.correct {
		color: var(--success);
	}

	.stat.wrong {
		color: var(--danger);
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
	}

	.empty-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}

	.empty-state h2 {
		margin-bottom: 0.5rem;
	}

	.empty-state p {
		color: var(--text-secondary);
		margin-bottom: 1rem;
	}

	.home-link {
		color: var(--primary);
		font-weight: 500;
	}

	/* Question content (reused styles) */
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
</style>
