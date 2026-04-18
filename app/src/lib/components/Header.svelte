<script lang="ts">
	import Icon from './Icon.svelte';
	import type { Snippet } from 'svelte';

	let { title, back = true, settings = true, trailing, onback, onsettings }: {
		title: string;
		back?: boolean;
		settings?: boolean;
		trailing?: Snippet;
		onback?: () => void;
		onsettings?: () => void;
	} = $props();
</script>

<div class="header">
	<button
		class="header-btn"
		style:visibility={back ? 'visible' : 'hidden'}
		onclick={onback}
	>
		<Icon name="back" size={20} />
	</button>
	<div class="header-title">{title}</div>
	{#if trailing}
		{@render trailing()}
	{:else}
		<button
			class="header-btn"
			style:visibility={settings ? 'visible' : 'hidden'}
			onclick={onsettings}
		>
			<Icon name="settings" size={19} stroke={1.5} />
		</button>
	{/if}
</div>

<style>
	.header {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 16px 4px;
		height: 48px;
		border-bottom: 0.5px solid var(--hairline);
		background: var(--bg);
		flex-shrink: 0;
	}
	.header-btn {
		width: 36px;
		height: 36px;
		border-radius: 12px;
		border: none;
		background: transparent;
		color: var(--ink);
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		flex-shrink: 0;
	}
	.header-title {
		flex: 1;
		text-align: center;
		font-family: var(--font-ui);
		font-size: 15px;
		font-weight: 600;
		letter-spacing: -0.1px;
		color: var(--ink);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
