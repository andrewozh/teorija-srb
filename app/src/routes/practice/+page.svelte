<script lang="ts">
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection, sectionIcon, sectionColor } from '$lib/data.js';
	import { getSectionCompletedCount, subscribe, getSettings } from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t, sectionName } from '$lib/i18n.js';
	import type { SectionMeta } from '$lib/types.js';
	import type { Lang } from '$lib/types.js';

	let sections = $state<SectionMeta[]>([]);
	let sectionQuestionCounts = $state<Record<string, number>>({});
	let sectionCompleted = $state<Record<string, number>>({});
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		setPageTitle(t('practice.title', lang));
	});

	onMount(async () => {
		const data = await loadQuestions();
		sections = getSections(data);
		for (const s of sections) {
			const qs = getQuestionsBySection(data, s.id);
			sectionQuestionCounts[s.id] = qs.length;
			sectionCompleted[s.id] = getSectionCompletedCount(s.id);
		}

		const unsub = subscribe(() => {
			lang = getSettings().lang;
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

<div class="pb-4">
	<!-- Section list -->
	<div class="list-group list-group-flush px-3 pt-3 d-flex flex-column gap-2">
		{#each sections as section}
			{@const pct = progressPercent(section.id)}
			{@const color = sectionColor(section.id)}
			<a href="/practice/{section.id}" class="list-group-item list-group-item-action d-flex align-items-center gap-3 rounded-3 border shadow-sm px-3 py-3">
				<div class="flex-shrink-0">
					<svg width="48" height="48" viewBox="0 0 48 48">
						<circle cx="24" cy="24" r="18" fill="none" stroke="var(--bs-border-color)" stroke-width="4"/>
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
				<div class="flex-grow-1 min-w-0">
					<div class="fw-semibold small">
						<span class="me-1">{sectionIcon(section.id)}</span>{sectionName(section.id, lang)}
					</div>
					<small class="text-body-secondary">
						{sectionCompleted[section.id] || 0} / {sectionQuestionCounts[section.id] || section.questions} {t('practice.questions', lang)}
					</small>
				</div>
				<span class="text-body-tertiary fs-4">›</span>
			</a>
		{/each}
	</div>
</div>
