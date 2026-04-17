<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks, getSections, sectionColor } from '$lib/data.js';
	import { getQuestionProgress, subscribe } from '$lib/store.js';
	import type { Question, Chunk, SectionMeta } from '$lib/types.js';

	let sectionId = $derived($page.params.section);
	let sectionName = $state('');
	let chunks = $state<Chunk[]>([]);
	let chunkStats = $state<Array<{ total: number; correct: number; wrong: number }>>([]);

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
		const sections = getSections(data);
		const meta = sections.find((s) => s.id === sectionId);
		sectionName = meta?.name || sectionId;

		const questions = getQuestionsBySection(data, sectionId);
		chunks = getChunks(questions);
		chunkStats = computeChunkStats(chunks);

		const unsub = subscribe(() => {
			chunkStats = computeChunkStats(chunks);
		});
		return unsub;
	});

	function chunkStatus(stat: { total: number; correct: number; wrong: number }): string {
		if (stat.correct === stat.total) return 'complete';
		if (stat.correct > 0 || stat.wrong > 0) return 'in-progress';
		return 'not-started';
	}
</script>

<div class="chunks-page">
	<header class="page-header">
		<a href="/practice" class="back-btn" aria-label="Назад">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 18l-6-6 6-6"/>
			</svg>
		</a>
		<h1 class="header-title">{sectionName}</h1>
		<div style="width: 40px"></div>
	</header>

	<main class="chunk-grid">
		{#each chunks as chunk, i}
			{@const stat = chunkStats[i] || { total: 0, correct: 0, wrong: 0 }}
			{@const status = chunkStatus(stat)}
			<a
				href="/practice/{sectionId}/{chunk.index}"
				class="chunk-card {status}"
			>
				<div class="chunk-number">
					{chunk.start + 1}–{chunk.end}
				</div>
				<div class="chunk-progress">
					<div class="chunk-bar">
						<div
							class="chunk-bar-fill correct"
							style="width: {(stat.correct / stat.total) * 100}%"
						></div>
						<div
							class="chunk-bar-fill wrong"
							style="width: {(stat.wrong / stat.total) * 100}%"
						></div>
					</div>
					<span class="chunk-count">{stat.correct}/{stat.total}</span>
				</div>
			</a>
		{/each}
	</main>
</div>

<style>
	.chunks-page {
		padding-bottom: 2rem;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		background: var(--card);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.header-title {
		font-size: 0.95rem;
		font-weight: 600;
		text-align: center;
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding: 0 0.5rem;
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

	.chunk-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
		padding: 1rem;
	}

	.chunk-card {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 1rem;
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		text-decoration: none;
		color: var(--text);
		transition: transform 0.15s;
		border-left: 4px solid var(--border);
	}

	.chunk-card:active {
		transform: scale(0.97);
	}

	.chunk-card.in-progress {
		border-left-color: var(--warning);
	}

	.chunk-card.complete {
		border-left-color: var(--success);
	}

	.chunk-number {
		font-size: 1rem;
		font-weight: 700;
	}

	.chunk-progress {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.chunk-bar {
		flex: 1;
		height: 4px;
		background: var(--bg-secondary);
		border-radius: 2px;
		overflow: hidden;
		display: flex;
	}

	.chunk-bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.chunk-bar-fill.correct {
		background: var(--success);
	}

	.chunk-bar-fill.wrong {
		background: var(--danger);
	}

	.chunk-count {
		font-size: 0.7rem;
		color: var(--text-secondary);
		flex-shrink: 0;
	}
</style>
