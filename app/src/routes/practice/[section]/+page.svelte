<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks } from '$lib/data.js';
	import { getQuestionProgress, getSectionCompletedCount, subscribe, getSettings } from '$lib/store.js';
	import { sectionName } from '$lib/i18n.js';
	import type { Chunk, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';

	let sectionId = $derived($page.params.section);
	let chunks = $state<Chunk[]>([]);
	let chunkStats = $state<Array<{ total: number; correct: number; wrong: number }>>([]);
	let totalQuestions = $state(0);
	let totalCorrect = $state(0);
	let totalWrong = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	function computeChunkStats(chunks: Chunk[]): Array<{ total: number; correct: number; wrong: number }> {
		return chunks.map((chunk) => {
			let correct = 0;
			let wrong = 0;
			for (const q of chunk.questions) {
				const prog = getQuestionProgress(q.section, q.id);
				if (prog) {
					if (prog.correct > 0) correct++;
					else if (prog.wrong > 0) wrong++;
				}
			}
			return { total: chunk.questions.length, correct, wrong };
		});
	}

	onMount(async () => {
		const data = await loadQuestions();
		const questions = getQuestionsBySection(data, sectionId);
		chunks = getChunks(questions);
		totalQuestions = questions.length;
		chunkStats = computeChunkStats(chunks);
		recalcTotals();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
			chunkStats = computeChunkStats(chunks);
			recalcTotals();
		});
		return unsub;
	});

	function recalcTotals() {
		totalCorrect = chunkStats.reduce((s, c) => s + c.correct, 0);
		totalWrong = chunkStats.reduce((s, c) => s + c.wrong, 0);
	}

	let pct = $derived(totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0);
</script>

<div class="page">
	<Header
		title={sectionName(sectionId, lang)}
		onback={() => history.back()}
		onsettings={() => goto(`${base}/settings`)}
	/>

	<div class="scroll-area">
		<!-- Section header -->
		<div class="section-header-area">
			<div class="section-meta">
				{lang === 'sr' ? 'Област' : 'Раздел'} · {totalQuestions} {lang === 'sr' ? 'питања' : 'вопросов'}
			</div>
			<div class="section-big-title">{sectionName(sectionId, lang)}</div>
			<ProgressBar value={totalCorrect} total={totalQuestions} height={4} />
			<div class="section-stats">
				<span>
					<span class="correct-text">{totalCorrect}</span> {lang === 'sr' ? 'тачно' : 'верно'} ·
					<span class="wrong-text">{totalWrong}</span> {lang === 'sr' ? 'погрешно' : 'неверно'}
				</span>
				<span>{pct}%</span>
			</div>
		</div>

		<div class="blocks-label">
			{chunks.length} {lang === 'sr' ? 'блокова' : 'блоков'}
		</div>

		{#each chunks as chunk, i}
			{@const stat = chunkStats[i] || { total: 0, correct: 0, wrong: 0 }}
			{@const isDone = stat.correct === stat.total}
			{@const isStarted = stat.correct > 0 || stat.wrong > 0}
			<a
				href="{base}/practice/{sectionId}/{chunk.index}"
				class="block-card"
				style:opacity={!isStarted ? '0.5' : '1'}
			>
				<div class="block-num" class:block-done={isDone}>
					{#if isDone}
						<Icon name="check" size={13} stroke={2.5} />
					{:else}
						{i + 1}
					{/if}
				</div>
				<div class="block-name">
					{lang === 'sr' ? 'Блок' : 'Блок'} {String(i + 1).padStart(2, '0')}
				</div>
				<div class="block-bar">
					<ProgressBar value={stat.correct} total={stat.total} height={2} />
				</div>
				<div class="block-count">{stat.correct}/{stat.total}</div>
			</a>
		{/each}
	</div>
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 16px 14px 20px; }

	.section-header-area { padding: 4px 4px 16px; }
	.section-meta {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		margin-bottom: 6px;
	}
	.section-big-title {
		font-size: 24px;
		font-weight: 500;
		letter-spacing: -0.4px;
		margin-bottom: 14px;
	}
	.section-stats {
		display: flex;
		justify-content: space-between;
		margin-top: 10px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		letter-spacing: 0.3px;
	}
	.correct-text { color: var(--correct); }
	.wrong-text { color: var(--wrong); }

	.blocks-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		padding: 10px 4px;
	}

	.block-card {
		display: flex;
		align-items: center;
		gap: 12px;
		background: var(--surface);
		border-radius: 14px;
		padding: 12px 14px;
		margin-bottom: 5px;
		border: 0.5px solid var(--hairline);
	}
	.block-num {
		width: 24px; height: 24px; border-radius: 6px;
		background: var(--surface2); color: var(--ink3);
		display: flex; align-items: center; justify-content: center;
		font-family: var(--font-mono); font-size: 11px;
		flex-shrink: 0;
	}
	.block-done {
		background: var(--correct-wash);
		color: var(--correct);
	}
	.block-name {
		flex: 1;
		font-size: 13px;
		letter-spacing: -0.1px;
	}
	.block-bar { width: 80px; }
	.block-count {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		width: 34px;
		text-align: right;
	}
</style>
