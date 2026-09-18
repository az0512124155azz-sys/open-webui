<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { getFileContentById } from '$lib/apis/files';
	import { formatFileSize } from '$lib/utils';
	import { settings, showFileNavPath } from '$lib/stores';

	import FileItemModal from './FileItemModal.svelte';
	import EnhancedFileModal from './EnhancedFileModal.svelte';
	import Spinner from './Spinner.svelte';
	import Tooltip from './Tooltip.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import DocumentPage from '../icons/DocumentPage.svelte';
	import Database from '../icons/Database.svelte';
	import PageEdit from '../icons/PageEdit.svelte';
	import ChatBubble from '../icons/ChatBubble.svelte';
	import Folder from '../icons/Folder.svelte';

	const i18n: any = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let className = 'w-60';
	export let colorClassName =
		'bg-white dark:bg-gray-850 border border-gray-50/30 dark:border-gray-800/30';
	export let url: string | null = null;
	export let dismissible = false;
	export let modal = false;
	export let loading = false;
	export let item: any = null;
	export let edit = false;
	export let small = false;
	export let name: string;
	export let type: string;
	export let size: number;

	let showModal = false;
	$: enhancedFile = item?.type === 'file' && Boolean(item?.id);
	$: typeLabel =
		type === 'file' || type === 'filesystem'
			? $i18n.t('File')
			: type === 'note'
				? $i18n.t('Note')
				: type === 'doc'
					? $i18n.t('Document')
					: type === 'collection'
						? $i18n.t('Collection')
						: type;

	const decodeString = (str: string) => {
		try {
			return decodeURIComponent(str);
		} catch {
			return str;
		}
	};

	const openItem = async () => {
		const filesystemPath = item?.type === 'filesystem' ? (item.path ?? item.url ?? item.id) : null;
		if (filesystemPath) {
			showFileNavPath.set(filesystemPath);
		} else if (
			enhancedFile ||
			item?.file?.data?.content ||
			item?.type === 'file' ||
			item?.content ||
			modal
		) {
			showModal = !showModal;
		} else if (url) {
			if (type === 'file') {
				window
					.open(
						url.startsWith('http')
							? `${url}/content`
							: `${WEBUI_API_BASE_URL}/files/${url}/content`,
						'_blank'
					)
					?.focus();
			} else {
				window.open(url, '_blank')?.focus();
			}
		}
		dispatch('click');
	};

	const downloadItem = async (event: MouseEvent) => {
		event.stopPropagation();
		const id = item?.id ?? item?.tempId ?? (type === 'file' ? url : null);
		if (!id) return;
		try {
			const data = await getFileContentById(id);
			if (!data) throw new Error('Unable to download file content.');
			const blobUrl = URL.createObjectURL(
				new Blob([data], {
					type: item?.meta?.content_type ?? item?.content_type ?? 'application/octet-stream'
				})
			);
			const anchor = document.createElement('a');
			anchor.href = blobUrl;
			anchor.download = name || item?.name || 'download';
			anchor.click();
			URL.revokeObjectURL(blobUrl);
		} catch {
			const direct = item?.url ?? url;
			if (direct)
				window
					.open(
						direct.startsWith('http') ? direct : `${WEBUI_API_BASE_URL}/files/${direct}/content`,
						'_blank'
					)
					?.focus();
		}
	};
</script>

{#if item}
	{#if enhancedFile}
		<EnhancedFileModal bind:show={showModal} bind:item />
	{:else}
		<FileItemModal bind:show={showModal} bind:item {edit} />
	{/if}
{/if}

<div class="relative group {className}">
	<button
		class="w-full flex items-center {colorClassName} {small
			? 'h-8 gap-1.5 rounded-xl px-2.5 text-[0.8125rem] leading-5'
			: 'gap-1 rounded-2xl p-1.5'} text-left"
		type="button"
		on:click={openItem}
	>
		{#if !small}
			<div
				class="size-10 shrink-0 flex justify-center items-center bg-black/20 dark:bg-white/10 text-white rounded-xl"
			>
				{#if !loading}
					<DocumentPage className="size-4.5" />
				{:else}
					<Spinner />
				{/if}
			</div>
		{:else}
			<div class="shrink-0 text-gray-500 dark:text-gray-400">
				{#if !loading}
					<Tooltip
						content={type === 'collection'
							? $i18n.t('Collection')
							: type === 'note'
								? $i18n.t('Note')
								: type === 'chat'
									? $i18n.t('Chat')
									: type === 'file' || type === 'filesystem'
										? $i18n.t('File')
										: $i18n.t('Document')}
						placement="top"
					>
						{#if type === 'collection'}
							<Database className="size-3.5" />
						{:else if type === 'note'}
							<PageEdit className="size-3.5" />
						{:else if type === 'chat'}
							<ChatBubble className="size-3.5" />
						{:else if type === 'folder'}
							<Folder className="size-3.5" />
						{:else}
							<DocumentPage className="size-3.5" />
						{/if}
					</Tooltip>
				{:else}
					<Spinner className="size-3.5" />
				{/if}
			</div>
		{/if}

		{#if !small}
			<div class="flex flex-col justify-center -space-y-0.5 px-2.5 w-full min-w-0">
				<div class="dark:text-gray-100 text-sm font-normal line-clamp-1 mb-1 pr-7">
					{decodeString(name)}
				</div>
				<div
					class="flex justify-between text-xs line-clamp-1 {($settings?.highContrastMode ?? false)
						? 'text-gray-800 dark:text-gray-100'
						: 'text-gray-500'}"
				>
					<span>{typeLabel}</span>
					{#if size}<span class="capitalize">{formatFileSize(size)}</span>{/if}
				</div>
			</div>
		{:else}
			<Tooltip
				content={decodeString(name)}
				className="flex min-w-0 flex-1 overflow-hidden"
				placement="top-start"
			>
				<div class="flex min-w-0 flex-1 items-center justify-between dark:text-gray-100">
					<div class="min-w-0 flex-1 truncate pr-8 font-normal">{decodeString(name)}</div>
					<div class="max-w-[35%] shrink-0 truncate text-[0.6875rem] capitalize text-gray-500">
						{size ? formatFileSize(size) : type}
					</div>
				</div>
			</Tooltip>
		{/if}
	</button>

	{#if type === 'file' && (item?.id || url) && !loading && !edit}
		<button
			type="button"
			class="absolute right-1.5 top-1/2 flex size-6 -translate-y-1/2 items-center justify-center rounded-lg text-gray-400 opacity-0 transition hover:bg-black/5 hover:text-gray-700 group-hover:opacity-100 focus:opacity-100 dark:hover:bg-white/10 dark:hover:text-gray-200"
			on:click={downloadItem}
			aria-label={$i18n.t('Download')}
			title={$i18n.t('Download')}
		>
			<svg
				viewBox="0 0 20 20"
				fill="none"
				stroke="currentColor"
				class="size-3.5"
				stroke-width="1.6"
				aria-hidden="true"
			>
				<path
					d="M10 2.5v9m0 0 3-3m-3 3-3-3M4 14.5v2h12v-2"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
		</button>
	{/if}

	{#if dismissible}
		<div class="absolute -top-1 -right-1">
			<button
				aria-label={$i18n.t('Remove File')}
				class="bg-white text-black border border-gray-50 rounded-full {($settings?.highContrastMode ??
				false)
					? ''
					: 'hover-reveal transition'}"
				type="button"
				on:click|stopPropagation={() => dispatch('dismiss')}
			>
				<XMark className="size-4" />
			</button>
		</div>
	{/if}
</div>
