<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks, questionKey, qText, oText } from '$lib/data.js';
	import {
		recordAnswer,
		getQuestionProgress,
		isBookmarked,
		toggleBookmark,
		subscribe,
		getSettings,
		updateSettings
	} from '$lib/store.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { Question, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import Tag from '$lib/components/Tag.svelte';
	import QuestionPills from '$lib/components/QuestionPills.svelte';
	import AnswerOption from '$lib/components/AnswerOption.svelte';

	let sectionId = $derived($page.params.section);
	let chunkIndex = $derived(parseInt($page.params.chunk, 10));

	let questions = $state<Question[]>([]);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let bookmarked = $state(false);
	let lang = $state<Lang>(getSettings().lang);

	let currentQuestion = $derived(questions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);
	let currentQProg = $derived(currentQuestion ? getQuestionProgress(currentQuestion.section, currentQuestion.id) : null);

	let pillStates = $derived(questions.map((q, i) => {
		if (i === currentIndex) return 'current';
		const prog = getQuestionProgress(q.section, q.id);
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
	}));

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
		} else {
			goto(`${base}/practice/${sectionId}`);
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
			bookmarked = !bookmarked;
		}
	}

	function optionState(letter: string): 'idle' | 'selected' | 'correct' | 'wrong' | 'muted' {
		if (!isAnswered) {
			return selectedAnswers.has(letter) ? 'selected' : 'idle';
		}
		const isCorrectAnswer = currentQuestion?.correct_answers?.includes(letter);
		const wasSelected = selectedAnswers.has(letter);
		if (isCorrectAnswer) return 'correct';
		if (wasSelected && !isCorrectAnswer) return 'wrong';
		return 'muted';
	}

	$effect(() => {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	});
</script>

