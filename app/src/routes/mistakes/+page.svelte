<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey, questionKey, sectionIcon, qText, oText } from '$lib/data.js';
	import {
		getMistakeQuestionKeys,
		recordAnswer,
		getQuestionProgress,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { Question, QuestionsData, Lang } from '$lib/types.js';

	let data = $state<QuestionsData | null>(null);
	let mistakeKeys = $state<string[]>([]);
	let mistakeQuestions = $state<Question[]>([]);

	// Practice mode
	let practicing = $state(false);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let lang = $state<Lang>(getSettings().lang);
	let isCorrect = $state(false);

	let currentQuestion = $derived(mistakeQuestions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	$effect(() => {
		setPageTitle(t('mistakes.title', lang));
	});

	onMount(async () => {
		data = await loadQuestions();
		refreshMistakes();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
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

	// Group by section for list view
	let groupedMistakes = $derived.by(() => {
		const groups: Record<string, Question[]> = {};
		for (const q of mistakeQuestions) {
			if (!groups[q.section]) groups[q.section] = [];
			groups[q.section].push(q);
		}
		return groups;
	});
</script>

<div class="d-flex flex-column min-vh-100">
	{#if practicing && currentQuestion}
		<!-- Practice header with counter -->
		<div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom bg-body">
			<button class="btn btn-link text-body p-2" onclick={() => { practicing = false; refreshMistakes(); }} aria-label={t('common.back', lang)}>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</button>
			<span class="text-body-secondary fw-semibold small">{currentIndex + 1} / {mistakeQuestions.length}</span>
			<div style="width:40px"></div>
		</div>

		<main class="flex-grow-1 p-3 d-flex flex-column gap-3">
			{#if currentQuestion.has_image && currentQuestion.image}
				<div class="card border-0 shadow-sm overflow-hidden">
					<img src="/images/{currentQuestion.image}" alt="Слика уз питање" class="card-img-top" />
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
					{currentIndex < mistakeQuestions.length - 1 ? t('question.next', lang) + ' →' : '✓'}
				</button>
			{/if}
		</main>

	{:else}
		<main class="p-3">
			{#if mistakeQuestions.length === 0}
				<div class="text-center py-5">
					<div class="fs-1 mb-3">🎉</div>
					<h2 class="h5 fw-bold">{t('mistakes.empty', lang)}</h2>
					<a href="/" class="text-primary fw-medium mt-3 d-inline-block">← {t('exam.back', lang)}</a>
				</div>
			{:else}
				<div class="d-flex align-items-center justify-content-between mb-3">
					<small class="text-body-secondary">{mistakeQuestions.length} {t('home.mistakes.sub', lang)}</small>
					<button class="btn btn-danger btn-sm rounded-pill fw-semibold" onclick={startPractice}>
						{t('mistakes.practice', lang)}
					</button>
				</div>

				{#each Object.entries(groupedMistakes) as [sId, questions]}
					<div class="mb-3">
						<h3 class="small fw-semibold text-body-secondary mb-2">
							{sectionIcon(sId)} {sectionName(sId, lang)}
							<span class="fw-normal">({questions.length})</span>
						</h3>
						{#each questions as q}
							{@const prog = getQuestionProgress(q.section, q.id)}
							<div class="card border-start border-danger border-3 shadow-sm mb-2">
								<div class="card-body py-2 px-3">
									<p class="small mb-1" style="line-height:1.4;">{qText(q, lang)}</p>
									{#if prog}
										<div class="d-flex gap-3">
											<small class="fw-semibold text-success">✓ {prog.correct}</small>
											<small class="fw-semibold text-danger">✗ {prog.wrong}</small>
										</div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/each}
			{/if}
		</main>
	{/if}
</div>
