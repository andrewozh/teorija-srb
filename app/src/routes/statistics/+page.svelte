<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection, sectionIcon, sectionColor } from '$lib/data.js';
	import {
		getTotalCompletedCount,
		getSectionCompletedCount,
		getExams,
		getMistakeQuestionKeys,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { SectionMeta, ExamResult, Lang } from '$lib/types.js';

	let sections = $state<SectionMeta[]>([]);
	let sectionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});
	let totalCompleted = $state(0);
	let totalActive = $state(0);
	let exams = $state<ExamResult[]>([]);
	let mistakeCount = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		setPageTitle(t('stats.title', lang));
	});

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

<div class="pb-4">
	<div class="p-3 d-flex flex-column gap-3">
		<!-- Overall progress -->
		<div class="card border-0 shadow-sm">
			<div class="card-body d-flex flex-column align-items-center gap-3 p-4">
				<h2 class="h6 fw-semibold mb-0">{t('stats.overall', lang)}</h2>
				<div class="overall-ring">
					<svg width="100" height="100" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="40" fill="none" stroke="var(--bs-border-color)" stroke-width="8"/>
						<circle
							cx="50" cy="50" r="40"
							fill="none"
							stroke="var(--bs-primary)"
							stroke-width="8"
							stroke-dasharray="{(overallPercent / 100) * 2 * Math.PI * 40} {2 * Math.PI * 40}"
							stroke-linecap="round"
							transform="rotate(-90 50 50)"
						/>
						<text x="50" y="46" text-anchor="middle" font-size="20" font-weight="700" fill="var(--bs-body-color)">
							{overallPercent}%
						</text>
					</svg>
				</div>
				<div class="d-flex gap-4">
					<div class="text-center">
						<span class="d-block fs-5 fw-bold">{totalCompleted}</span>
						<small class="text-body-secondary">✓</small>
					</div>
					<div class="text-center">
						<span class="d-block fs-5 fw-bold">{totalActive - totalCompleted}</span>
						<small class="text-body-secondary">…</small>
					</div>
					<div class="text-center">
						<span class="d-block fs-5 fw-bold">{mistakeCount}</span>
						<small class="text-body-secondary">✗</small>
					</div>
				</div>
			</div>
		</div>

		<!-- Per-section breakdown -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="h6 fw-semibold mb-3">{t('stats.sections', lang)}</h2>
				{#each sections as section}
					{@const total = sectionCounts[section.id] || 1}
					{@const done = sectionCompleted[section.id] || 0}
					{@const pct = Math.round((done / total) * 100)}
					<div class="mb-3">
						<div class="d-flex align-items-center gap-2 mb-1">
							<span>{sectionIcon(section.id)}</span>
							<small class="text-body-secondary text-truncate">{sectionName(section.id, lang)}</small>
						</div>
						<div class="d-flex align-items-center gap-2">
							<div class="progress flex-grow-1" style="height:6px;">
								<div class="progress-bar" style="width:{pct}%;background:{sectionColor(section.id)}"></div>
							</div>
							<small class="text-body-tertiary flex-shrink-0" style="min-width:4rem;text-align:right;">{done}/{total}</small>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Exam history -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="h6 fw-semibold mb-3">{t('stats.exams', lang)}</h2>
				{#if exams.length === 0}
					<p class="text-body-tertiary small text-center py-3">{t('stats.no_exams', lang)}</p>
				{:else}
					{#each exams as exam, i}
						<div class="d-flex align-items-center justify-content-between py-2 {i < exams.length - 1 ? 'border-bottom' : ''}">
							<div class="d-flex align-items-center gap-2">
								<span class="badge rounded-circle d-flex align-items-center justify-content-center {exam.passed ? 'text-bg-success' : 'text-bg-danger'}" style="width:28px;height:28px;font-size:0.8rem;">
									{exam.passed ? '✓' : '✗'}
								</span>
								<div>
									<div class="small fw-semibold">{exam.score} / {exam.total}</div>
									<div class="text-body-tertiary" style="font-size:0.7rem;">{formatDate(exam.date)}</div>
								</div>
							</div>
							<small class="text-body-secondary">{exam.total - exam.score} {t('exam.errors', lang)}</small>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	</div>
</div>
