<script lang="ts">
	import { getSettings, updateSettings, exportState, importState, resetState, subscribe } from '$lib/store.js';
	import type { Settings } from '$lib/types.js';

	let settings = $state<Settings>(getSettings());
	let showResetConfirm = $state(false);
	let importMessage = $state('');

	$effect(() => {
		const unsub = subscribe(() => {
			settings = getSettings();
		});
		return unsub;
	});

	function setTheme(theme: Settings['theme']) {
		updateSettings({ theme });
	}

	function setFontSize(fontSize: Settings['fontSize']) {
		updateSettings({ fontSize });
	}

	function handleExport() {
		const data = exportState();
		const blob = new Blob([data], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `vozacki-ispit-backup-${new Date().toISOString().split('T')[0]}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	function handleImport() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = async () => {
			const file = input.files?.[0];
			if (!file) return;
			try {
				const text = await file.text();
				const success = importState(text);
				importMessage = success ? '✓ Подаци успешно увезени!' : '✗ Неисправан формат фајла.';
				setTimeout(() => { importMessage = ''; }, 3000);
			} catch {
				importMessage = '✗ Грешка при читању фајла.';
				setTimeout(() => { importMessage = ''; }, 3000);
			}
		};
		input.click();
	}

	function handleReset() {
		resetState();
		showResetConfirm = false;
	}
</script>

<div class="settings-page">
	<header class="page-header">
		<a href="/" class="back-btn" aria-label="Назад">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 18l-6-6 6-6"/>
			</svg>
		</a>
		<h1>Подешавања</h1>
		<div style="width: 40px"></div>
	</header>

	<main class="settings-content">
		<!-- Theme -->
		<div class="settings-group">
			<h2>Тема</h2>
			<div class="toggle-group">
				<button
					class="toggle-btn"
					class:active={settings.theme === 'light'}
					onclick={() => setTheme('light')}
				>
					☀️ Светла
				</button>
				<button
					class="toggle-btn"
					class:active={settings.theme === 'dark'}
					onclick={() => setTheme('dark')}
				>
					🌙 Тамна
				</button>
				<button
					class="toggle-btn"
					class:active={settings.theme === 'system'}
					onclick={() => setTheme('system')}
				>
					⚙️ Систем
				</button>
			</div>
		</div>

		<!-- Font size -->
		<div class="settings-group">
			<h2>Величина текста</h2>
			<div class="toggle-group">
				<button
					class="toggle-btn"
					class:active={settings.fontSize === 'small'}
					onclick={() => setFontSize('small')}
				>
					<span style="font-size: 0.8rem">Аа</span> Мало
				</button>
				<button
					class="toggle-btn"
					class:active={settings.fontSize === 'medium'}
					onclick={() => setFontSize('medium')}
				>
					<span style="font-size: 1rem">Аа</span> Средње
				</button>
				<button
					class="toggle-btn"
					class:active={settings.fontSize === 'large'}
					onclick={() => setFontSize('large')}
				>
					<span style="font-size: 1.2rem">Аа</span> Велико
				</button>
			</div>
		</div>

		<!-- Data management -->
		<div class="settings-group">
			<h2>Подаци</h2>

			<button class="action-btn" onclick={handleExport}>
				<span class="action-icon">📤</span>
				<div class="action-body">
					<span class="action-title">Извези податке</span>
					<span class="action-desc">Преузми JSON фајл са напретком</span>
				</div>
			</button>

			<button class="action-btn" onclick={handleImport}>
				<span class="action-icon">📥</span>
				<div class="action-body">
					<span class="action-title">Увези податке</span>
					<span class="action-desc">Учитај претходно сачуван напредак</span>
				</div>
			</button>

			{#if importMessage}
				<div class="import-message" class:success={importMessage.startsWith('✓')}>
					{importMessage}
				</div>
			{/if}

			<button class="action-btn danger" onclick={() => { showResetConfirm = true; }}>
				<span class="action-icon">🗑️</span>
				<div class="action-body">
					<span class="action-title">Обриши све податке</span>
					<span class="action-desc">Ресетуј напредак, обележене и историју</span>
				</div>
			</button>

			{#if showResetConfirm}
				<div class="confirm-box">
					<p>Да ли сте сигурни? Ова акција се не може поништити.</p>
					<div class="confirm-actions">
						<button class="confirm-cancel" onclick={() => { showResetConfirm = false; }}>
							Откажи
						</button>
						<button class="confirm-delete" onclick={handleReset}>
							Обриши
						</button>
					</div>
				</div>
			{/if}
		</div>

		<!-- About -->
		<div class="settings-group about">
			<p>Возачки испит — Вежбање</p>
			<p class="about-sub">1780 питања • МУП Србије</p>
		</div>
	</main>
</div>

<style>
	.settings-page {
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

	.settings-content {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.settings-group {
		background: var(--card);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 1rem;
	}

	.settings-group h2 {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.75rem;
	}

	.toggle-group {
		display: flex;
		gap: 0.5rem;
	}

	.toggle-btn {
		flex: 1;
		padding: 0.6rem 0.5rem;
		border-radius: var(--radius-sm);
		font-size: 0.8rem;
		font-weight: 500;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.3rem;
	}

	.toggle-btn.active {
		background: var(--primary);
		color: white;
	}

	.toggle-btn:active {
		transform: scale(0.97);
	}

	/* Action buttons */
	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.75rem;
		border-radius: var(--radius-sm);
		text-align: left;
		transition: background 0.2s;
		margin-bottom: 0.5rem;
	}

	.action-btn:last-child {
		margin-bottom: 0;
	}

	.action-btn:active {
		background: var(--bg-secondary);
	}

	.action-btn.danger:active {
		background: var(--danger-light);
	}

	.action-icon {
		font-size: 1.3rem;
		flex-shrink: 0;
	}

	.action-body {
		display: flex;
		flex-direction: column;
	}

	.action-title {
		font-size: 0.9rem;
		font-weight: 500;
	}

	.action-desc {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.action-btn.danger .action-title {
		color: var(--danger);
	}

	.import-message {
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius-sm);
		font-size: 0.85rem;
		font-weight: 500;
		background: var(--danger-light);
		color: var(--danger);
		margin-bottom: 0.5rem;
	}

	.import-message.success {
		background: var(--success-light);
		color: var(--success);
	}

	.confirm-box {
		background: var(--danger-light);
		border-radius: var(--radius-sm);
		padding: 1rem;
		margin-top: 0.5rem;
	}

	.confirm-box p {
		font-size: 0.85rem;
		margin-bottom: 0.75rem;
		color: var(--danger);
	}

	.confirm-actions {
		display: flex;
		gap: 0.5rem;
	}

	.confirm-cancel {
		flex: 1;
		padding: 0.5rem;
		border-radius: var(--radius-sm);
		background: var(--card);
		font-weight: 500;
		font-size: 0.85rem;
	}

	.confirm-delete {
		flex: 1;
		padding: 0.5rem;
		border-radius: var(--radius-sm);
		background: var(--danger);
		color: white;
		font-weight: 600;
		font-size: 0.85rem;
	}

	.about {
		text-align: center;
		color: var(--text-muted);
		font-size: 0.8rem;
	}

	.about-sub {
		font-size: 0.7rem;
		margin-top: 0.2rem;
	}
</style>
