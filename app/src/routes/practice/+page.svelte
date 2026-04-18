<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection } from '$lib/data.js';
	import { getSectionCompletedCount, getTotalCompletedCount, subscribe, getSettings } from '$lib/store.js';
	import { sectionName } from '$lib/i18n.js';
	import type { SectionMeta, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';

	let sections = $state<SectionMeta[]>([]);
	let sectionQuestionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});
	let totalCompleted = $state(0);
	let totalQuestions = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	onMount(async () => {
		const data = await loadQuestions();
		sections = getSections(data);
		for (const s of sections) {
			const qs = getQuestionsBySection(data, s.id);
			sectionQuestionCounts[s.id] = qs.length;
			sectionCompleted[s.id] = getSectionCompletedCount(s.id);
		}
		totalQuestions = data.questions.filter(q => !q.is_removed).length;
		totalCompleted = getTotalCompletedCount();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
			totalCompleted = getTotalCompletedCount();
			for (const s of sections) {
				sectionCompleted[s.id] = getSectionCompletedCount(s.id);
			}
		});
		return unsub;
	});
</script>

<div class="page">
	<Header
		title={lang === 'sr' ? 'Учење' : 'Обучение'}
		onback={() => history.back()}
		onsettings={() => goto(`${base}/settings`)}
	/>

	<div class="scroll-area">
		<div class="list-meta">
			{sections.length} {lang === 'sr' ? 'области' : 'разделов'} ·
			<span class="mono-ink">{totalCompleted}/{totalQuestions}</span>
			{lang === 'sr' ? 'завршено' : 'завершено'}
		</div>

		{#each sections as section, i}
			{@const total = sectionQuestionCounts[section.id] || section.questions}
			{@const done = sectionCompleted[section.id] || 0}
			<a href="{base}/practice/{section.id}" class="section-card">
				<div class="section-top">
					<div class="section-num">{i + 1}</div>
					<div class="section-body">
						<div class="section-title">{sectionName(section.id, lang)}</div>
					</div>
					<div class="section-count">{done}/{total}</div>
				</div>
				<ProgressBar value={done} total={total} />
			</a>
		{/each}
	</div>
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 12px 14px 20px; }

	.list-meta {
		padding: 8px 6px 16px;
		font-size: 13px;
		color: var(--ink3);
		line-height: 1.5;
	}
	.mono-ink {
		color: var(--ink);
		font-family: var(--font-mono);
	}

	.section-card {
		display: block;
		background: var(--surface);
		border-radius: 16px;
		padding: 14px 16px;
		margin-bottom: 6px;
		border: 0.5px solid var(--hairline);
	}
	.section-top {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 10px;
	}
	.section-num {
		width: 28px; height: 28px; border-radius: 8px;
		background: var(--surface2); color: var(--ink3);
		display: flex; align-items: center; justify-content: center;
		font-family: var(--font-mono); font-size: 12px; font-weight: 500;
		flex-shrink: 0;
	}
	.section-body { flex: 1; min-width: 0; }
	.section-title {
		font-size: 14px; font-weight: 500;
		letter-spacing: -0.1px; line-height: 1.3;
	}
	.section-count {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		letter-spacing: 0.3px;
		flex-shrink: 0;
	}
</style>
