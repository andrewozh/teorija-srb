<script lang="ts">
	import {
		getTotalCompletedCount,
		getMistakeQuestionKeys,
		getPassedExamCount,
		getExams,
		subscribe,
		getSettings
	} from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Lang } from '$lib/types.js';

	let completed = $state(getTotalCompletedCount());
	let mistakeCount = $state(getMistakeQuestionKeys().length);
	let passedExams = $state(getPassedExamCount());
	let totalExams = $state(getExams().length);
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		const unsub = subscribe(() => {
			completed = getTotalCompletedCount();
			mistakeCount = getMistakeQuestionKeys().length;
			passedExams = getPassedExamCount();
			totalExams = getExams().length;
			lang = getSettings().lang;
		});
		return unsub;
	});

	const totalQuestions = 1756; // 1780 - 24 removed

	let progressPercent = $derived(Math.round((completed / totalQuestions) * 100));
</script>

<div class="pb-4">
	<!-- Cards -->
	<div class="d-flex flex-column gap-3 px-3 pt-3">
		<!-- Practice card -->
		<a href="/practice" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">
			<div class="card-body d-flex align-items-center gap-3 flex-wrap">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">📚</div>
				<div class="flex-grow-1 min-w-0">
					<h2 class="h6 fw-semibold mb-0">{t('home.practice', lang)}</h2>
					<small class="opacity-75">{completed} / {totalQuestions} {t('home.practice.sub', lang)}</small>
				</div>
				<div class="w-100 d-flex align-items-center gap-2 mt-1">
					<div class="progress flex-grow-1" style="height:6px;background:rgba(255,255,255,0.3);">
						<div class="progress-bar bg-white" style="width:{progressPercent}%"></div>
					</div>
					<small class="fw-semibold opacity-75 flex-shrink-0">{progressPercent}%</small>
				</div>
			</div>
		</a>

		<!-- Exam card -->
		<a href="/exam" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #10b981, #059669);">
			<div class="card-body d-flex align-items-center gap-3">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">📝</div>
				<div class="flex-grow-1">
					<h2 class="h6 fw-semibold mb-0">{t('home.exam', lang)}</h2>
					<small class="opacity-75">{passedExams} {t('home.exam.passed', lang)} {t('home.exam.of', lang)} {totalExams} {t('home.exam.attempts', lang)}</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>

		<!-- Mistakes card -->
		<a href="/mistakes" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #ef4444, #dc2626);">
			<div class="card-body d-flex align-items-center gap-3">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">❌</div>
				<div class="flex-grow-1">
					<h2 class="h6 fw-semibold mb-0">{t('home.mistakes', lang)}</h2>
					<small class="opacity-75">{mistakeCount} {t('home.mistakes.sub', lang)}</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>

		<!-- Statistics card -->
		<a href="/statistics" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);">
			<div class="card-body d-flex align-items-center gap-3">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">📊</div>
				<div class="flex-grow-1">
					<h2 class="h6 fw-semibold mb-0">{t('home.stats', lang)}</h2>
					<small class="opacity-75">{t('home.stats.sub', lang)}</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>
	</div>
</div>
