<script lang="ts">
	import { onDestroy } from 'svelte';
	import TerminalOutputFile from './TerminalOutputFile.svelte';
	import Model3DPreview from '$lib/components/common/Model3DPreview.svelte';
	import { selectedTerminalId, settings, terminalServers } from '$lib/stores';
	import { downloadFileBlob } from '$lib/apis/terminal';
	import { fileExtension, isModel3dFile } from '$lib/utils/model3d';

	export let item: any;
	export let chatId = '';

	let loading = false;
	let error = '';
	let modelData: ArrayBuffer | null = null;
	let loadedKey = '';
	let expanded = true;

	$: path = String(item?.full_path || item?.path || '');
	$: name = String(item?.name || path.split('/').filter(Boolean).at(-1) || 'model');
	$: model = isModel3dFile(name || path);
	$: selector = item?.terminal_selector;
	$: terminal = resolveTerminal();
	$: key = terminal ? `${terminal.url}|${path}|${chatId}` : '';
	$: if (model && expanded && terminal && key && key !== loadedKey && !loading) void loadModel(key);

	function resolveTerminal(): { url: string; key: string } | null {
		if (!selector || $selectedTerminalId !== selector) return null;
		const systemTerminal = ($terminalServers ?? []).find((server: any) => server.id === selector);
		if (systemTerminal?.url) return { url: systemTerminal.url, key: localStorage.token };
		const directTerminal = (($settings as any)?.terminalServers ?? []).find(
			(server: any) => server.url === selector && server.enabled
		);
		return directTerminal?.url ? { url: directTerminal.url, key: directTerminal.key ?? '' } : null;
	}

	async function loadModel(nextKey: string) {
		loadedKey = nextKey;
		loading = true;
		error = '';
		try {
			if (!terminal) throw new Error('Terminal unavailable');
			const result = await downloadFileBlob(terminal.url, terminal.key, path, chatId || undefined);
			if (!result) throw new Error('Unable to read model file');
			modelData = await result.blob.arrayBuffer();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			modelData = null;
		} finally {
			loading = false;
		}
	}

	async function downloadOriginal() {
		if (!terminal) return;
		const result = await downloadFileBlob(terminal.url, terminal.key, path, chatId || undefined);
		if (!result) return;
		const url = URL.createObjectURL(result.blob);
		const anchor = document.createElement('a');
		anchor.href = url;
		anchor.download = result.filename || name;
		anchor.click();
		URL.revokeObjectURL(url);
	}

	onDestroy(() => {
		modelData = null;
	});
</script>

{#if !model}
	<TerminalOutputFile {item} {chatId} />
{:else}
	<div class="my-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-white/10 dark:bg-gray-950/20">
		<div class="flex h-8 items-center border-b border-gray-100 px-2.5 dark:border-white/10">
			<button type="button" class="min-w-0 flex-1 truncate text-left text-xs font-medium" on:click={() => (expanded = !expanded)}>{name}</button>
			<span class="mr-2 rounded bg-gray-100 px-1.5 py-0.5 text-[0.625rem] uppercase text-gray-500 dark:bg-gray-800">{fileExtension(name)}</span>
			<button type="button" class="rounded px-2 py-1 text-[0.6875rem] text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800" on:click={downloadOriginal}>Download</button>
		</div>
		{#if expanded}
			<div class="h-96 max-h-[70vh] min-h-72 resize-y overflow-hidden bg-gray-50 dark:bg-gray-950">
				{#if loading}
					<div class="flex h-full items-center justify-center text-xs text-gray-500">Loading 3D model…</div>
				{:else if error}
					<div class="flex h-full items-center justify-center p-5 text-xs text-red-500">{error}</div>
				{:else if modelData}
					<Model3DPreview filename={name} data={modelData} />
				{/if}
			</div>
		{/if}
	</div>
{/if}
