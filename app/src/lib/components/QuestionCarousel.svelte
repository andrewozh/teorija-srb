<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { questionKey, qText, oText } from '$lib/data.js';
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
	import Icon from '$lib/components/Icon.svelte';

	import QuestionPills from '$lib/components/QuestionPills.svelte';
	import AnswerOption from '$lib/components/AnswerOption.svelte';

	let {
		questions,
		headerTitle,
		headerSub = undefined,
		showLangToggle = true,
		showBookmark = true,
		showFlag = true,
		showTimer = false,
		timerSeconds = 2700,
		forceLang = undefined,
		onBack,
		onComplete = undefined,
		score = $bindable(0),
		wrongIds = $bindable<string[]>([]),
	}: {
		questions: Question[];
		headerTitle: string;
		headerSub?: string;
		showLangToggle?: boolean;
		showBookmark?: boolean;
		showFlag?: boolean;
		showTimer?: boolean;
		timerSeconds?: number;
		forceLang?: Lang;
		onBack: () => void;
		onComplete?: () => void;
		score?: number;
		wrongIds?: string[];
	} = $props();

	let currentIndex = $state(0);
	let lang = $state<Lang>(forceLang ?? getSettings().lang);

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

	// Timer state
	let timerRemaining = $state(timerSeconds);
	let timerInterval: ReturnType<typeof setInterval> | undefined = undefined;

	// Carousel ref
	let carouselEl = $state<HTMLDivElement | undefined>(undefined);
	let programmaticScroll = false;

	onMount(() => {
		updateBookmarkState();

		const unsub = subscribe(() => {
			if (!forceLang) lang = getSettings().lang;
			updateBookmarkState();
		});

		// Start timer if enabled
		if (showTimer) {
			timerRemaining = timerSeconds;
			timerInterval = setInterval(() => {
				timerRemaining -= 1;
				if (timerRemaining <= 0) {
					clearInterval(timerInterval);
					timerInterval = undefined;
					onComplete?.();
				}
			}, 1000);
		}

		return () => {
			unsub();
			if (timerInterval) clearInterval(timerInterval);
		};
	});

	function formatTimer(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
	}

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
		if (isCorrect) {
			score += q.points;
		} else {
			wrongIds = [...wrongIds, questionKey(q)];
		}
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
			onComplete?.();
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
		<button class="q-header-btn" onclick={onBack}>
			<Icon name="back" size={20} />
		</button>
		<div class="q-header-center">
			<div class="q-header-context">
				{headerTitle}{#if headerSub} · {headerSub}{/if}
			</div>
			{#if showTimer}
				<div class="q-header-counter q-header-timer">
					{formatTimer(timerRemaining)}
				</div>
			{:else}
				<div class="q-header-counter">
					{String(currentIndex + 1).padStart(2, '0')}<span class="q-header-total"> / {questions.length}</span>
				</div>
			{/if}
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
				<div class="slide-body" class:has-image={q.has_image && q.image}>
					<!-- Image -->
					<div class="q-media" class:q-media-has-image={q.has_image && q.image}>
						{#if q.has_image && q.image}
							<img
								src="{base}/images/{q.image}"
								alt=""
								class="q-image"
								loading="lazy"
								onload={(e) => {
									const img = e.currentTarget as HTMLImageElement;
									const displayWidth = img.clientWidth;
									const scale = displayWidth / img.naturalWidth;
									const displayHeight = img.naturalHeight * scale;
									if (img.parentElement) img.parentElement.style.minHeight = (displayHeight * 0.3) + 'px';
								}}
							/>
						{/if}
					</div>

					<!-- Question text (never shrinks) -->
					<div class="q-text-wrap">
						<div class="q-text">{qText(q, lang)}</div>
						<div class="q-meta">
							{#if q.is_changed}<span class="meta-dot meta-dot-changed" title={lang === 'sr' ? 'Измењено' : 'Изменено'}></span>{/if}
							{#if q.is_new}<span class="meta-dot meta-dot-new" title={lang === 'sr' ? 'Ново' : 'Новый'}></span>{/if}
							{#if qProg && qProg.wrong > 0}<span class="meta-dot meta-dot-wrong" title={lang === 'sr' ? 'Претходно погрешно' : 'Ранее неверно'}></span>{/if}
							{isMulti
								? (lang === 'sr' ? 'Изабери више одговора' : 'Выберите несколько ответов')
								: (lang === 'sr' ? 'Изабери један одговор' : 'Выберите один ответ')}
							· {q.points} {lang === 'sr' ? 'поен' : 'балл'}
						</div>
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
					<div class="footer-spacer"></div>
				</div>

				<!-- Footer (fixed at bottom of slide) -->
				<div class="q-footer">
					{#if showLangToggle}
						<button class="q-footer-icon" onclick={() => { updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' }); }}>
							<Icon name="language" size={19} stroke={1.6} />
						</button>
					{/if}
					{#if showBookmark}
						<button
							class="q-footer-icon"
							class:q-footer-active={i === currentIndex && bookmarked}
							onclick={handleToggleBookmark}
						>
							<Icon name={i === currentIndex && bookmarked ? 'bookmark-fill' : 'bookmark'} size={19} stroke={1.6} />
						</button>
					{/if}
					{#if showFlag}
						<button class="q-footer-icon" onclick={() => {}}>
							<Icon name="flag" size={19} stroke={1.6} />
						</button>
					{/if}
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
	.q-header-timer {
		font-size: 15px;
		font-weight: 600;
		letter-spacing: 1px;
	}

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
		position: relative;
	}

	/*
	   Two blocks sharing space between header and footer:
	   - Question: natural size, shrinks FIRST, max 60%
	   - Answers: natural size, NEVER shrinks, fills remaining, scrolls
	*/
	.slide-body {
		flex: 0 999 auto;     /* no grow, SHRINKS FIRST (999 priority), basis = content */
		min-height: 20%;
		max-height: 60%;
		overflow: hidden;
		padding: 8px 16px 8px;
		position: relative;
		z-index: 2;
		background: var(--bg);
		display: flex;
		flex-direction: column;
		justify-content: center;
		box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.12);
	}
	.slide-body.has-image {
		min-height: 30%;
	}

	.slide-answers {
		flex: 1 1 auto;       /* GROWS to fill, can shrink (after question hits min), basis = content */
		min-height: 0;        /* allows shrink below content → triggers overflow scroll */
		overflow-y: auto;
		-webkit-overflow-scrolling: touch;
		padding: 10px 14px 8px;
		display: flex; flex-direction: column; gap: 8px;
		background: var(--answer-zone-bg);
		border-top: 0.5px solid var(--hairline);
		z-index: 1;
	}

	/* Media / Tags — shrinks when space is tight, but doesn't grow */
	.q-media {
		position: relative;
		margin-bottom: 6px;
		flex: 0 1 auto;
		min-height: 0;
		overflow: hidden;
	}
	/* Meta dots for question status */
	.meta-dot {
		display: inline-block;
		width: 8px; height: 8px;
		border-radius: 50%;
		margin-right: 4px;
		vertical-align: middle;
		position: relative;
		top: -1px;
	}
	.meta-dot-changed { background: var(--accent); }
	.meta-dot-new { background: #44aa44; }
	.meta-dot-wrong { background: var(--wrong); }

	.q-image {
		width: 100%;
		height: 100%;
		object-fit: contain;
		object-position: center top;
		display: block;
	}

	/* Text + meta — never shrink */
	.q-text-wrap {
		flex-shrink: 0;
	}
	.q-text {
		font-size: 16px; font-weight: 500;
		line-height: 1.4; letter-spacing: -0.2px;
		color: var(--ink);
	}
	.q-meta {
		font-family: var(--font-mono); font-size: 11px;
		color: var(--ink3); margin-top: 4px;
		letter-spacing: 0.3px;
	}

	/* Spacer at bottom of answers to account for absolute footer */
	.footer-spacer {
		flex-shrink: 0;
		height: calc(52px + env(safe-area-inset-bottom));
	}

	/* Confirm button */
	.q-confirm-btn {
		width: 100%; height: 48px; border-radius: 16px;
		background: var(--accent); color: var(--accent-ink);
		border: none; font-family: var(--font-ui);
		font-size: 15px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
	}

	/* Footer — fixed at bottom of each slide, above answers in z-order */
	.q-footer {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		display: flex; align-items: center; gap: 4px;
		padding: 4px 14px;
		padding-bottom: calc(4px + env(safe-area-inset-bottom));
		border-top: 0.5px solid var(--hairline);
		background: var(--bg);
		z-index: 3;
		box-shadow: 0 -4px 12px -2px rgba(0, 0, 0, 0.12);
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
