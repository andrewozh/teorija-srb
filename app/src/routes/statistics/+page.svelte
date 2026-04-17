<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection, sectionIcon, sectionColor } from '$lib/data.js';
	import {
		getTotalCompletedCount,
		getSectionCompletedCount,
		getExams,
		getMistakeQuestionKeys,
		subscribe
	} from '$lib/store.js';
	import type { SectionMeta, ExamResult } from '$lib/types.js';

	let sections = $state<SectionMeta[]>([]);
	let sectionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});
	let totalCompleted = $state(0);
	let totalActive = $state(0);
	let exams = $state<ExamResult[]>([]);
	let mistakeCount = $state(0);

	onMount(async () => {
		const data = await loadQuestions();
		sections = getSections(data);
		totalActive = data.questions.filter((q) => !q.is_removed).length;

		for (const s of sections) {
			sectionCounts[s.id] = getQuestionsBySection(data, s.id).length;
		}

		refreshStats();

		const unsub = subscribe(() => refreshStats());
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

	function formatDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('sr-Latn-RS', {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<div class="stats-page">
	<header class="page-header">
		<a href="/" class="back-btn" aria-label="Назад">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 18l-6-6 6-6"/>
			</svg>
		</a>
		<h1>Статистика</h1>
		<div style="width: 40px"></div>
	</header>

	<main class="stats-content">
		<!-- Overall progress -->
		<div class="overall-card">
			<div class="overall-ring">
				<svg width="100" height="100" viewBox="0 0 100 100">
					<circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" stroke-width="8"/>
					<circle
						cx="50" cy="50" r="40"
						fill="none"
						stroke="var(--primary)"
						stroke-width="8"
						stroke-dasharray="{(overallPercent / 100) * 2 * Math.PI * 40} {2 * Math.PI * 40}"
						stroke-linecap="round"
						transform="rotate(-90 50 50)"
					/>
					<text x="50" y="46" text-anchor="middle" font-size="20" font-weight="700" fill="var(--text)">
						{overallPercent}%
					</text>
					<text x="50" y="62" text-anchor="middle" font-size="10" fill="var(--text-secondary)">
						завршено
					</text>
				</svg>
			</div>
			<div class="overall-stats">
				<div class="stat-item">
					<span class="stat-value">{totalCompleted}</span>
					<span class="stat-label">Урађено</span>
				</div>
				<div class="stat-item">
					<span class="stat-value">{totalActive - totalCompleted}</span>
					<span class="stat-label">Преостало</span>
				</div>
				<div class="stat-item">
					<span class="stat-value">{mistakeCount}</span>
					<span class="stat-label">Грешке</span>
				</div>
			</div>
		</div>

		<!-- Per-section breakdown -->
		<div class="section-stats">
			<h2>По областима</h2>
			{#each sections as section}
				{@const total = sectionCounts[section.id] || 1}
				{@const done = sectionCompleted[section.id] || 0}
				{@const pct = Math.round((done / total) * 100)}
				<div class="section-row">
					<div class="section-label">
						<span>{sectionIcon(section.id)}</span>
						<span class="section-name">{section.name}</span>
					</div>
					<div class="section-bar-row">
						<div class="section-bar">
							<div
								class="section-bar-fill"
								style="width: {pct}%; background: {sectionColor(section.id)}"
							></div>
						</div>
						<span class="section-pct">{done}/{total}</span>
					</div>
				</div>
			{/each}
		</div>

		<!-- Exam history -->
		<div class="exam-history">
			<h2>Историја испита</h2>
			{#if exams.length === 0}
				<p class="no-exams">Нема покушаја испита.</p>
			{:else}
				{#each exams as exam}
					<div class="exam-row" class:passed={exam.passed} class:failed={!exam.passed}>
						<div class="exam-info">
							<span class="exam-badge">{exam.passed ? '✓' : '✗'}</span>
							<div>
								<div class="exam-score">{exam.score} / {exam.total}</div>
								<div class="exam-date">{formatDate(exam.date)}</div>
							</div>
						</div>
						<span class="exam-errors">{exam.total - exam.score} грешака</span>
					</div>
				{/each}
			{/if}
		</div>
	</main>
</div>

<style>
	.stats-page {
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

	.page-header h1 {
		font-size: 1.1rem;
		font-weight: 600;
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

	.stats-content {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	/* Overall */
	.overall-card {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.overall-stats {
		display: flex;
		gap: 2rem;
	}

	.stat-item {
		text-align: center;
	}

	.stat-value {
		display: block;
		font-size: 1.3rem;
		font-weight: 700;
	}

	.stat-label {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	/* Section stats */
	.section-stats {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 1rem;
	}

	.section-stats h2 {
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
	}

	.section-row {
		margin-bottom: 0.75rem;
	}

	.section-row:last-child {
		margin-bottom: 0;
	}

	.section-label {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-bottom: 0.25rem;
	}

	.section-name {
		font-size: 0.8rem;
		color: var(--text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.section-bar-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.section-bar {
		flex: 1;
		height: 6px;
		background: var(--bg-secondary);
		border-radius: 3px;
		overflow: hidden;
	}

	.section-bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.section-pct {
		font-size: 0.7rem;
		color: var(--text-muted);
		flex-shrink: 0;
		min-width: 4rem;
		text-align: right;
	}

	/* Exam history */
	.exam-history {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 1rem;
	}

	.exam-history h2 {
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
	}

	.no-exams {
		color: var(--text-muted);
		font-size: 0.85rem;
		text-align: center;
		padding: 1rem;
	}

	.exam-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.6rem 0;
		border-bottom: 1px solid var(--border);
	}

	.exam-row:last-child {
		border-bottom: none;
	}

	.exam-info {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.exam-badge {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 0.8rem;
		flex-shrink: 0;
	}

	.exam-row.passed .exam-badge {
		background: var(--success-light);
		color: var(--success);
	}

	.exam-row.failed .exam-badge {
		background: var(--danger-light);
		color: var(--danger);
	}

	.exam-score {
		font-size: 0.9rem;
		font-weight: 600;
	}

	.exam-date {
		font-size: 0.7rem;
		color: var(--text-muted);
	}

	.exam-errors {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}
</style>
