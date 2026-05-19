<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection } from '$lib/data.js';
	import { getSectionCompletedCount, getTotalCompletedCount, getQuestionProgress, getMistakeStatus, subscribe, getSettings, getBookmarks } from '$lib/store.js';
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
	let bookmarkCount = $state(getBookmarks().length);
	let sectionOldestDays = $state<Record<string, number | null>>({});
	let sectionWrong = $state<Record<string, number>>({});
	let sectionRecovering = $state<Record<string, number>>({});

	function computeSectionOldestDays(sectionId: string, data: any): number | null {
		const qs = getQuestionsBySection(data, sectionId);
		let oldest: string | null = null;
		for (const q of qs) {
			const prog = getQuestionProgress(q.section, q.id);
			if (prog && prog.last) {
				if (!oldest || prog.last < oldest) oldest = prog.last;
			}
		}
		if (!oldest) return null;
		const [y, m, d] = oldest.split('-').map(Number);
		const then = new Date(y, m - 1, d).getTime();
		const now = new Date().setHours(0, 0, 0, 0);
		return Math.floor((now - then) / (1000 * 60 * 60 * 24));
	}

	let _data: any = null;

	function computeSectionStats(sectionId: string, data: any): { correct: number; wrong: number; recovering: number } {
		const qs = getQuestionsBySection(data, sectionId);
		let correct = 0, wrong = 0, recovering = 0;
		for (const q of qs) {
			const prog = getQuestionProgress(q.section, q.id);
			if (prog) {
				const m = getMistakeStatus(q.section, q.id);
				if (m === 'none' && prog.correct > 0) correct++;
				else if (m === 'recovering') recovering++;
				else if (m === 'wrong') wrong++;
			}
		}
		return { correct, wrong, recovering };
	}

	function recalcSections() {
		if (!_data) return;
		bookmarkCount = getBookmarks().length;
		let tc = 0;
		let tq = 0;
		for (const s of sections) {
			const qs = getQuestionsBySection(_data, s.id);
			sectionQuestionCounts[s.id] = qs.length;
			const stats = computeSectionStats(s.id, _data);
			sectionCompleted[s.id] = stats.correct;
			sectionWrong[s.id] = stats.wrong;
			sectionRecovering[s.id] = stats.recovering;
			sectionOldestDays[s.id] = computeSectionOldestDays(s.id, _data);
			tc += stats.correct;
			tq += qs.length;
		}
		totalCompleted = tc;
		totalQuestions = tq;
	}

	onMount(async () => {
		_data = await loadQuestions();
		sections = getSections(_data);
		for (const s of sections) {
			const qs = getQuestionsBySection(_data, s.id);
			sectionQuestionCounts[s.id] = qs.length;
		}
		totalQuestions = _data.questions.filter((q: any) => !q.is_removed).length;
		recalcSections();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
			recalcSections();
		});
		return unsub;
	});
</script>

<div class="page">
	<Header
		title={lang === 'sr' ? 'Сва питања' : 'Все вопросы'}
		home onback={() => goto(`${base}/`)}
		onsettings={() => goto(`${base}/settings`)}
	/>

	<div class="scroll-area">
		<div class="list-meta">
			{sections.length} {lang === 'sr' ? 'области' : 'разделов'} ·
			<span class="mono-ink">{totalCompleted}/{totalQuestions}</span>
			{lang === 'sr' ? 'завршено' : 'завершено'}
		</div>

		{#if bookmarkCount > 0}
			<a href="{base}/practice/bookmarks" class="section-card bookmark-card">
				<div class="section-top">
					<div class="section-num bookmark-icon">
						<Icon name="bookmark-fill" size={14} color="var(--accent)" />
					</div>
					<div class="section-body">
						<div class="section-title">{lang === 'sr' ? 'Обележено' : 'Избранное'}</div>
					</div>
					<div class="section-count">{bookmarkCount}</div>
				</div>
			</a>
		{/if}

		{#each sections as section, i}
			{@const total = sectionQuestionCounts[section.id] || section.questions}
			{@const done = sectionCompleted[section.id] || 0}
			<a href="{base}/practice/{section.id}" class="section-card">
				<div class="section-top">
					<div class="section-num">{i + 1}</div>
					<div class="section-body">
						<div class="section-title">{sectionName(section.id, lang)}</div>
					</div>
					{#if sectionOldestDays[section.id] !== null && sectionOldestDays[section.id] !== undefined}
						<span class="section-age">{sectionOldestDays[section.id]}д</span>
					{/if}
					<div class="section-count">{done}/{total}</div>
				</div>
				<ProgressBar value={done} total={total} wrong={sectionWrong[section.id] || 0} recovering={sectionRecovering[section.id] || 0} />
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
	.bookmark-card {
		border-color: var(--accent-wash);
		margin-bottom: 16px;
	}
	.bookmark-card .section-top { margin-bottom: 0; }
	.bookmark-icon {
		background: var(--accent-wash) !important;
	}
	.section-age {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink4);
		flex-shrink: 0;
	}
	.section-count {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		letter-spacing: 0.3px;
		flex-shrink: 0;
	}

	/* Desktop */
	@media (min-width: 1024px) {
		.scroll-area { padding: 24px 40px 40px; max-width: 720px; }
		.section-card { padding: 16px 20px; }
	}
</style>
