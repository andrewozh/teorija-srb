<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
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
	let lang = $state<Lang>(getSettings().lang);

	// Per-question answer state
	let questionStates = $state<Record<number, {
		selected: Set<string>;
		answered: boolean;
		correct: boolean;
	}>>({});

	function getQState(index: number) {
		return questionStates[index] ?? { selected: new Set<string>(), answered: false, correct: false };
	}

	let currentQuestion = $derived(questions[currentIndex]);
	let currentQState = $derived(getQState(currentIndex));
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);
	let currentQProg = $derived(currentQuestion ? getQuestionProgress(currentQuestion.section, currentQuestion.id) : null);
	let bookmarked = $state(false);

	let pillStates = $derived(questions.map((q, i) => {
		if (i === currentIndex) return 'current';
		const qs = getQState(i);
		if (qs.answered && qs.correct) return 'correct';
		if (qs.answered && !qs.correct) return 'wrong';
		const prog = getQuestionProgress(q.section, q.id);
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
	}));

	// Carousel ref
	let carouselEl = $state<HTMLDivElement | undefined>(undefined);
	let programmaticScroll = false;

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

	function selectAnswer(qIndex: number, letter: string) {
		const qs = getQState(qIndex);
		if (qs.answered) return;

		const q = questions[qIndex];
		const isMulti = q.correct_answers_count > 1;

		const newSelected = new Set(qs.selected);
		if (isMulti) {
			if (newSelected.has(letter)) newSelected.delete(letter);
			else newSelected.add(letter);
			questionStates[qIndex] = { ...qs, selected: newSelected };
		} else {
			questionStates[qIndex] = { ...qs, selected: new Set([letter]) };
			// Auto-check for single answer
			checkAnswerForQuestion(qIndex, new Set([letter]));
		}
	}

	function checkAnswerForQuestion(qIndex: number, selected?: Set<string>) {
		const q = questions[qIndex];
		if (!q || !q.correct_answers) return;
		const qs = getQState(qIndex);
		const sel = selected ?? qs.selected;
		const correctSet = new Set(q.correct_answers);
		const isCorrect =
			sel.size === correctSet.size &&
			[...sel].every((a) => correctSet.has(a));
		questionStates[qIndex] = { selected: sel, answered: true, correct: isCorrect };
		recordAnswer(q.section, q.id, isCorrect);
	}

	function confirmMultiAnswer(qIndex: number) {
		const qs = getQState(qIndex);
		if (qs.selected.size === 0) return;
		checkAnswerForQuestion(qIndex);
	}

	function scrollToSlide(index: number) {
		if (!carouselEl) return;
		programmaticScroll = true;
		const slideWidth = carouselEl.clientWidth;
		carouselEl.scrollTo({ left: slideWidth * index, behavior: 'smooth' });
		// Reset programmatic flag after scroll settles
		setTimeout(() => { programmaticScroll = false; }, 400);
	}

	function nextQuestion() {
		if (currentIndex < questions.length - 1) {
			scrollToSlide(currentIndex + 1);
		} else {
			goto(`${base}/practice/${sectionId}`);
		}
	}

	function goToQuestion(index: number) {
		scrollToSlide(index);
	}

	function handleCarouselScroll() {
		if (!carouselEl || programmaticScroll) return;
		const slideWidth = carouselEl.clientWidth;
		if (slideWidth === 0) return;
		const newIndex = Math.round(carouselEl.scrollLeft / slideWidth);
		if (newIndex !== currentIndex && newIndex >= 0 && newIndex < questions.length) {
			currentIndex = newIndex;
			updateBookmarkState();
		}
	}

	// Also update currentIndex when programmatic scroll ends (scrollend or fallback)
	function handleScrollEnd() {
		if (!carouselEl) return;
		const slideWidth = carouselEl.clientWidth;
		if (slideWidth === 0) return;
		const newIndex = Math.round(carouselEl.scrollLeft / slideWidth);
		if (newIndex >= 0 && newIndex < questions.length) {
			currentIndex = newIndex;
			programmaticScroll = false;
			updateBookmarkState();
		}
	}

	function handleToggleBookmark() {
		if (currentQuestion) {
			toggleBookmark(questionKey(currentQuestion));
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	}

	function optionStateForQuestion(qIndex: number, letter: string): 'idle' | 'selected' | 'correct' | 'wrong' | 'muted' {
		const qs = getQState(qIndex);
		const q = questions[qIndex];
		if (!qs.answered) {
			return qs.selected.has(letter) ? 'selected' : 'idle';
		}
		const isCorrectAnswer = q?.correct_answers?.includes(letter);
		const wasSelected = qs.selected.has(letter);
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

{#if questions.length > 0}
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

	<!-- Carousel -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="carousel"
		bind:this={carouselEl}
		onscroll={handleCarouselScroll}
		onscrollend={handleScrollEnd}
	>
		{#each questions as q, i}
			{@const qs = getQState(i)}
			{@const isMulti = q.correct_answers_count > 1}
			{@const qProg = getQuestionProgress(q.section, q.id)}
			<div class="slide">
				<div class="slide-body">
					<!-- Tags + Image -->
					<div class="q-media" class:q-media-has-image={q.has_image && q.image}>
						<div class="q-tags">
							{#if q.is_changed}
								<Tag tone="accent">
									<span class="tag-dot accent-dot"></span>
									{lang === 'sr' ? 'Измењено' : 'Изменено'}
								</Tag>
							{/if}
							{#if q.is_new}
								<Tag tone="accent">
									<span class="tag-dot accent-dot"></span>
									{lang === 'sr' ? 'Ново' : 'Новый'}
								</Tag>
							{/if}
							{#if qProg && qProg.wrong > 0}
								<Tag tone="wrong">
									<Icon name="warn" size={10} color="var(--wrong)" stroke={2} />
									{lang === 'sr' ? 'Претходно погрешно' : 'Ранее неверно'}
								</Tag>
							{/if}
						</div>
						{#if q.has_image && q.image}
							<img src="{base}/images/{q.image}" alt="" class="q-image" loading="lazy" />
						{/if}
					</div>

					<!-- Question text -->
					<div class="q-text">{qText(q, lang)}</div>
					<div class="q-meta">
						{isMulti
							? (lang === 'sr' ? 'Изабери више одговора' : 'Выберите несколько ответов')
							: (lang === 'sr' ? 'Изабери један одговор' : 'Выберите один ответ')}
						· {q.points} {lang === 'sr' ? 'поен' : 'балл'}
					</div>
				</div>

				<!-- Answers zone -->
				<div class="slide-answers">
					{#each q.options as option}
						<AnswerOption
							letter={option.letter}
							text={oText(option, lang)}
							state={optionStateForQuestion(i, option.letter)}
							multi={isMulti}
							onclick={() => selectAnswer(i, option.letter)}
						/>
					{/each}

					<!-- Multi-answer confirm -->
					{#if isMulti && !qs.answered && qs.selected.size > 0}
						<button class="q-confirm-btn" onclick={() => confirmMultiAnswer(i)}>
							{t('question.confirm', lang)} ({qs.selected.size})
						</button>
					{/if}

					<!-- Footer -->
					<div class="q-footer">
						<button class="q-footer-icon" onclick={() => { updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' }); }}>
							<Icon name="language" size={19} stroke={1.6} />
						</button>
						<button
							class="q-footer-icon"
							class:q-footer-active={i === currentIndex && bookmarked}
							onclick={handleToggleBookmark}
						>
							<Icon name={i === currentIndex && bookmarked ? 'bookmark-fill' : 'bookmark'} size={19} stroke={1.6} />
						</button>
						<button class="q-footer-icon" onclick={() => {}}>
							<Icon name="flag" size={19} stroke={1.6} />
						</button>
						<div class="q-footer-spacer"></div>
						{#if qs.answered}
							<button class="q-next-btn q-next-accent" onclick={nextQuestion}>
								{i < questions.length - 1
									? (lang === 'sr' ? 'Следеће' : 'Далее')
									: '✓'}
								<Icon name="chev-right" size={14} color="var(--accent-ink)" />
							</button>
						{/if}
					</div>
				</div>
			</div>
		{/each}
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

	/* Carousel */
	.carousel {
		flex: 1;
		display: flex;
		overflow-x: auto;
		overflow-y: hidden;
		scroll-snap-type: x mandatory;
		scrollbar-width: none;
		-webkit-overflow-scrolling: touch;
	}
	.carousel::-webkit-scrollbar { display: none; }

	/* Slide */
	.slide {
		min-width: 100%;
		width: 100%;
		flex-shrink: 0;
		scroll-snap-align: start;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.slide-body {
		flex: 1;
		overflow-y: auto;
		padding: 16px 16px 8px;
		-webkit-overflow-scrolling: touch;
	}

	.slide-answers {
		padding: 12px 14px 14px;
		padding-bottom: calc(14px + env(safe-area-inset-bottom));
		display: flex; flex-direction: column; gap: 8px;
		background: var(--answer-zone-bg);
		flex-shrink: 0;
		border-top: 0.5px solid var(--hairline);
	}

	/* Media / Tags */
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

	/* Confirm button */
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
