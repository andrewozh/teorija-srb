<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks, getSections, sectionColor } from '$lib/data.js';
	import { getQuestionProgress, subscribe, getSettings } from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { sectionName } from '$lib/i18n.js';
	import type { Question, Chunk, SectionMeta, Lang } from '$lib/types.js';

	let sectionId = $derived($page.params.section);
	let chunks = $state<Chunk[]>([]);
	let chunkStats = $state<Array<{ total: number; correct: number; wrong: number }>>([]);
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		setPageTitle(sectionName(sectionId, lang));
	});

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
		chunkStats = computeChunkStats(chunks);

		const unsub = subscribe(() => {
			lang = getSettings().lang;
			chunkStats = computeChunkStats(chunks);
		});
		return unsub;
	});

	function chunkStatus(stat: { total: number; correct: number; wrong: number }): string {
		if (stat.correct === stat.total) return 'complete';
		if (stat.correct > 0 || stat.wrong > 0) return 'in-progress';
		return 'not-started';
	}

	function borderClass(status: string): string {
		if (status === 'complete') return 'border-success';
		if (status === 'in-progress') return 'border-warning';
		return '';
	}
</script>

<div class="pb-4">
	<!-- Chunk grid -->
	<div class="row row-cols-2 g-3 px-3 pt-3">
		{#each chunks as chunk, i}
			{@const stat = chunkStats[i] || { total: 0, correct: 0, wrong: 0 }}
			{@const status = chunkStatus(stat)}
			<div class="col">
				<a
					href="{base}/practice/{sectionId}/{chunk.index}"
					class="card text-decoration-none border-start border-4 shadow-sm h-100 {borderClass(status)}"
				>
					<div class="card-body p-3">
						<div class="fw-bold mb-2">{chunk.start + 1}–{chunk.end}</div>
						<div class="d-flex align-items-center gap-2">
							<div class="progress flex-grow-1" style="height:4px;">
								<div class="progress-bar bg-success" style="width:{(stat.correct / stat.total) * 100}%"></div>
								<div class="progress-bar bg-danger" style="width:{(stat.wrong / stat.total) * 100}%"></div>
							</div>
							<small class="text-body-secondary flex-shrink-0">{stat.correct}/{stat.total}</small>
						</div>
					</div>
				</a>
			</div>
		{/each}
	</div>
</div>
