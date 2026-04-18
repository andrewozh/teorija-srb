<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks, questionKey, qText, oText } from '$lib/data.js';
	import {
		recordAnswer,
		getQuestionProgress,
		isBookmarked,
		toggleBookmark,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { Question, Chunk, Lang } from '$lib/types.js';

	let sectionId = $derived($page.params.section);
	let chunkIndex = $derived(parseInt($page.params.chunk, 10));

	let questions = $state<Question[]>([]);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let bookmarked = $state(false);
	let storeVersion = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	let currentQuestion = $derived(questions[currentIndex]);
	let qKey = $derived(currentQuestion ? questionKey(currentQuestion) : '');
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	$effect(() => {
		setPageTitle(sectionName(sectionId, lang));
	});

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
			lang = getSettings().lang;
			updateBookmarkState();
		});
		return unsub;
	});

	function updateBookmarkState() {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	}

	function pillState(index: number): string {
		if (!questions[index]) return 'unanswered';
		const q = questions[index];
		const prog = getQuestionProgress(q.section, q.id);
		if (index === currentIndex) return 'current';
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
	}

	function pillClass(state: string): string {
		switch (state) {
			case 'current': return 'btn-primary';
			case 'correct': return 'btn-outline-success';
			case 'wrong': return 'btn-outline-danger';
			default: return 'btn-outline-secondary';
		}
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

	$effect(() => {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	});

	let pillsContainer = $state<HTMLDivElement | undefined>(undefined);

	$effect(() => {
		if (pillsContainer && currentIndex >= 0) {
			const pill = pillsContainer.children[currentIndex] as HTMLElement;
			if (pill) {
				pill.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
			}
		}
	});
</script>

<div class="d-flex flex-column">
	<!-- Question number pills -->
	<div class="pills-scroll bg-body border-bottom" bind:this={pillsContainer}>
		{#each questions as _, i}
			<button
				class="btn btn-sm rounded-pill pill-btn {pillClass(pillState(i))}"
				onclick={() => goToQuestion(i)}
			>
				{i + 1}
			</button>
		{/each}
	</div>

	{#if currentQuestion}
		<main class="flex-grow-1 p-3 d-flex flex-column gap-3">
			<!-- Image -->
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="card border-0 shadow-sm overflow-hidden">
					<img src="{base}/images/{currentQuestion.image}" alt="Слика уз питање" class="card-img-top" />
				</div>
			{/if}

			<!-- Question text with bookmark -->
			<div class="card border-0 shadow-sm">
				<div class="card-body">
					<div class="d-flex align-items-start gap-2">
						<p class="mb-0 flex-grow-1" style="line-height:1.5;">{qText(currentQuestion, lang)}</p>
						<button
							class="btn btn-link text-body p-0 fs-5 flex-shrink-0"
							onclick={handleToggleBookmark}
							aria-label="Обележи"
						>
							{bookmarked ? '⭐' : '☆'}
						</button>
					</div>
					{#if hasMultipleAnswers}
						<span class="badge text-bg-primary mt-2">{t('question.multi', lang)} ({currentQuestion.correct_answers_count})</span>
					{/if}
					{#if !currentQuestion.correct_answers || currentQuestion.correct_answers.length === 0}
						<span class="badge text-bg-warning mt-2">⚠ {t('question.no_answer', lang)}</span>
					{/if}
				</div>
			</div>

			<!-- Options -->
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

			<!-- Multi-answer confirm button -->
			{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
				<button class="btn btn-primary btn-lg w-100" onclick={confirmMultiAnswer}>
					{t('question.confirm', lang)} ({selectedAnswers.size})
				</button>
			{/if}

			<!-- Next button -->
			{#if isAnswered && (!isCorrect || currentIndex === questions.length - 1)}
				<div>
					{#if currentIndex < questions.length - 1}
						<button class="btn btn-primary btn-lg w-100" onclick={nextQuestion}>
							{t('question.next', lang)} →
						</button>
					{:else}
						<a href="{base}/practice/{sectionId}" class="btn btn-success btn-lg w-100">
							✓ {t('question.correct', lang)}
						</a>
					{/if}
				</div>
			{/if}
		</main>
	{/if}
</div>

<style>
	.pills-scroll {
		display: flex;
		gap: 0.35rem;
		padding: 0.5rem 0.75rem;
		overflow-x: auto;
		scrollbar-width: none;
		flex-shrink: 0;
	}

	.pills-scroll::-webkit-scrollbar {
		display: none;
	}

	.pill-btn {
		min-width: 32px;
		height: 32px;
		font-size: 0.75rem;
		font-weight: 600;
		flex-shrink: 0;
		padding: 0 0.4rem;
	}
</style>