{#if currentQuestion}
<div class="qpage">
	<!-- Custom header -->
	<div class="q-header">
		<button class="q-header-btn" onclick={() => goto(`${base}/practice/${sectionId}`)}>
			<Icon name="back" size={20} />
		</button>
		<div class="q-header-center">
			<div class="q-header-context">
				{sectionName(sectionId, lang)} · {lang === 'sr' ? 'блок' : 'блок'} {String(chunkIndex + 1).padStart(2, '0')}
			</div>
			<div class="q-header-counter">
				{String(currentIndex + 1).padStart(2, '0')}<span class="q-header-total"> / {questions.length}</span>
			</div>
		</div>
		<button class="q-header-btn" onclick={() => goto(`${base}/settings`)}>
			<Icon name="settings" size={19} stroke={1.5} />
		</button>
	</div>

	<QuestionPills current={currentIndex} states={pillStates} onclick={goToQuestion} />

	<!-- Question body -->
	<div class="q-body">
		<!-- Tags -->
		<!-- Image + overlaid tags -->
		<div class="q-media" class:q-media-has-image={currentQuestion.has_image && currentQuestion.image}>
			<div class="q-tags">
				{#if currentQuestion.is_changed}
					<Tag tone="accent">
						<span class="tag-dot accent-dot"></span>
						{lang === 'sr' ? 'Измењено' : 'Изменено'}
					</Tag>
				{/if}
				{#if currentQuestion.is_new}
					<Tag tone="accent">
						<span class="tag-dot accent-dot"></span>
						{lang === 'sr' ? 'Ново' : 'Новый'}
					</Tag>
				{/if}
				{#if currentQProg && currentQProg.wrong > 0}
					<Tag tone="wrong">
						<Icon name="warn" size={10} color="var(--wrong)" stroke={2} />
						{lang === 'sr' ? 'Претходно погрешно' : 'Ранее неверно'}
					</Tag>
				{/if}
			</div>
			{#if currentQuestion.has_image && currentQuestion.image}
				<img src="{base}/images/{currentQuestion.image}" alt="" class="q-image" />
			{/if}
		</div>

		<!-- Question text -->
		<div class="q-text">{qText(currentQuestion, lang)}</div>
		<div class="q-meta">
			{hasMultipleAnswers
				? (lang === 'sr' ? 'Изабери више одговора' : 'Выберите несколько ответов')
				: (lang === 'sr' ? 'Изабери један одговор' : 'Выберите один ответ')}
			· {currentQuestion.points} {lang === 'sr' ? 'поен' : 'балл'}
		</div>
	</div>

	<!-- Answers zone -->
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

		<!-- Multi-answer confirm -->
		{#if hasMultipleAnswers && !isAnswered && selectedAnswers.size > 0}
			<button class="q-confirm-btn" onclick={confirmMultiAnswer}>
				{t('question.confirm', lang)} ({selectedAnswers.size})
			</button>
		{/if}

		<!-- Footer -->
		<div class="q-footer">
			<button class="q-footer-icon" onclick={() => { updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' }); }}>
				<Icon name="swap" size={19} stroke={1.6} />
			</button>
			<button
				class="q-footer-icon"
				class:q-footer-active={bookmarked}
				onclick={handleToggleBookmark}
			>
				<Icon name={bookmarked ? 'bookmark-fill' : 'bookmark'} size={19} stroke={1.6} />
			</button>
			<button class="q-footer-icon" onclick={() => {}}>
				<Icon name="flag" size={19} stroke={1.6} />
			</button>
			<div class="q-footer-spacer"></div>
			{#if isAnswered}
				<button class="q-next-btn q-next-accent" onclick={nextQuestion}>
					{currentIndex < questions.length - 1
						? (lang === 'sr' ? 'Следеће' : 'Далее')
						: '✓'}
					<Icon name="chev-right" size={14} color="var(--accent-ink)" />
				</button>
			{/if}
		</div>
	</div>
</div>
{/if}

<style>
	.qpage {
		position: fixed;
		inset: 0;
		display: flex;
		flex-direction: column;
		background: var(--bg);
		padding-top: env(safe-area-inset-top);
		z-index: 10;
	}

	/* Header */
	.q-header {
		display: flex; align-items: center; gap: 8px;
		padding: 6px 16px 4px; height: 48px;
		flex-shrink: 0;
	}
	.q-header-btn {
		width: 36px; height: 36px; border-radius: 12px;
		border: none; background: transparent; color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer; flex-shrink: 0;
	}
	.q-header-center { flex: 1; text-align: center; }
	.q-header-context {
		font-family: var(--font-mono); font-size: 9px;
		color: var(--ink3); letter-spacing: 1px;
		text-transform: uppercase; margin-bottom: 2px;
	}
	.q-header-counter {
		font-family: var(--font-mono); font-size: 13px;
		color: var(--ink); letter-spacing: 0.3px;
	}
	.q-header-total { color: var(--ink4); }

	/* Body */
	.q-body { flex: 1; overflow: auto; padding: 16px 16px 8px; }
	.q-media { position: relative; margin-bottom: 10px; }
	.q-media-has-image .q-tags { position: absolute; top: 8px; left: 8px; z-index: 2; }
	.q-tags {
		display: flex; gap: 6px; flex-wrap: wrap;
	}
	.tag-dot {
		width: 5px; height: 5px; border-radius: 3px;
		display: inline-block;
	}
	.accent-dot { background: var(--accent); }

	.q-image-wrap {
		width: 100%;
		border-radius: 16px;
		overflow: hidden;
		border: 0.5px solid var(--hairline);
		margin-bottom: 14px;
	}
	.q-image { width: 100%; display: block; }

	.q-text {
		font-size: 16px; font-weight: 500;
		line-height: 1.4; letter-spacing: -0.2px;
		color: var(--ink);
	}
	.q-meta {
		font-family: var(--font-mono); font-size: 11px;
		color: var(--ink3); margin-top: 6px;
		letter-spacing: 0.3px;
	}

	/* Answers */
	.q-answers {
		padding: 8px 10px 8px;
		padding-bottom: calc(8px + env(safe-area-inset-bottom));
		display: flex; flex-direction: column; gap: 8px;
		background: var(--answer-zone-bg);
		flex-shrink: 0;
		border-top: 0.5px solid var(--hairline);
		flex-shrink: 0;
	}

	.q-confirm-btn {
		width: 100%; height: 48px; border-radius: 16px;
		background: var(--accent); color: var(--accent-ink);
		border: none; font-family: var(--font-ui);
		font-size: 15px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
	}

	/* Footer */
	.q-footer {
		display: flex; align-items: center; gap: 4px;
		margin-top: 6px;
	}
	.q-footer-icon {
		width: 44px; height: 44px; border-radius: 12px;
		background: transparent; border: none;
		color: var(--ink2);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer;
	}
	.q-footer-active {
		background: var(--accent-wash);
		color: var(--accent);
	}
	.q-footer-spacer { flex: 1; }

	.q-next-btn {
		height: 44px; padding: 0 22px; border-radius: 14px;
		border: none; font-family: var(--font-ui);
		font-size: 14px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
		display: flex; align-items: center; gap: 6px;
	}
	.q-next-accent {
		background: var(--accent);
		color: var(--accent-ink);
	}
</style>
