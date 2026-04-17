<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection, getChunks, sectionIcon, sectionColor } from '$lib/data.js';
	import { getSectionCompletedCount, subscribe } from '$lib/store.js';
	import type { SectionMeta, Chunk } from '$lib/types.js';

	let sections = $state<SectionMeta[]>([]);
	let sectionQuestionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});

	onMount(async () => {
		const data = await loadQuestions();
		sections = getSections(data);
		for (const s of sections) {
			const qs = getQuestionsBySection(data, s.id);
			sectionQuestionCounts[s.id] = qs.length;
			sectionCompleted[s.id] = getSectionCompletedCount(s.id);
		}

		const unsub = subscribe(() => {
			for (const s of sections) {
				sectionCompleted[s.id] = getSectionCompletedCount(s.id);
			}
		});
		return unsub;
	});

	function progressPercent(sectionId: string): number {
		const total = sectionQuestionCounts[sectionId] || 1;
		const done = sectionCompleted[sectionId] || 0;
		return Math.round((done / total) * 100);
	}

	// SVG progress ring
	function ringDasharray(percent: number): string {
		const circumference = 2 * Math.PI * 18;
		const filled = (percent / 100) * circumference;
		return `${filled} ${circumference - filled}`;
	}
</script>

<div class="practice-page">
	<header class="page-header">
		<a href="/" class="back-btn" aria-label="Назад">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 18l-6-6 6-6"/>
			</svg>
		</a>
		<h1>Тренировка</h1>
		<div style="width: 40px"></div>
	</header>

	<main class="section-list">
		{#each sections as section}
			{@const pct = progressPercent(section.id)}
			{@const color = sectionColor(section.id)}
			<a href="/practice/{section.id}" class="section-card">
				<div class="section-ring">
					<svg width="48" height="48" viewBox="0 0 48 48">
						<circle cx="24" cy="24" r="18" fill="none" stroke="var(--border)" stroke-width="4"/>
						<circle
							cx="24" cy="24" r="18"
							fill="none"
							stroke={color}
							stroke-width="4"
							stroke-dasharray={ringDasharray(pct)}
							stroke-dashoffset={2 * Math.PI * 18 * 0.25}
							stroke-linecap="round"
							transform="rotate(-90 24 24)"
						/>
						<text x="24" y="24" text-anchor="middle" dominant-baseline="central" font-size="11" font-weight="600" fill={color}>
							{pct}%
						</text>
					</svg>
				</div>
				<div class="section-info">
					<div class="section-name">
						<span class="section-emoji">{sectionIcon(section.id)}</span>
						{section.name}
					</div>
					<div class="section-meta">
						{sectionCompleted[section.id] || 0} / {sectionQuestionCounts[section.id] || section.questions} питања
					</div>
				</div>
				<div class="section-arrow">›</div>
			</a>
		{/each}
	</main>
</div>

<style>
	.practice-page {
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
		transition: background 0.2s;
	}

	.back-btn:active {
		background: var(--bg-secondary);
	}

	.section-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 1rem;
	}

	.section-card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		transition: transform 0.15s;
		text-decoration: none;
		color: var(--text);
	}

	.section-card:active {
		transform: scale(0.98);
	}

	.section-ring {
		flex-shrink: 0;
	}

	.section-info {
		flex: 1;
		min-width: 0;
	}

	.section-name {
		font-size: 0.9rem;
		font-weight: 600;
		line-height: 1.3;
	}

	.section-emoji {
		margin-right: 0.25rem;
	}

	.section-meta {
		font-size: 0.75rem;
		color: var(--text-secondary);
		margin-top: 0.15rem;
	}

	.section-arrow {
		font-size: 1.5rem;
		color: var(--text-muted);
		flex-shrink: 0;
	}
</style>
