<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey, questionKey, qText, oText } from '$lib/data.js';
	import {
		getMistakeQuestionKeys,
		recordAnswer,
		getQuestionProgress,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { Question, QuestionsData, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionPills from '$lib/components/QuestionPills.svelte';
	import AnswerOption from '$lib/components/AnswerOption.svelte';

	let data = $state<QuestionsData | null>(null);
	let mistakeKeys = $state<string[]>([]);
	let mistakeQuestions = $state<Question[]>([]);

	let practicing = $state(false);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let lang = $state<Lang>(getSettings().lang);

	let currentQuestion = $derived(mistakeQuestions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	let pillStates = $derived(mistakeQuestions.map((q, i) => {
		const prog = getQuestionProgress(q.section, q.id);
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
	}));

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

	function optionState(letter: string): 'idle' | 'selected' | 'correct' | 'wrong' | 'muted' {
		if (!isAnswered) return selectedAnswers.has(letter) ? 'selected' : 'idle';
		const isCorrectAnswer = currentQuestion?.correct_answers?.includes(letter);
		const wasSelected = selectedAnswers.has(letter);
		if (isCorrectAnswer) return 'correct';
		if (wasSelected && !isCorrectAnswer) return 'wrong';
		return 'muted';
	}

	let groupedMistakes = $derived.by(() => {
		const groups: Record<string, Question[]> = {};
		for (const q of mistakeQuestions) {
			if (!groups[q.section]) groups[q.section] = [];
			groups[q.section].push(q);
		}
		return groups;
	});
</script>

<div class="page">
	{#if practicing && currentQuestion}
		<!-- Practice mode -->
		<div class="q-header">
			<button class="q-header-btn" onclick={() => { practicing = false; refreshMistakes(); }}>
				<Icon name="back" size={20} />
			</button>
			<div class="q-header-center">
				<div class="q-header-counter">
					{String(currentIndex + 1).padStart(2, '0')}<span class="q-header-total"> / {mistakeQuestions.length}</span>
				</div>
			</div>
			<div style="width:36px"></div>
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
						{currentIndex < mistakeQuestions.length - 1 ? (lang === 'sr' ? 'Следеће' : 'Далее') : '✓'}
						<Icon name="chev-right" size={14} color="var(--accent-ink)" />
					</button>
				</div>
			{/if}
		</div>

	{:else}
		<!-- List mode -->
		<Header
			title={t('mistakes.title', lang)}
			onback={() => history.back()}
			onsettings={() => goto(`${base}/settings`)}
		/>

		<div class="scroll-area">
			{#if mistakeQuestions.length === 0}
				<div class="empty-center">
					<div class="empty-emoji">🎉</div>
					<div class="empty-msg">{t('mistakes.empty', lang)}</div>
					<a href="{base}/" class="back-link">← {t('exam.back', lang)}</a>
				</div>
			{:else}
				<div class="mistakes-header">
					<span class="mistakes-count">{mistakeQuestions.length} {t('home.mistakes.sub', lang)}</span>
					<button class="practice-btn" onclick={startPractice}>
						{t('mistakes.practice', lang)}
					</button>
				</div>

				{#each Object.entries(groupedMistakes) as [sId, questions]}
					<div class="mistake-group">
						<div class="mistake-group-title">
							{sectionName(sId, lang)}
							<span class="mistake-group-count">({questions.length})</span>
						</div>
						{#each questions as q}
							{@const prog = getQuestionProgress(q.section, q.id)}
							<div class="mistake-item">
								<p class="mistake-text">{qText(q, lang)}</p>
								{#if prog}
									<div class="mistake-stats">
										<span class="stat-correct">✓ {prog.correct}</span>
										<span class="stat-wrong">✗ {prog.wrong}</span>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 16px; }

	/* Question mode styles */
	.q-header {
		display: flex; align-items: center; gap: 8px;
		padding: 6px 16px 4px; height: 48px; flex-shrink: 0;
	}
	.q-header-btn {
		width: 36px; height: 36px; border-radius: 12px;
		border: none; background: transparent; color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer; flex-shrink: 0;
	}
	.q-header-center { flex: 1; text-align: center; }
	.q-header-counter {
		font-family: var(--font-mono); font-size: 13px;
		color: var(--ink); letter-spacing: 0.3px;
	}
	.q-header-total { color: var(--ink4); }

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

	/* List mode */
	.empty-center { text-align: center; padding: 60px 0; }
	.empty-emoji { font-size: 48px; margin-bottom: 12px; }
	.empty-msg { font-size: 16px; font-weight: 500; }
	.back-link {
		display: inline-block; margin-top: 16px;
		color: var(--accent); font-weight: 500; font-size: 14px;
	}

	.mistakes-header {
		display: flex; align-items: center; justify-content: space-between;
		margin-bottom: 16px;
	}
	.mistakes-count { font-size: 13px; color: var(--ink3); }
	.practice-btn {
		padding: 8px 16px; border-radius: 999px;
		background: var(--wrong); color: #fff;
		border: none; font-family: var(--font-ui);
		font-size: 13px; font-weight: 600; cursor: pointer;
	}

	.mistake-group { margin-bottom: 20px; }
	.mistake-group-title {
		font-size: 13px; font-weight: 600; color: var(--ink2);
		margin-bottom: 8px;
	}
	.mistake-group-count { font-weight: 400; color: var(--ink3); }

	.mistake-item {
		background: var(--surface);
		border-radius: 14px;
		padding: 12px 14px;
		margin-bottom: 5px;
		border: 0.5px solid var(--hairline);
		border-left: 3px solid var(--wrong);
	}
	.mistake-text { font-size: 13px; line-height: 1.4; margin-bottom: 4px; }
	.mistake-stats { display: flex; gap: 12px; }
	.stat-correct { font-size: 12px; font-weight: 600; color: var(--correct); }
	.stat-wrong { font-size: 12px; font-weight: 600; color: var(--wrong); }
</style>
