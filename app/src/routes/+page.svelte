<script lang="ts">
	import {
		getTotalCompletedCount,
		getMistakeQuestionKeys,
		getPassedExamCount,
		getExams,
		subscribe,
		getProgress
	} from '$lib/store.js';

	let completed = $state(getTotalCompletedCount());
	let mistakeCount = $state(getMistakeQuestionKeys().length);
	let passedExams = $state(getPassedExamCount());
	let totalExams = $state(getExams().length);

	$effect(() => {
		const unsub = subscribe(() => {
			completed = getTotalCompletedCount();
			mistakeCount = getMistakeQuestionKeys().length;
			passedExams = getPassedExamCount();
			totalExams = getExams().length;
		});
		return unsub;
	});

	const totalQuestions = 1756; // 1780 - 24 removed

	let progressPercent = $derived(Math.round((completed / totalQuestions) * 100));
</script>

<div class="home">
	<header class="home-header">
		<div class="header-content">
			<h1>🚗 Возачки испит</h1>
			<a href="/settings" class="settings-btn" aria-label="Подешавања">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="3"/>
					<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
				</svg>
			</a>
		</div>
	</header>

	<main class="cards">
		<a href="/practice" class="card card-practice">
			<div class="card-icon">📚</div>
			<div class="card-body">
				<h2>Тренировка</h2>
				<p>{completed} / {totalQuestions} питања</p>
			</div>
			<div class="card-progress">
				<div class="progress-bar">
					<div class="progress-fill" style="width: {progressPercent}%"></div>
				</div>
				<span class="progress-text">{progressPercent}%</span>
			</div>
		</a>

		<a href="/exam" class="card card-exam">
			<div class="card-icon">📝</div>
			<div class="card-body">
				<h2>Испит</h2>
				<p>{passedExams} положених од {totalExams} покушаја</p>
			</div>
			<div class="card-arrow">→</div>
		</a>

		<a href="/mistakes" class="card card-mistakes">
			<div class="card-icon">❌</div>
			<div class="card-body">
				<h2>Моје грешке</h2>
				<p>{mistakeCount} питања за понављање</p>
			</div>
			<div class="card-arrow">→</div>
		</a>

		<a href="/statistics" class="card card-stats">
			<div class="card-icon">📊</div>
			<div class="card-body">
				<h2>Статистика</h2>
				<p>Преглед напретка</p>
			</div>
			<div class="card-arrow">→</div>
		</a>
	</main>
</div>

<style>
	.home {
		padding-bottom: 2rem;
	}

	.home-header {
		background: var(--primary);
		color: white;
		padding: 1.5rem 1rem 2rem;
		border-radius: 0 0 24px 24px;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-content h1 {
		font-size: 1.4rem;
		font-weight: 700;
	}

	.settings-btn {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		background: rgba(255, 255, 255, 0.2);
		transition: background 0.2s;
	}

	.settings-btn:active {
		background: rgba(255, 255, 255, 0.3);
	}

	.cards {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		padding: 1rem;
		margin-top: -1rem;
	}

	.card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		transition: transform 0.15s, box-shadow 0.15s;
		text-decoration: none;
		color: white;
	}

	.card:active {
		transform: scale(0.98);
	}

	.card-practice {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		flex-wrap: wrap;
	}

	.card-exam {
		background: linear-gradient(135deg, #10b981, #059669);
	}

	.card-mistakes {
		background: linear-gradient(135deg, #ef4444, #dc2626);
	}

	.card-stats {
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
	}

	.card-icon {
		font-size: 2rem;
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.2);
		border-radius: var(--radius-sm);
		flex-shrink: 0;
	}

	.card-body {
		flex: 1;
		min-width: 0;
	}

	.card-body h2 {
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: 0.15rem;
	}

	.card-body p {
		font-size: 0.8rem;
		opacity: 0.9;
	}

	.card-arrow {
		font-size: 1.2rem;
		opacity: 0.7;
		flex-shrink: 0;
	}

	.card-progress {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.progress-bar {
		flex: 1;
		height: 6px;
		background: rgba(255, 255, 255, 0.3);
		border-radius: 3px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: white;
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.75rem;
		font-weight: 600;
		opacity: 0.9;
		flex-shrink: 0;
	}
</style>
