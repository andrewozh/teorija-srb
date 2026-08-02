<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { goto, afterNavigate } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getQuestionsBySection, getChunks } from '$lib/data.js';
	import { getQuestionProgress, getMistakeStatus, subscribe, getSettings, updateSettings } from '$lib/store.js';
	import { sectionName } from '$lib/i18n.js';
	import { getTopicsForSection, getTopicModulesForSection, topicName, topicHint, moduleName, moduleSummary } from '$lib/topics.js';
	import type { Question, Chunk, Lang } from '$lib/types.js';
	import type { Topic, TopicModule } from '$lib/topics.js';
	import Header from '$lib/components/Header.svelte';
	import TopicHint from '$lib/components/TopicHint.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';

	let sectionId = $derived($page.params.section);
	let questions = $state<Question[]>([]);
	let chunks = $state<Chunk[]>([]);
	let topics = $state<Topic[] | null>(null);
	let modules = $state<TopicModule[] | null>(null);
	let expandedHints = $state<Set<string>>(new Set());
	let expandedModules = $state<Set<string>>(new Set());
	let totalQuestions = $state(0);
	let totalCorrect = $state(0);
	let totalWrong = $state(0);
	let totalRecovering = $state(0);
	let lang = $state<Lang>(getSettings().lang);

	// Topic chunks: each topic split into chunks of ≤20
	interface TopicGroup {
		topic: Topic;
		chunks: Chunk[];
		stats: { total: number; correct: number; wrong: number; recovering: number; oldestDays: number | null };
	}
	let topicGroups = $state<TopicGroup[]>([]);

	interface ModuleGroup {
		module: TopicModule;
		topics: TopicGroup[];
		stats: { total: number; correct: number; wrong: number; recovering: number };
	}

	function computeOldestDays(qs: Question[]): number | null {
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

	function computeQuestionStats(qs: Question[]): { correct: number; wrong: number; recovering: number } {
		let correct = 0, wrong = 0, recovering = 0;
		for (const q of qs) {
			const prog = getQuestionProgress(q.section, q.id);
			if (prog) {
				const mistake = getMistakeStatus(q.section, q.id);
				if (mistake === 'none' && prog.correct > 0) correct++;
				else if (mistake === 'recovering') recovering++;
				else if (mistake === 'wrong') wrong++;
			}
		}
		return { correct, wrong, recovering };
	}

	function buildTopicGroups(allQuestions: Question[], topics: Topic[]): TopicGroup[] {
		const qMap = new Map(allQuestions.map(q => [q.id, q]));
		return topics.map(topic => {
			const tqs = topic.questionIds.map(id => qMap.get(id)).filter(Boolean) as Question[];
			const tChunks = getChunks(tqs);
			const stats = computeQuestionStats(tqs);
			const oldestDays = computeOldestDays(tqs);
			return { topic, chunks: tChunks, stats: { total: tqs.length, ...stats, oldestDays } };
		});
	}

	function recalc() {
		if (topics) {
			topicGroups = buildTopicGroups(questions, topics);
			totalCorrect = topicGroups.reduce((s, g) => s + g.stats.correct, 0);
			totalWrong = topicGroups.reduce((s, g) => s + g.stats.wrong, 0);
			totalRecovering = topicGroups.reduce((s, g) => s + g.stats.recovering, 0);
			const topicQs = topicGroups.reduce((s, g) => s + g.stats.total, 0);
			console.log(`[section] totalQs=${totalQuestions} topicQs=${topicQs} correct=${totalCorrect} wrong=${totalWrong} recovering=${totalRecovering} sum=${totalCorrect+totalWrong+totalRecovering} gap=${totalQuestions - totalCorrect - totalWrong - totalRecovering}`);
		} else {
			chunks = getChunks(questions);
			const stats = computeQuestionStats(questions);
			totalCorrect = stats.correct;
			totalWrong = stats.wrong;
			totalRecovering = stats.recovering;
		}
	}

	let _sectionData: any = null;

	function reloadSection(id: string) {
		if (!_sectionData) return;
		questions = getQuestionsBySection(_sectionData, id);
		totalQuestions = questions.length;
		topics = getTopicsForSection(id);
		modules = getTopicModulesForSection(id);
		expandedHints = new Set();
		expandedModules = new Set(modules?.map((module) => module.id) ?? []);
		recalc();
	}

	afterNavigate(() => reloadSection(sectionId));

	onMount(async () => {
		_sectionData = await loadQuestions();
		reloadSection(sectionId);

		const unsub = subscribe(() => {
			lang = getSettings().lang;
			reloadSection(sectionId);
		});

		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'l' || e.key === 'L') {
				updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' });
			}
		};
		window.addEventListener('keydown', onKeyDown);

		return () => {
			unsub();
			window.removeEventListener('keydown', onKeyDown);
		};
	});

	function toggleHint(topicId: string) {
		const next = new Set(expandedHints);
		if (next.has(topicId)) next.delete(topicId);
		else next.add(topicId);
		expandedHints = next;
	}

	function toggleModule(moduleId: string) {
		const next = new Set(expandedModules);
		if (next.has(moduleId)) next.delete(moduleId);
		else next.add(moduleId);
		expandedModules = next;
	}

	let topicGroupIndexById = $derived(new Map(topicGroups.map((group, index) => [group.topic.id, index])));
	let moduleGroups = $derived.by((): ModuleGroup[] => {
		if (!modules) return [];
		const byId = new Map(topicGroups.map((group) => [group.topic.id, group]));
		return modules.map((module) => {
			const moduleTopics = module.topicIds.map((id) => byId.get(id)).filter(Boolean) as TopicGroup[];
			const stats = moduleTopics.reduce(
				(total, group) => ({
					total: total.total + group.stats.total,
					correct: total.correct + group.stats.correct,
					wrong: total.wrong + group.stats.wrong,
					recovering: total.recovering + group.stats.recovering
				}),
				{ total: 0, correct: 0, wrong: 0, recovering: 0 }
			);
			return { module, topics: moduleTopics, stats };
		});
	});

	// For topic-based: we need a global chunk index for routing
	// Build a flat chunk index map: globalIndex → { topicIndex, localChunkIndex }
	let globalChunkMap = $derived.by(() => {
		if (!topics) return [];
		const map: Array<{ questions: Question[] }> = [];
		for (const g of topicGroups) {
			for (const c of g.chunks) {
				map.push({ questions: c.questions });
			}
		}
		return map;
	});

	// Pre-compute global chunk index for each topic's chunk
	let topicChunkStartIndex = $derived.by(() => {
		const starts: number[] = [];
		let idx = 0;
		for (const g of topicGroups) {
			starts.push(idx);
			idx += g.chunks.length;
		}
		return starts;
	});

	let pct = $derived(totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0);
