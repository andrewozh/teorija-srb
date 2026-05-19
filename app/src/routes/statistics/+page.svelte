<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection } from '$lib/data.js';
	import {
		getTotalCompletedCount,
		getSectionCompletedCount,
		getExams,
		getMistakeQuestionKeys,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { SectionMeta, ExamResult, Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';

	let sections = $state<SectionMeta[]>([]);
	let sectionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});
	let totalCompleted = $state(0);
	let totalActive = $state(0);
	let exams = $state<ExamResult[]>([]);
	let mistakeCount = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	onMount(async () => {
		const data = await loadQuestions();
		sections = getSections(data);
		totalActive = data.questions.filter((q) => !q.is_removed).length;
		for (const s of sections) {
			sectionCounts[s.id] = getQuestionsBySection(data, s.id).length;
		}
		refreshStats();
		const unsub = subscribe(() => {
			lang = getSettings().lang;
			refreshStats();
		});
		return unsub;
	});

	function refreshStats() {
		totalCompleted = getTotalCompletedCount();
		mistakeCount = getMistakeQuestionKeys().length;
		exams = [...getExams()].reverse();
		for (const s of sections) {
			sectionCompleted[s.id] = getSectionCompletedCount(s.id);
		}
	}

	let overallPercent = $derived(totalActive > 0 ? Math.round((totalCompleted / totalActive) * 100) : 0);

	// Ring calculations
	const ringSize = 168;
	const ringStroke = 10;
	let ringR = $derived((ringSize - ringStroke) / 2);
	let ringCirc = $derived(2 * Math.PI * ringR);
	let ringOffset = $derived(ringCirc * (1 - (totalActive > 0 ? totalCompleted / totalActive : 0)));

	function formatDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('sr-Latn-RS', { day: 'numeric', month: 'short' });
	}

	let passedExams = $derived(exams.filter(e => e.passed).length);
	let failedExams = $derived(exams.filter(e => !e.passed).length);
</script>

