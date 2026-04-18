<script lang="ts">
	import { getSettings, updateSettings, exportState, importState, resetState, subscribe } from '$lib/store.js';
	import { setPageTitle } from '$lib/nav.js';
	import { t } from '$lib/i18n.js';
	import type { Settings, Lang } from '$lib/types.js';

	let settings = $state<Settings>(getSettings());
	let showResetConfirm = $state(false);
	let importMessage = $state('');
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		setPageTitle(t('settings.title', lang));
	});

	$effect(() => {
		const unsub = subscribe(() => {
			settings = getSettings();
			lang = getSettings().lang;
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
				importMessage = success ? '✓' : '✗';
				setTimeout(() => { importMessage = ''; }, 3000);
			} catch {
				importMessage = '✗';
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

<div class="pb-4">
	<div class="p-3 d-flex flex-column gap-3">
		<!-- Theme -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="small fw-semibold text-body-secondary text-uppercase mb-3" style="letter-spacing:0.05em;">{t('settings.theme', lang)}</h2>
				<div class="btn-group w-100" role="group">
					<button
						class="btn {settings.theme === 'light' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('light')}
					>
						☀️ {t('settings.theme.light', lang)}
					</button>
					<button
						class="btn {settings.theme === 'dark' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('dark')}
					>
						🌙 {t('settings.theme.dark', lang)}
					</button>
					<button
						class="btn {settings.theme === 'system' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('system')}
					>
						⚙️ {t('settings.theme.system', lang)}
					</button>
				</div>
			</div>
		</div>

		<!-- Font size -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="small fw-semibold text-body-secondary text-uppercase mb-3" style="letter-spacing:0.05em;">{t('settings.font', lang)}</h2>
				<div class="btn-group w-100" role="group">
					<button
						class="btn {settings.fontSize === 'small' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('small')}
					>
						<span style="font-size:0.8rem">Аа</span>
					</button>
					<button
						class="btn {settings.fontSize === 'medium' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('medium')}
					>
						<span style="font-size:1rem">Аа</span>
					</button>
					<button
						class="btn {settings.fontSize === 'large' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('large')}
					>
						<span style="font-size:1.2rem">Аа</span>
					</button>
				</div>
			</div>
		</div>

		<!-- Data management -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<button class="btn btn-light d-flex align-items-center gap-3 w-100 text-start mb-2 p-3" onclick={handleExport}>
					<span class="fs-5">📤</span>
					<div>
						<div class="fw-medium">{t('settings.export', lang)}</div>
					</div>
				</button>

				<button class="btn btn-light d-flex align-items-center gap-3 w-100 text-start mb-2 p-3" onclick={handleImport}>
					<span class="fs-5">📥</span>
					<div>
						<div class="fw-medium">{t('settings.import', lang)}</div>
					</div>
				</button>

				{#if importMessage}
					<div class="alert {importMessage.startsWith('✓') ? 'alert-success' : 'alert-danger'} py-2 small mb-2">
						{importMessage}
					</div>
				{/if}

				<button class="btn btn-light d-flex align-items-center gap-3 w-100 text-start p-3" onclick={() => { showResetConfirm = true; }}>
					<span class="fs-5">🗑️</span>
					<div>
						<div class="fw-medium text-danger">{t('settings.reset', lang)}</div>
					</div>
				</button>

				{#if showResetConfirm}
					<div class="alert alert-danger mt-3">
						<p class="small mb-2">{t('settings.reset.confirm', lang)}</p>
						<div class="d-flex gap-2">
							<button class="btn btn-outline-secondary btn-sm flex-grow-1" onclick={() => { showResetConfirm = false; }}>
								{t('common.back', lang)}
							</button>
							<button class="btn btn-danger btn-sm flex-grow-1" onclick={handleReset}>
								{t('settings.reset.yes', lang)}
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- About -->
		<div class="card border-0 shadow-sm">
			<div class="card-body text-center text-body-tertiary small">
				<p class="mb-0">{t('settings.about', lang)}</p>
				<small>1780 • MUP</small>
			</div>
		</div>
	</div>
</div>
