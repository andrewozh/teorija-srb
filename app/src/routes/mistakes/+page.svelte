<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey, qText } from '$lib/data.js';
	import {
		getMistakeQuestionKeys,
		getMistakeStatus,
		getQuestionProgress,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { Question, QuestionsData, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import QuestionCarousel from '$lib/components/QuestionCarousel.svelte';

	let data = $state<QuestionsData | null>(null);
	let mistakeQuestions = $state<Question[]>([]);
	let practicing = $state(false);
	let lang = $state<Lang>(getSettings().lang);

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
		const keys = getMistakeQuestionKeys();
		mistakeQuestions = keys
			.map((key) => {
				const { section, id } = parseQuestionKey(key);
				return data!.questions.find((q) => q.section === section && q.id === id);
			})
			.filter((q): q is Question => !!q);
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
	{#if practicing && mistakeQuestions.length > 0}
		<QuestionCarousel
			questions={mistakeQuestions}
			headerTitle={lang === 'sr' ? 'ГРЕШКЕ' : 'ОШИБКИ'}
			showFlag={false}
			onBack={() => { practicing = false; refreshMistakes(); }}
			onComplete={() => { practicing = false; refreshMistakes(); }}
		/>
	{:else}
		<Header
			title={t('mistakes.title', lang)}
			home onback={() => goto(`${base}/`)}
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
					<button class="practice-btn" onclick={() => { practicing = true; }}>
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
							{@const mStatus = getMistakeStatus(q.section, q.id)}
							<div class="mistake-item" class:mistake-recovering={mStatus === "recovering"}>
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
	.mistake-item.mistake-recovering {
		border-left-color: var(--recovering);
	}
	.mistake-text { font-size: 13px; line-height: 1.4; margin-bottom: 4px; }
	.mistake-stats { display: flex; gap: 12px; }
	.stat-correct { font-size: 12px; font-weight: 600; color: var(--correct); }
	.stat-wrong { font-size: 12px; font-weight: 600; color: var(--wrong); }

	/* Desktop */
	@media (min-width: 1024px) {
		.scroll-area { padding: 24px 40px 40px; max-width: 720px; }
	}
</style>