<div class="page">
	<Header
		title={t('stats.title', lang)}
		home onback={() => goto(`${base}/`)}
		onsettings={() => goto(`${base}/settings`)}
	/>

	<div class="scroll-area">
		<!-- Ring + stats -->
		<div class="ring-section">
			<div class="ring-wrap" style:width="{ringSize}px" style:height="{ringSize}px">
				<svg width={ringSize} height={ringSize} style="transform: rotate(-90deg)">
					<circle cx={ringSize/2} cy={ringSize/2} r={ringR} fill="none" stroke="var(--neutral)" stroke-width={ringStroke} />
					<circle cx={ringSize/2} cy={ringSize/2} r={ringR} fill="none" stroke="var(--accent)" stroke-width={ringStroke}
						stroke-dasharray={ringCirc} stroke-dashoffset={ringOffset} stroke-linecap="round" />
				</svg>
				<div class="ring-center">
					<div class="ring-pct">
						{overallPercent}<span class="ring-pct-sign">%</span>
					</div>
					<div class="ring-label">{lang === 'sr' ? 'спремност' : 'готовность'}</div>
				</div>
			</div>

			<div class="ring-stats">
				<div class="ring-stat">
					<div class="ring-stat-row">
						<div class="stat-dot" style:background="var(--accent)"></div>
						<div class="stat-num">{totalCompleted.toLocaleString()}</div>
					</div>
					<div class="stat-label">{lang === 'sr' ? 'Завршено' : 'Завершено'}</div>
				</div>
				<div class="ring-stat">
					<div class="ring-stat-row">
						<div class="stat-dot" style:background="var(--ink3)"></div>
						<div class="stat-num">{(totalActive - totalCompleted).toLocaleString()}</div>
					</div>
					<div class="stat-label">{lang === 'sr' ? 'Преостало' : 'Осталось'}</div>
				</div>
				<div class="ring-stat">
					<div class="ring-stat-row">
						<div class="stat-dot" style:background="var(--wrong)"></div>
						<div class="stat-num">{mistakeCount}</div>
					</div>
					<div class="stat-label">{lang === 'sr' ? 'Грешке' : 'Ошибки'}</div>
				</div>
			</div>
		</div>

		<!-- Per-section -->
		<div class="section-label">{lang === 'sr' ? 'По областима' : 'По разделам'}</div>
		<div class="sections-card">
			{#each sections as section, i}
				{@const total = sectionCounts[section.id] || 1}
				{@const done = sectionCompleted[section.id] || 0}
				{@const pct = Math.round((done / total) * 100)}
				<div class="section-row" class:section-row-last={i === sections.length - 1}>
					<div class="section-idx">{String(i + 1).padStart(2, '0')}</div>
					<div class="section-name">{sectionName(section.id, lang)}</div>
					<div class="section-bar">
						<ProgressBar value={done} total={total} height={2} />
					</div>
					<div class="section-pct" class:section-pct-dim={pct === 0}>{pct}%</div>
				</div>
			{/each}
		</div>

		<!-- Exam history -->
		<div class="exam-history-header">
			<div class="section-label">{t('stats.exams', lang)}</div>
			{#if exams.length > 0}
				<div class="exam-ratio">
					<span style="color:var(--correct)">{passedExams}</span>
					<span style="color:var(--ink4)"> / </span>
					<span style="color:var(--wrong)">{failedExams}</span>
				</div>
			{/if}
		</div>

		{#if exams.length === 0}
			<div class="no-exams">{t('stats.no_exams', lang)}</div>
		{:else}
			<!-- Sparkline -->
			<div class="sparkline-card">
				<div class="sparkline-bars">
					{#each exams.slice().reverse().slice(-5) as h, i}
						{@const hPct = (h.score / h.total) * 100}
						<div class="sparkline-col">
							<div
								class="sparkline-bar"
								style:height="{hPct}%"
								style:background={h.passed ? 'var(--correct)' : 'var(--wrong)'}
								style:opacity={i === exams.length - 1 ? '1' : '0.5'}
							></div>
						</div>
					{/each}
				</div>
			</div>

			{#each exams.slice(0, 3) as h, i}
				<div class="exam-item">
					<div class="exam-badge" style:background={h.passed ? 'var(--correct-wash)' : 'var(--wrong-wash)'} style:color={h.passed ? 'var(--correct)' : 'var(--wrong)'}>
						<Icon name={h.passed ? 'check' : 'x'} size={14} stroke={2.5} />
					</div>
					<div class="exam-info">
						<div class="exam-score">
							{h.score}<span class="exam-score-total">/{h.total}</span>
						</div>
						<div class="exam-date">
							{formatDate(h.date)} · {h.total - h.score} {t('exam.errors', lang)}
						</div>
					</div>
					<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 18px 16px 24px; }

	/* Ring */
	.ring-section {
		display: flex; align-items: center; gap: 20px;
		padding: 8px 4px 22px;
	}
	.ring-wrap {
		position: relative; flex-shrink: 0;
	}
	.ring-center {
		position: absolute; inset: 0;
		display: flex; flex-direction: column;
		align-items: center; justify-content: center;
	}
	.ring-pct {
		font-family: var(--font-mono); font-size: 38px;
		color: var(--ink); letter-spacing: -0.8px; line-height: 1;
	}
	.ring-pct-sign { font-size: 22px; color: var(--ink3); }
	.ring-label {
		font-family: var(--font-mono); font-size: 10px;
		color: var(--ink3); letter-spacing: 1px;
		text-transform: uppercase; margin-top: 4px;
	}

	.ring-stats { flex: 1; display: flex; flex-direction: column; gap: 14px; }
	.ring-stat-row { display: flex; align-items: baseline; gap: 6px; }
	.stat-dot {
		width: 5px; height: 5px; border-radius: 3px;
		align-self: center;
	}
	.stat-num {
		font-family: var(--font-mono); font-size: 18px;
		color: var(--ink); letter-spacing: -0.3px;
	}
	.stat-label {
		font-size: 11px; color: var(--ink3);
		margin-left: 11px; margin-top: 1px;
	}

	/* Sections */
	.section-label {
		font-family: var(--font-mono); font-size: 10px;
		color: var(--ink3); letter-spacing: 1px;
		text-transform: uppercase; padding: 4px 4px 12px;
	}
	.sections-card {
		background: var(--surface); border-radius: 18px;
		padding: 4px 0; border: 0.5px solid var(--hairline);
		margin-bottom: 22px;
	}
	.section-row {
		display: flex; align-items: center; gap: 12px;
		padding: 10px 16px;
		border-bottom: 0.5px solid var(--hairline);
	}
	.section-row-last { border-bottom: none; }
	.section-idx {
		width: 20px; font-family: var(--font-mono);
		font-size: 10px; color: var(--ink3); letter-spacing: 0.3px;
	}
	.section-name {
		flex: 1; font-size: 13px; letter-spacing: -0.1px;
		color: var(--ink); overflow: hidden;
		text-overflow: ellipsis; white-space: nowrap;
	}
	.section-bar { width: 72px; }
	.section-pct {
		font-family: var(--font-mono); font-size: 11px;
		color: var(--ink); width: 32px; text-align: right;
		letter-spacing: 0.2px;
	}
	.section-pct-dim { color: var(--ink4); }

	/* Exam history */
	.exam-history-header {
		display: flex; justify-content: space-between;
		align-items: baseline; padding: 4px 4px 12px;
	}
	.exam-history-header .section-label { padding: 0; }
	.exam-ratio {
		font-family: var(--font-mono); font-size: 10px;
		color: var(--ink3); letter-spacing: 0.3px;
	}

	.no-exams {
		text-align: center; padding: 24px;
		font-size: 13px; color: var(--ink3);
	}

	.sparkline-card {
		background: var(--surface); border-radius: 18px;
		padding: 14px 16px 10px;
		border: 0.5px solid var(--hairline);
		margin-bottom: 10px;
	}
	.sparkline-bars {
		display: flex; align-items: flex-end; gap: 6px;
		height: 56px; margin-bottom: 8px;
	}
	.sparkline-col {
		flex: 1; height: 100%;
		display: flex; flex-direction: column; justify-content: flex-end;
	}
	.sparkline-bar { border-radius: 3px; }

	.exam-item {
		background: var(--surface); border-radius: 14px;
		padding: 12px 14px; margin-bottom: 5px;
		display: flex; align-items: center; gap: 12px;
		border: 0.5px solid var(--hairline);
	}
	.exam-badge {
		width: 28px; height: 28px; border-radius: 8px;
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0;
	}
	.exam-info { flex: 1; }
	.exam-score {
		font-family: var(--font-mono); font-size: 14px;
		color: var(--ink); letter-spacing: 0.2px;
	}
	.exam-score-total { color: var(--ink3); }
	.exam-date { font-size: 11px; color: var(--ink3); margin-top: 2px; }

	/* Desktop */
	@media (min-width: 1024px) {
		.scroll-area { padding: 28px 40px 40px; max-width: 960px; }
	}
</style>