</script>

<div class="page">
	<Header
		title={sectionName(sectionId, lang)}
		onback={() => goto(`${base}/practice`)}
	>
		{#snippet trailing()}
			<button class="lang-btn" onclick={() => updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' })}>
				<Icon name="language" size={19} stroke={1.5} />
			</button>
		{/snippet}
	</Header>

	<div class="scroll-area">
		<!-- Section header -->
		<div class="section-header-area">
			<div class="section-meta">
				{lang === 'sr' ? 'Област' : 'Раздел'} · {totalQuestions} {lang === 'sr' ? 'питања' : 'вопросов'}
			</div>
			<div class="section-big-title">{sectionName(sectionId, lang)}</div>
			<ProgressBar value={totalCorrect} total={totalQuestions} height={4} wrong={totalWrong} recovering={totalRecovering} />
			<div class="section-stats">
				<span>
					<span class="correct-text">{totalCorrect}</span> {lang === 'sr' ? 'тачно' : 'верно'} ·
					<span class="recovering-text">{totalRecovering}</span> {lang === 'sr' ? 'поновљено' : 'повтор'} ·
					<span class="wrong-text">{totalWrong}</span> {lang === 'sr' ? 'погрешно' : 'неверно'}
				</span>
				<span>{pct}%</span>
			</div>
		</div>

		{#if topics && topicGroups.length > 0}
			{#if moduleGroups.length > 0}
				{#each moduleGroups as moduleGroup}
					<section class="module-section" class:module-collapsed={!expandedModules.has(moduleGroup.module.id)}>
						<button class="module-header" onclick={() => toggleModule(moduleGroup.module.id)} aria-expanded={expandedModules.has(moduleGroup.module.id)}>
							<div class="module-copy">
								<div class="module-name">{moduleName(moduleGroup.module, lang)}</div>
								<div class="module-summary">{moduleSummary(moduleGroup.module, lang)}</div>
							</div>
							<div class="module-right">
								<span>{moduleGroup.stats.correct}/{moduleGroup.stats.total}</span>
								<Icon name={expandedModules.has(moduleGroup.module.id) ? 'chev-down' : 'chev-right'} size={16} stroke={1.8} />
							</div>
						</button>

						{#if expandedModules.has(moduleGroup.module.id)}
							<div class="module-topics">
								{#each moduleGroup.topics as group}
									{@const gi = topicGroupIndexById.get(group.topic.id) ?? 0}
									<div class="topic-section">
										<div class="topic-header">
											<div class="topic-name">{topicName(group.topic, lang)}</div>
											<div class="topic-right">
												{#if group.stats.oldestDays !== null}<span class="topic-age">{group.stats.oldestDays}{lang === 'sr' ? 'д' : 'д'}</span>{/if}
												<span class="topic-count">{group.stats.correct}/{group.stats.total}</span>
												<button class="topic-hint-btn" aria-label={lang === 'sr' ? 'Прикажи савет' : 'Показать подсказку'} aria-expanded={expandedHints.has(group.topic.id)} onclick={() => toggleHint(group.topic.id)}>
													<Icon name="info" size={14} color="var(--accent)" stroke={1.8} />
												</button>
											</div>
										</div>

										{#if expandedHints.has(group.topic.id)}
											<div class="topic-hint"><TopicHint blocks={group.topic.hintBlocks} legacyHint={topicHint(group.topic, lang)} {lang} /></div>
										{/if}

										{#each group.chunks as chunk, ci}
											{@const globalChunkIdx = (topicChunkStartIndex[gi] || 0) + ci}
											{@const stat = computeQuestionStats(chunk.questions)}
											{@const isDone = stat.correct === chunk.questions.length}
											{@const isStarted = stat.correct > 0 || stat.wrong > 0}
											<a href="{base}/practice/{sectionId}/{globalChunkIdx}" class="block-card" style:opacity={!isStarted ? '0.5' : '1'}>
												<div class="block-num" class:block-done={isDone}>{#if isDone}<Icon name="check" size={13} stroke={2.5} />{:else}{globalChunkIdx + 1}{/if}</div>
												<div class="block-name">{lang === 'sr' ? 'Блок' : 'Блок'} {String(globalChunkIdx + 1).padStart(2, '0')}<span class="block-range">Q{chunk.questions[0]?.id}–{chunk.questions[chunk.questions.length - 1]?.id}</span></div>
												<div class="block-bar"><ProgressBar value={stat.correct} total={chunk.questions.length} height={2} wrong={stat.wrong} recovering={stat.recovering} /></div>
												<div class="block-count">{stat.correct}/{chunk.questions.length}</div>
											</a>
										{/each}
									</div>
								{/each}
							</div>
						{/if}
					</section>
				{/each}
			{:else}
				<!-- Existing flat topic layout for sections without modules -->
				{#each topicGroups as group, gi}
					<div class="topic-section">
						<div class="topic-header"><div class="topic-name">{topicName(group.topic, lang)}</div><div class="topic-right"><span class="topic-count">{group.stats.correct}/{group.stats.total}</span><button class="topic-hint-btn" aria-label={lang === 'sr' ? 'Прикажи савет' : 'Показать подсказку'} onclick={() => toggleHint(group.topic.id)}><Icon name="info" size={14} color="var(--accent)" stroke={1.8} /></button></div></div>
						{#if expandedHints.has(group.topic.id)}<div class="topic-hint"><TopicHint blocks={group.topic.hintBlocks} legacyHint={topicHint(group.topic, lang)} {lang} /></div>{/if}
						{#each group.chunks as chunk, ci}
							{@const globalChunkIdx = (topicChunkStartIndex[gi] || 0) + ci}
							{@const stat = computeQuestionStats(chunk.questions)}
							<a href="{base}/practice/{sectionId}/{globalChunkIdx}" class="block-card" style:opacity={!(stat.correct > 0 || stat.wrong > 0) ? '0.5' : '1'}><div class="block-num">{globalChunkIdx + 1}</div><div class="block-name">{lang === 'sr' ? 'Блок' : 'Блок'} {String(globalChunkIdx + 1).padStart(2, '0')}</div><div class="block-bar"><ProgressBar value={stat.correct} total={chunk.questions.length} height={2} wrong={stat.wrong} recovering={stat.recovering} /></div><div class="block-count">{stat.correct}/{chunk.questions.length}</div></a>
						{/each}
					</div>
				{/each}
			{/if}
		{:else}
			<!-- Flat chunks (sections without topics) -->
			<div class="blocks-label">
				{chunks.length} {lang === 'sr' ? 'блокова' : 'блоков'}
			</div>

			{#each chunks as chunk, i}
				{@const stat = computeQuestionStats(chunk.questions)}
				{@const isDone = stat.correct === chunk.questions.length}
				{@const isStarted = stat.correct > 0 || stat.wrong > 0}
				<a
					href="{base}/practice/{sectionId}/{chunk.index}"
					class="block-card"
					style:opacity={!isStarted ? '0.5' : '1'}
				>
					<div class="block-num" class:block-done={isDone}>
						{#if isDone}
							<Icon name="check" size={13} stroke={2.5} />
						{:else}
							{i + 1}
						{/if}
					</div>
					<div class="block-name">
						{lang === 'sr' ? 'Блок' : 'Блок'} {String(i + 1).padStart(2, '0')}
					</div>
					<div class="block-bar">
						<ProgressBar value={stat.correct} total={chunk.questions.length} height={2} wrong={stat.wrong} recovering={stat.recovering} />
					</div>
					<div class="block-count">{stat.correct}/{chunk.questions.length}</div>
				</a>
			{/each}
		{/if}
	</div>
</div>

<style>
	.lang-btn {
		width: 36px; height: 36px;
		border-radius: 12px; border: none;
		background: transparent; color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer; flex-shrink: 0;
	}
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 16px 14px 20px; }

	.section-header-area { padding: 4px 4px 16px; }
	.section-meta {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		margin-bottom: 6px;
	}
	.section-big-title {
		font-size: 24px;
		font-weight: 500;
		letter-spacing: -0.4px;
		margin-bottom: 14px;
	}
	.section-stats {
		display: flex;
		justify-content: space-between;
		margin-top: 10px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		letter-spacing: 0.3px;
	}
	.correct-text { color: var(--correct); }
	.recovering-text { color: var(--recovering); }
	.wrong-text { color: var(--wrong); }

	/* Learning modules */
	.module-section {
		margin: 0 -2px 12px;
		border: .5px solid var(--hairline);
		border-radius: 16px;
		background: var(--surface);
		overflow: hidden;
	}
	.module-header {
		width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 12px;
		padding: 14px 14px 13px; border: 0; background: transparent; color: var(--ink); text-align: left; cursor: pointer;
	}
	.module-copy { min-width: 0; }
	.module-name { font-size: 15px; font-weight: 650; letter-spacing: -.15px; }
	.module-summary { margin-top: 3px; font-size: 11px; line-height: 1.35; color: var(--ink3); }
	.module-right { display: flex; align-items: center; gap: 7px; font-family: var(--font-mono); font-size: 11px; color: var(--ink3); flex-shrink: 0; }
	.module-topics { padding: 0 10px 8px; border-top: .5px solid var(--hairline); }
	.module-collapsed .module-header { padding-bottom: 14px; }

	/* Topic layout */
	.topic-section {
		margin-bottom: 16px;
	}
	.topic-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		padding: 10px 4px 6px;
	}
	.topic-name {
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
		letter-spacing: -0.1px;
		flex: 1;
	}
	.topic-right {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}
	.topic-age {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink4);
	}
	.topic-count {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
	}
	.topic-hint-btn {
		cursor: pointer;
		display: flex;
		align-items: center;
		padding: 4px;
		border: 0;
		background: transparent;
		border-radius: 8px;
	}
	.topic-hint-btn:active { background: var(--surface2); }
	.topic-hint {
		padding: 12px 14px;
		margin: 0 0 10px;
		border-radius: 14px;
		background: var(--accent-wash);
		color: var(--ink);
	}

	/* Flat chunks label */
	.blocks-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		padding: 10px 4px;
	}

	/* Block cards */
	.block-card {
		display: flex;
		align-items: center;
		gap: 12px;
		background: var(--surface);
		border-radius: 14px;
		padding: 12px 14px;
		margin-bottom: 5px;
		border: 0.5px solid var(--hairline);
		text-decoration: none;
		color: inherit;
	}
	.block-num {
		width: 24px; height: 24px; border-radius: 6px;
		background: var(--surface2); color: var(--ink3);
		display: flex; align-items: center; justify-content: center;
		font-family: var(--font-mono); font-size: 11px;
		flex-shrink: 0;
	}
	.block-done {
		background: var(--correct-wash);
		color: var(--correct);
	}
	.block-name {
		flex: 1;
		font-size: 13px;
		letter-spacing: -0.1px;
	}
	.block-range {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		margin-left: 6px;
	}
	.block-bar { width: 80px; }
	.block-count {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		width: 34px;
		text-align: right;
	}

	/* Desktop */
	@media (min-width: 1024px) {
		.page { position: static; height: auto; padding-top: 0; z-index: auto; }
		.scroll-area { padding: 24px 40px 40px; max-width: 720px; }
	}
</style>
