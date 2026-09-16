declare module 'katex/contrib/mhchem';

declare module '@joplin/turndown-plugin-gfm' {
	import type TurndownService from 'turndown';

	export const gfm: TurndownService.Plugin;
}

declare module '@sveltejs/svelte-virtual-list' {
	import { SvelteComponentTyped } from 'svelte';

	export default class VirtualList<Item> extends SvelteComponentTyped<
		{
			items: Item[];
			rowHeight: number;
			height?: number | string;
			width?: number | string;
		},
		Record<string, never>,
		{ default: { item: Item } }
	> {}
}
