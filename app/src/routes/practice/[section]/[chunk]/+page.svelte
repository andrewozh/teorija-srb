<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks, questionKey } from '$lib/data.js';
	import {
		recordAnswer,
		getQuestionProgress,
		isBookmarked,
		toggleBookmark,
		subscribe
	} from '$lib/store.js';
	import type { Question, Chunk } from '$lib/types.js';

	let sectionId = $derived($page.params.section);
	let chunkIndex = $derived(parseInt($page.params.chunk, 10));

	let questions = $state<Question[]>([]);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let bookmarked = $state(false);
	let storeVersion = $state(0);

	let currentQuestion = $derived(questions[currentIndex]);
	let qKey = $derived(currentQuestion ? questionKey(currentQuestion) : '');
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	onMount(async () => {
		const data = await loadQuestions();
		const sectionQuestions = getQuestionsBySection(data, sectionId);
		const chunks = getChunks(sectionQuestions);
		const chunk = chunks[chunkIndex];
		if (chunk) {
			questions = chunk.questions;
		}
		updateBookmarkState();

		const unsub = subscribe(() => {
			storeVersion++;
			updateBookmarkState();
		});
		return unsub;
	});

	function updateBookmarkState() {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	}

	// Track question pill states
	function pillState(index: number): string {
		if (!questions[index]) return 'unanswered';
		const q = questions[index];
		const prog = getQuestionProgress(q.section, q.id);
		if (index === currentIndex) return 'current';
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
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
			checkAnswer();
		}
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

	function confirmMultiAnswer() {
		if (selectedAnswers.size === 0) return;
		checkAnswer();
	}

	function nextQuestion() {
		if (currentIndex < questions.length - 1) {
			currentIndex++;
			resetState();
		}
	}

	function goToQuestion(index: number) {
		currentIndex = index;
		resetState();
	}

	function resetState() {
		selectedAnswers = new Set();
		isAnswered = false;
		isCorrect = false;
		updateBookmarkState();
	}

	function handleToggleBookmark() {
		if (currentQuestion) {
			toggleBookmark(questionKey(currentQuestion));
		}
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

	let autoAdvanceTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		if (isAnswered && isCorrect && currentIndex < questions.length - 1) {
			autoAdvanceTimer = setTimeout(() => {
				nextQuestion();
			}, 800);
		}
		return () => {
			if (autoAdvanceTimer) clearTimeout(autoAdvanceTimer);
		};
	});

	// Update bookmark when question changes
	$effect(() => {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	});

	let pillsContainer = $state<HTMLDivElement | undefined>(undefined);

	$effect(() => {
		// Scroll current pill into view
		if (pillsContainer && currentIndex >= 0) {
			const pill = pillsContainer.children[currentIndex] as HTMLElement;
			if (pill) {
				pill.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
			}
		}
	});
</script>

<div class="question-page">
	<header class="page-header">
		<a href="/practice/{sectionId}" class="back-btn" aria-label="Назад">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 18l-6-6 6-6"/>
			</svg>
		</a>
		<span class="header-title">
			{currentIndex + 1} / {questions.length}
		</span>
		<button
			class="bookmark-btn"
			class:active={bookmarked}
			onclick={handleToggleBookmark}
			aria-label="Обележи"
		>
			{bookmarked ? '⭐' : '☆'}
		</button>
	</header>

	<!-- Question number pills -->
	<div class="pills-scroll" bind:this={pillsContainer}>
		{#each questions as _, i}
			<button
				class="pill {pillState(i)}"
				onclick={() => goToQuestion(i)}
			>
				{i + 1}
			</button>
		{/each}
	</div>

	{#if currentQuestion}
		<main class="question-content">
			<!-- Image -->
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="question-image">
					<img src="/images/{currentQuestion.image}" alt="Слика уз питање" />
				</div>
			{/if}

			<!-- Question text -->
			<div class="question-text">
				<p>{currentQuestion.text}</p>
				{#if hasMultipleAnswers}
					<span class="multi-badge">Више одговора ({currentQuestion.correct_answers_count})</span>
				{/if}
				{#if !currentQuestion.correct_answers || currentQuestion.correct_answers.length === 0}
					<span class="no-answer-badge">⚠ Одговор није доступан</span>
				{/if}
			</div>

			<!-- Options -->
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

			<!-- Multi-answer confirm button -->
			{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
				<button class="confirm-btn" onclick={confirmMultiAnswer}>
					Потврди одговор ({selectedAnswers.size} изабрано)
				</button>
			{/if}

			<!-- Next button (shown after wrong answer or last question) -->
			{#if isAnswered && (!isCorrect || currentIndex === questions.length - 1)}
				<div class="next-area">
					{#if currentIndex < questions.length - 1}
						<button class="next-btn" onclick={nextQuestion}>
							Следеће питање →
						</button>
					{:else}
						<a href="/practice/{sectionId}" class="next-btn done-btn">
							✓ Завршено
						</a>
					{/if}
				</div>
			{/if}
		</main>
	{/if}
</div>

<style>
	.question-page {
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

	.back-btn:active {
		background: var(--bg-secondary);
	}

	.bookmark-btn {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.3rem;
		border-radius: 50%;
		flex-shrink: 0;
		transition: transform 0.2s;
	}

	.bookmark-btn:active {
		transform: scale(1.2);
	}

	.bookmark-btn.active {
		animation: pop 0.3s ease;
	}

	@keyframes pop {
		50% { transform: scale(1.3); }
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
		flex-shrink: 0;
	}

	.pills-scroll::-webkit-scrollbar {
		display: none;
	}

	.pill {
		min-width: 32px;
		height: 32px;
		border-radius: var(--radius-pill);
		font-size: 0.75rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		border: 2px solid transparent;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		transition: all 0.2s;
	}

	.pill.current {
		background: var(--primary);
		color: white;
		border-color: var(--primary);
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

	/* Content */
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

	.question-image img {
		width: 100%;
		height: auto;
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

	.no-answer-badge {
		display: inline-block;
		margin-top: 0.5rem;
		padding: 0.2rem 0.6rem;
		background: var(--warning-light);
		color: var(--warning);
		border-radius: var(--radius-pill);
		font-size: 0.7rem;
		font-weight: 600;
	}

	/* Options */
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

	.option-card:active:not(:disabled) {
		transform: scale(0.98);
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
		min-width: 1.2rem;
	}

	.option-text {
		flex: 1;
		font-size: 0.9rem;
		line-height: 1.4;
	}

	.option-icon {
		flex-shrink: 0;
		font-weight: 700;
		font-size: 1rem;
	}

	.option-card.correct .option-icon {
		color: var(--success);
	}

	.option-card.wrong .option-icon {
		color: var(--danger);
	}

	/* Confirm button for multi-answer */
	.confirm-btn {
		padding: 0.85rem;
		background: var(--primary);
		color: white;
		border-radius: var(--radius);
		font-weight: 600;
		font-size: 0.95rem;
		transition: opacity 0.2s;
	}

	.confirm-btn:active {
		opacity: 0.8;
	}

	/* Next button */
	.next-area {
		padding-top: 0.25rem;
	}

	.next-btn {
		display: block;
		width: 100%;
		padding: 0.85rem;
		background: var(--primary);
		color: white;
		border-radius: var(--radius);
		font-weight: 600;
		font-size: 0.95rem;
		text-align: center;
		transition: opacity 0.2s;
	}

	.next-btn:active {
		opacity: 0.8;
	}

	.done-btn {
		background: var(--success);
	}
</style>
