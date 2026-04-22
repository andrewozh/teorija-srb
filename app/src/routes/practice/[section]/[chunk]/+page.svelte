<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks } from '$lib/data.js';
	import { getSettings, subscribe } from '$lib/store.js';
	import { sectionName } from '$lib/i18n.js';
	import type { Question, Lang } from '$lib/types.js';
	import QuestionCarousel from '$lib/components/QuestionCarousel.svelte';

	let sectionId = $derived($page.params.section ?? '');
	let chunkIndex = $derived(parseInt($page.params.chunk ?? '0', 10));

	let questions = $state<Question[]>([]);
	let lang = $state<Lang>(getSettings().lang);

	onMount(async () => {
		const data = await loadQuestions();
		const sectionQuestions = getQuestionsBySection(data, sectionId);
		const chunks = getChunks(sectionQuestions);
		const chunk = chunks[chunkIndex];
		if (chunk) {
			questions = chunk.questions;
		}

		const unsub = subscribe(() => {
			lang = getSettings().lang;
		});
		return unsub;
	});

	function handleBack() {
		goto(`${base}/practice/${sectionId}`);
	}

	function handleComplete() {
		goto(`${base}/practice/${sectionId}`);
	}
</script>

{#if questions.length > 0}
	<QuestionCarousel
		{questions}
		headerTitle={sectionName(sectionId, lang)}
		headerSub="{lang === 'sr' ? 'блок' : 'блок'} {String(chunkIndex + 1).padStart(2, '0')}"
		onBack={handleBack}
		onComplete={handleComplete}
	/>
{/if}
