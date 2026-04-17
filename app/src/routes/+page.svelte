<script lang="ts">
	import {
		getTotalCompletedCount,
		getMistakeQuestionKeys,
		getPassedExamCount,
		getExams,
		subscribe,
		getProgress,
		getSettings,
		updateSettings
	} from '$lib/store.js';
	import type { Lang } from '$lib/types.js';

	let completed = $state(getTotalCompletedCount());
	let mistakeCount = $state(getMistakeQuestionKeys().length);
	let passedExams = $state(getPassedExamCount());
	let totalExams = $state(getExams().length);
	let lang = $state(getSettings().lang);

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

	function toggleLang() {
		const next: Lang = lang === 'sr' ? 'ru' : 'sr';
		updateSettings({ lang: next });
	}

	const totalQuestions = 1756; // 1780 - 24 removed

	let progressPercent = $derived(Math.round((completed / totalQuestions) * 100));
</script>

<div class="pb-4">
	<!-- Header -->
	<div class="px-3 pt-4 pb-4">
		<div class="d-flex justify-content-between align-items-center">
			<h1 class="h5 fw-bold mb-0">🚗 Возачки испит</h1>
			<div class="d-flex gap-2">
				<button onclick={toggleLang} class="btn btn-outline-secondary btn-sm fw-bold" style="min-width:42px;">
					{lang === 'sr' ? 'RU' : 'SR'}
				</button>
				<a href="/settings" class="btn btn-outline-secondary btn-sm rounded-circle d-flex align-items-center justify-content-center" style="width:36px;height:36px;" aria-label="Подешавања">
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="3" y1="6" x2="21" y2="6"/>
						<line x1="3" y1="12" x2="21" y2="12"/>
						<line x1="3" y1="18" x2="21" y2="18"/>
					</svg>
				</a>
			</div>
		</div>
	</div>

	<!-- Cards -->
	<div class="d-flex flex-column gap-3 px-3">
		<!-- Practice card -->
		<a href="/practice" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">
			<div class="card-body d-flex align-items-center gap-3 flex-wrap">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">📚</div>
				<div class="flex-grow-1 min-w-0">
					<h2 class="h6 fw-semibold mb-0">Тренировка</h2>
					<small class="opacity-75">{completed} / {totalQuestions} питања</small>
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
					<h2 class="h6 fw-semibold mb-0">Испит</h2>
					<small class="opacity-75">{passedExams} положених од {totalExams} покушаја</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>

		<!-- Mistakes card -->
		<a href="/mistakes" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #ef4444, #dc2626);">
			<div class="card-body d-flex align-items-center gap-3">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">❌</div>
				<div class="flex-grow-1">
					<h2 class="h6 fw-semibold mb-0">Моје грешке</h2>
					<small class="opacity-75">{mistakeCount} питања за понављање</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>

		<!-- Statistics card -->
		<a href="/statistics" class="card text-white text-decoration-none border-0 shadow-sm" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);">
			<div class="card-body d-flex align-items-center gap-3">
				<div class="d-flex align-items-center justify-content-center rounded-3 flex-shrink-0" style="width:48px;height:48px;background:rgba(255,255,255,0.2);font-size:2rem;">📊</div>
				<div class="flex-grow-1">
					<h2 class="h6 fw-semibold mb-0">Статистика</h2>
					<small class="opacity-75">Преглед напретка</small>
				</div>
				<span class="opacity-50 fs-5">→</span>
			</div>
		</a>
	</div>
</div>
