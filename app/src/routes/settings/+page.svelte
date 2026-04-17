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

<div class="pb-4">
	<!-- Header -->
	<nav class="navbar sticky-top bg-body border-bottom px-2">
		<div class="d-flex align-items-center justify-content-between w-100">
			<a href="/" class="btn btn-link text-body p-2" aria-label="Назад">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 18l-6-6 6-6"/>
				</svg>
			</a>
			<h1 class="h6 fw-semibold mb-0">Подешавања</h1>
			<div style="width:40px"></div>
		</div>
	</nav>

	<div class="p-3 d-flex flex-column gap-3">
		<!-- Theme -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="small fw-semibold text-body-secondary text-uppercase mb-3" style="letter-spacing:0.05em;">Тема</h2>
				<div class="btn-group w-100" role="group">
					<button
						class="btn {settings.theme === 'light' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('light')}
					>
						☀️ Светла
					</button>
					<button
						class="btn {settings.theme === 'dark' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('dark')}
					>
						🌙 Тамна
					</button>
					<button
						class="btn {settings.theme === 'system' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setTheme('system')}
					>
						⚙️ Систем
					</button>
				</div>
			</div>
		</div>

		<!-- Font size -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="small fw-semibold text-body-secondary text-uppercase mb-3" style="letter-spacing:0.05em;">Величина текста</h2>
				<div class="btn-group w-100" role="group">
					<button
						class="btn {settings.fontSize === 'small' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('small')}
					>
						<span style="font-size:0.8rem">Аа</span> Мало
					</button>
					<button
						class="btn {settings.fontSize === 'medium' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('medium')}
					>
						<span style="font-size:1rem">Аа</span> Средње
					</button>
					<button
						class="btn {settings.fontSize === 'large' ? 'btn-primary' : 'btn-outline-secondary'}"
						onclick={() => setFontSize('large')}
					>
						<span style="font-size:1.2rem">Аа</span> Велико
					</button>
				</div>
			</div>
		</div>

		<!-- Data management -->
		<div class="card border-0 shadow-sm">
			<div class="card-body">
				<h2 class="small fw-semibold text-body-secondary text-uppercase mb-3" style="letter-spacing:0.05em;">Подаци</h2>

				<button class="btn btn-light d-flex align-items-center gap-3 w-100 text-start mb-2 p-3" onclick={handleExport}>
					<span class="fs-5">📤</span>
					<div>
						<div class="fw-medium">Извези податке</div>
						<small class="text-body-tertiary">Преузми JSON фајл са напретком</small>
					</div>
				</button>

				<button class="btn btn-light d-flex align-items-center gap-3 w-100 text-start mb-2 p-3" onclick={handleImport}>
					<span class="fs-5">📥</span>
					<div>
						<div class="fw-medium">Увези податке</div>
						<small class="text-body-tertiary">Учитај претходно сачуван напредак</small>
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
						<div class="fw-medium text-danger">Обриши све податке</div>
						<small class="text-body-tertiary">Ресетуј напредак, обележене и историју</small>
					</div>
				</button>

				{#if showResetConfirm}
					<div class="alert alert-danger mt-3">
						<p class="small mb-2">Да ли сте сигурни? Ова акција се не може поништити.</p>
						<div class="d-flex gap-2">
							<button class="btn btn-outline-secondary btn-sm flex-grow-1" onclick={() => { showResetConfirm = false; }}>
								Откажи
							</button>
							<button class="btn btn-danger btn-sm flex-grow-1" onclick={handleReset}>
								Обриши
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- About -->
		<div class="card border-0 shadow-sm">
			<div class="card-body text-center text-body-tertiary small">
				<p class="mb-0">Возачки испит — Вежбање</p>
				<small>1780 питања • МУП Србије</small>
			</div>
		</div>
	</div>
</div>
