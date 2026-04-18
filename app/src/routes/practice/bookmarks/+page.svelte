<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey, questionKey, qText, oText } from '$lib/data.js';
	import {
		getBookmarks,
		recordAnswer,
		isBookmarked,
		toggleBookmark,
		subscribe,
		getSettings,
		updateSettings,
		getQuestionProgress
	} from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Question, QuestionsData, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionPills from '$lib/components/QuestionPills.svelte';
	import AnswerOption from '$lib/components/AnswerOption.svelte';

	let data = $state<QuestionsData | null>(null);
	let questions = $state<Question[]>([]);
	let currentIndex = $state(0);
	let selectedAnswers = $state<Set<string>>(new Set());
	let isAnswered = $state(false);
	let isCorrect = $state(false);
	let bookmarked = $state(true);
	let lang = $state<Lang>(getSettings().lang);

	let currentQuestion = $derived(questions[currentIndex]);
	let hasMultipleAnswers = $derived(currentQuestion ? currentQuestion.correct_answers_count > 1 : false);

	let pillStates = $derived(questions.map((q, i) => {
		if (i === currentIndex) return 'current';
		const prog = getQuestionProgress(q.section, q.id);
		if (prog && prog.correct > 0) return 'correct';
		if (prog && prog.wrong > 0) return 'wrong';
		return 'unanswered';
	}));

	onMount(async () => {
		data = await loadQuestions();
		refreshQuestions();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
		});
		return unsub;
	});

	function refreshQuestions() {
		if (!data) return;
		const keys = getBookmarks();
		questions = keys.map(key => {
			const { section, id } = parseQuestionKey(key);
			return data!.questions.find(q => q.section === section && q.id === id);
		}).filter(Boolean) as Question[];
		if (currentIndex >= questions.length) currentIndex = Math.max(0, questions.length - 1);
		updateBookmark();
	}

	function updateBookmark() {
		if (currentQuestion) {
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	}

	function selectAnswer(letter: string) {
		if (isAnswered) return;
		if (hasMultipleAnswers) {
			const next = new Set(selectedAnswers);
			if (next.has(letter)) next.delete(letter); else next.add(letter);
			selectedAnswers = next;
		} else {
			selectedAnswers = new Set([letter]);
			checkAnswer();
		}
	}

	function checkAnswer() {
		if (!currentQuestion?.correct_answers) return;
		const correct = new Set(currentQuestion.correct_answers);
		isCorrect = correct.size === selectedAnswers.size && [...selectedAnswers].every(a => correct.has(a));
		isAnswered = true;
		recordAnswer(currentQuestion.section, currentQuestion.id, isCorrect);
	}

	function nextQuestion() {
		if (currentIndex < questions.length - 1) {
			currentIndex++;
		} else {
			goto(`${base}/practice`);
			return;
		}
		selectedAnswers = new Set();
		isAnswered = false;
		isCorrect = false;
		updateBookmark();
	}

	function handleToggleBookmark() {
		if (currentQuestion) {
			toggleBookmark(questionKey(currentQuestion));
			bookmarked = isBookmarked(questionKey(currentQuestion));
		}
	}

	function optionState(letter: string): 'idle' | 'selected' | 'correct' | 'wrong' | 'muted' {
		if (!isAnswered) {
			return selectedAnswers.has(letter) ? 'selected' : 'idle';
		}
		const correct = new Set(currentQuestion?.correct_answers || []);
		if (correct.has(letter)) return 'correct';
		if (selectedAnswers.has(letter)) return 'wrong';
		return 'muted';
	}
</script>

{#if questions.length === 0}
<div class="qpage">
	<Header
		title={lang === 'sr' ? 'Обележено' : 'Избранное'}
		onback={() => goto(`${base}/practice`)}
		onsettings={() => goto(`${base}/settings`)}
	/>
	<div class="empty">
		<Icon name="bookmark" size={32} color="var(--ink3)" />
		<p>{lang === 'sr' ? 'Нема обележених питања' : 'Нет избранных вопросов'}</p>
	</div>
</div>
{:else if currentQuestion}
<div class="qpage">
	<div class="q-header">
		<button class="q-header-btn" onclick={() => goto(`${base}/practice`)}>
			<Icon name="back" size={20} />
		</button>
		<div class="q-header-center">
			<div class="q-header-context">
				{lang === 'sr' ? 'ОБЕЛЕЖЕНО' : 'ИЗБРАННОЕ'}
			</div>
			<div class="q-header-counter">
				{String(currentIndex + 1).padStart(2, '0')}<span class="q-header-total"> / {questions.length}</span>
			</div>
		</div>
		<button class="q-header-btn" onclick={() => goto(`${base}/settings`)}>
			<Icon name="settings" size={19} stroke={1.5} />
		</button>
	</div>

	<QuestionPills
		current={currentIndex}
		states={pillStates}
		onclick={(i) => { currentIndex = i; selectedAnswers = new Set(); isAnswered = false; updateBookmark(); }}
	/>

	<div class="q-body">
		{#if currentQuestion.has_image && currentQuestion.image}
			<div class="q-media">
				<img src="{base}/images/{currentQuestion.image}" alt="" class="q-image" />
			</div>
		{/if}

		<div class="q-text">{qText(currentQuestion, lang)}</div>
		<div class="q-meta">
			{hasMultipleAnswers
				? (lang === 'sr' ? 'Изабери више одговора' : 'Выберите несколько ответов')
				: (lang === 'sr' ? 'Изабери један одговор' : 'Выберите один ответ')}
			· {currentQuestion.points} {lang === 'sr' ? 'поен' : 'балл'}
		</div>
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
			<button class="q-confirm-btn" onclick={checkAnswer}>
				{t('question.confirm', lang)} ({selectedAnswers.size})
			</button>
		{/if}

		<div class="q-footer">
			<button class="q-footer-icon" onclick={() => { updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' }); }}>
				<Icon name="language" size={19} stroke={1.6} />
			</button>
			<button
				class="q-footer-icon"
				class:q-footer-active={bookmarked}
				onclick={handleToggleBookmark}
			>
				<Icon name={bookmarked ? 'bookmark-fill' : 'bookmark'} size={19} stroke={1.6} />
			</button>
			<div class="q-footer-spacer"></div>
			{#if isAnswered}
				<button class="q-next-btn q-next-accent" onclick={nextQuestion}>
					{currentIndex < questions.length - 1
						? (lang === 'sr' ? 'Следеће' : 'Далее')
						: '✓'}
				</button>
			{/if}
		</div>
	</div>
</div>
{/if}

<style>
	.qpage {
		position: fixed; inset: 0;
		display: flex; flex-direction: column;
		background: var(--bg);
		padding-top: env(safe-area-inset-top);
		z-index: 10;
	}
	.empty {
		flex: 1; display: flex; flex-direction: column;
		align-items: center; justify-content: center; gap: 12px;
		color: var(--ink3); font-size: 14px;
	}
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
	.q-header-context {
		font-family: var(--font-mono); font-size: 9px;
		color: var(--ink3); letter-spacing: 1px;
		text-transform: uppercase; margin-bottom: 2px;
	}
	.q-header-counter {
		font-family: var(--font-mono); font-size: 13px;
		color: var(--ink); letter-spacing: 0.3px;
	}
	.q-header-total { color: var(--ink3); }
	.q-body { flex: 1; overflow: auto; padding: 16px 16px 8px; }
	.q-media { position: relative; margin-bottom: 10px; }
	.q-image { width: 100%; display: block; border-radius: 16px; }
	.q-text {
		font-size: 16px; font-weight: 500;
		letter-spacing: -0.2px; line-height: 1.45;
	}
	.q-meta {
		color: var(--ink3); margin-top: 6px;
		font-size: 12px; font-family: var(--font-mono);
		letter-spacing: 0.2px;
	}
	.q-answers {
		padding: 12px 14px 14px;
		padding-bottom: calc(14px + env(safe-area-inset-bottom));
		display: flex; flex-direction: column; gap: 8px;
		background: var(--answer-zone-bg); flex-shrink: 0;
		border-top: 0.5px solid var(--hairline);
	}
	.q-confirm-btn {
		height: 44px; border-radius: 14px;
		background: var(--ink); color: var(--bg);
		font-size: 15px; font-weight: 600;
		border: none; cursor: pointer;
	}
	.q-footer {
		display: flex; align-items: center; gap: 4px; margin-top: 6px;
	}
	.q-footer-icon {
		width: 44px; height: 44px; border-radius: 12px;
		background: transparent; border: none;
		color: var(--ink2); display: flex;
		align-items: center; justify-content: center; cursor: pointer;
	}
	.q-footer-active { background: var(--accent-wash); color: var(--accent); }
	.q-footer-spacer { flex: 1; }
	.q-next-btn {
		height: 44px; padding: 0 22px; border-radius: 14px;
		font-size: 15px; font-weight: 600; border: none; cursor: pointer;
	}
	.q-next-accent { background: var(--accent); color: var(--accent-ink); }
</style>
