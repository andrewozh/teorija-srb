<script lang="ts">
	import type { Lang } from '$lib/types.js';
	import type { LessonBlock, LocalizedText } from '$lib/topics.js';

	let { blocks, legacyHint, lang }: { blocks?: LessonBlock[]; legacyHint: string; lang: Lang } = $props();

	function localize(text: LocalizedText): string {
		return text[lang] || text.sr;
	}

	function rich(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
			.replace(/`(.+?)`/g, '<span class="term">$1</span>')
			.replace(/\n/g, '<br>');
	}
</script>

<div class="hint">
	{#if blocks && blocks.length > 0}
		{#each blocks as block}
			{#if block.type === 'intro'}
				<p class="intro">{@html rich(localize(block.text))}</p>
			{:else if block.type === 'bullets'}
				<section class="block">
					{#if block.title}<h4>{@html rich(localize(block.title))}</h4>{/if}
					<ul>
						{#each block.items as item}
							<li>{@html rich(localize(item))}</li>
						{/each}
					</ul>
				</section>
			{:else if block.type === 'table'}
				<section class="block table-wrap">
					{#if block.title}<h4>{@html rich(localize(block.title))}</h4>{/if}
					<div class="table-scroll">
						<table>
							<thead>
								<tr>{#each block.headers as header}<th>{@html rich(localize(header))}</th>{/each}</tr>
							</thead>
							<tbody>
								{#each block.rows as row}
									<tr>{#each row as cell}<td>{@html rich(localize(cell))}</td>{/each}</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</section>
			{:else if block.type === 'formula'}
				<section class="formula">
					<div class="formula-label">{@html rich(localize(block.label))}</div>
					<div class="formula-text">{@html rich(localize(block.text))}</div>
				</section>
			{:else if block.type === 'callout'}
				<section class="callout">
					<div class="callout-label">{@html rich(localize(block.label))}</div>
					<div>{@html rich(localize(block.text))}</div>
				</section>
			{/if}
		{/each}
	{:else}
		<p class="legacy">{@html rich(legacyHint)}</p>
	{/if}
</div>

<style>
	.hint { font-size: 13px; line-height: 1.52; color: var(--ink); }
	.intro, .legacy { margin: 0; }
	.block { margin-top: 12px; }
	h4, .formula-label, .callout-label {
		margin: 0 0 6px;
		font-family: var(--font-mono);
		font-size: 10px;
		font-weight: 600;
		letter-spacing: .7px;
		text-transform: uppercase;
		color: var(--accent);
	}
	ul { margin: 0; padding-left: 18px; }
	li { margin: 4px 0; padding-left: 2px; }
	.table-wrap { margin-left: -2px; margin-right: -2px; }
	.table-scroll { overflow-x: auto; border: .5px solid var(--hairline); border-radius: 10px; }
	table { width: 100%; min-width: 370px; border-collapse: collapse; font-size: 12px; line-height: 1.35; }
	th, td { padding: 8px 9px; text-align: left; vertical-align: top; border-bottom: .5px solid var(--hairline); }
	th { background: var(--surface2); font-size: 10px; font-weight: 600; color: var(--ink2); }
	tr:last-child td { border-bottom: 0; }
	.formula, .callout { margin-top: 12px; padding: 10px 12px; border-radius: 10px; }
	.formula { background: var(--surface2); border: .5px solid var(--hairline); }
	.formula-text { font-family: var(--font-mono); font-size: 12px; line-height: 1.45; }
	.callout { background: var(--accent-wash); border-left: 3px solid var(--accent); }
	.callout-label { margin-bottom: 3px; }
	:global(.term) { font-family: var(--font-mono); font-size: .91em; white-space: nowrap; color: var(--ink2); }
</style>
