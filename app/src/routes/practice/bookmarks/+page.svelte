<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, parseQuestionKey } from '$lib/data.js';
	import { getBookmarks, subscribe, getSettings } from '$lib/store.js';
	import type { Question, QuestionsData, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionCarousel from '$lib/components/QuestionCarousel.svelte';

	let data = $state<QuestionsData | null>(null);
	let questions = $state<Question[]>([]);
	let lang = $state<Lang>(getSettings().lang);

	onMount(async () => {
		data = await loadQuestions();
		refreshQuestions();
		const unsub = subscribe(() => {
			lang = getSettings().lang;
			refreshQuestions();
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
	}
</script>

{#if questions.length === 0}
<div class="page">
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
{:else}
<QuestionCarousel
	{questions}
	headerTitle={lang === 'sr' ? 'ОБЕЛЕЖЕНО' : 'ИЗБРАННОЕ'}
	onBack={() => goto(`${base}/practice`)}
	onComplete={() => goto(`${base}/practice`)}
/>
{/if}

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.empty {
		flex: 1; display: flex; flex-direction: column;
		align-items: center; justify-content: center; gap: 12px;
		color: var(--ink3); font-size: 14px;
	}
</style>
