<script lang="ts">
	let { name, size = 20, color = 'currentColor', stroke = 1.75 }: {
		name: string;
		size?: number;
		color?: string;
		stroke?: number;
	} = $props();
</script>

{#if name === 'back'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>
{:else if name === 'settings'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
{:else if name === 'check'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 12l5 5L20 6"/></svg>
{:else if name === 'x'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M6 18L18 6"/></svg>
{:else if name === 'chev-right'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>
{:else if name === 'chev-down'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M5 9l7 7 7-7"/></svg>
{:else if name === 'bookmark'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
{:else if name === 'bookmark-fill'}
<svg width={size} height={size} viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z" fill={color} stroke={color} stroke-width={stroke} stroke-linejoin="round"/></svg>
{:else if name === 'flag'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22V15"/></svg>
{:else if name === 'lightbulb'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6M10 22h4M12 2a7 7 0 00-4 12.7c1 .8 1.5 1.7 1.5 2.8V18h5v-.5c0-1.1.5-2 1.5-2.8A7 7 0 0012 2z"/></svg>
{:else if name === 'warn'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l10 18H2L12 3zM12 10v5M12 18v0.5"/></svg>
{:else if name === 'book'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h7a3 3 0 013 3v13M20 4h-7a3 3 0 00-3 3v13M4 4v15h7M20 4v15h-7"/></svg>
{:else if name === 'target'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill={color}/></svg>
{:else if name === 'bolt'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/></svg>
{:else if name === 'chart'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>
{:else if name === 'info'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v0.5M12 11v6"/></svg>
{:else if name === 'upload'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4M6 10l6-6 6 6M4 20h16"/></svg>
{:else if name === 'download'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12M6 10l6 6 6-6M4 20h16"/></svg>
{:else if name === 'coffee'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M3 10h14v6a4 4 0 01-4 4H7a4 4 0 01-4-4v-6zM17 11h2a3 3 0 010 6h-2M6 3v2M10 3v2M14 3v2"/></svg>
{:else if name === 'swap'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h14l-3-3M20 17H6l3 3"/></svg>
{:else if name === 'car'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M3 14l2-6a2 2 0 012-1.5h10A2 2 0 0119 8l2 6M3 14h18v4a1 1 0 01-1 1h-2a1 1 0 01-1-1v-1H7v1a1 1 0 01-1 1H4a1 1 0 01-1-1v-4zM7 17h0.5M17 17h-0.5"/></svg>
{:else if name === 'language'}
<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke} stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12M10 3v2M12 17l4-10 4 10M13.5 14h5M4 9s3 7 8 10M14 9s-3 5-10 9"/></svg>
{/if}
