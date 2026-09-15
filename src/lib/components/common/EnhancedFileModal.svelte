<script lang="ts">
	import { getContext, onDestroy } from 'svelte';
	import DOMPurify from 'dompurify';
	import Modal from './Modal.svelte';
	import XMark from '../icons/XMark.svelte';
	import Spinner from './Spinner.svelte';
	import FilePreview from '$lib/components/chat/FileNav/FilePreview.svelte';
	import Model3DPreview from './Model3DPreview.svelte';
	import { getFileContentById } from '$lib/apis/files';
	import { fileExtension, isModel3dFile } from '$lib/utils/model3d';

	const i18n = getContext('i18n');

	export let item: any;
	export let show = false;

	let loading = false;
	let error = '';
	let loadedKey = '';
	let rawData: ArrayBuffer | null = null;
	let modelData: ArrayBuffer | null = null;
	let imageUrl: string | null = null;
	let videoUrl: string | null = null;
	let audioUrl: string | null = null;
	let pdfData: ArrayBuffer | null = null;
	let sqliteData: ArrayBuffer | null = null;
	let docxData: ArrayBuffer | null = null;
	let textContent: string | null = null;
	let officeHtml: string | null = null;
	let officeSlides: string[] | null = null;
	let excelWorkbook: any = null;
	let excelSheetNames: string[] = [];
	let selectedExcelSheet = '';
	let objectUrls: string[] = [];

	$: filename = item?.name || 'file';
	$: ext = fileExtension(filename);
	$: mime = item?.meta?.content_type || item?.content_type || 'application/octet-stream';
	$: key = `${item?.id ?? ''}:${filename}:${mime}`;
	$: if (show && item?.id && key !== loadedKey && !loading) void loadPreview(key);

	const imageExts = new Set([
		'png',
		'jpg',
		'jpeg',
		'gif',
		'webp',
		'bmp',
		'ico',
		'avif',
		'svg'
	]);
	const videoExts = new Set(['mp4', 'webm', 'mov', 'ogv', 'm4v']);
	const audioExts = new Set(['mp3', 'wav', 'ogg', 'oga', 'flac', 'm4a', 'aac', 'opus']);
	const sqliteExts = new Set(['db', 'sqlite', 'sqlite3', 'db3']);
	const textExts = new Set([
		'txt',
		'log',
		'md',
		'markdown',
		'mdx',
		'csv',
		'tsv',
		'json',
		'jsonc',
		'jsonl',
		'json5',
		'html',
		'htm',
		'xml',
		'yaml',
		'yml',
		'toml',
		'ini',
		'env',
		'py',
		'js',
		'ts',
		'tsx',
		'jsx',
		'java',
		'kt',
		'kts',
		'c',
		'h',
		'cpp',
		'hpp',
		'cs',
		'go',
		'rs',
		'php',
		'rb',
		'sh',
		'bash',
		'zsh',
		'fish',
		'sql',
		'css',
		'scss',
		'less',
		'svelte',
		'vue',
		'ipynb'
	]);

	function clearPreview() {
		for (const url of objectUrls) URL.revokeObjectURL(url);
		objectUrls = [];
		rawData = null;
		modelData = null;
		imageUrl = null;
		videoUrl = null;
		audioUrl = null;
		pdfData = null;
		sqliteData = null;
		docxData = null;
		textContent = null;
		officeHtml = null;
		officeSlides = null;
		excelWorkbook = null;
		excelSheetNames = [];
		selectedExcelSheet = '';
	}

	function makeUrl(data: ArrayBuffer, contentType: string) {
		const url = URL.createObjectURL(new Blob([data], { type: contentType }));
		objectUrls = [...objectUrls, url];
		return url;
	}

	async function loadExcelSheet(sheet: string) {
		if (!excelWorkbook) return;
		selectedExcelSheet = sheet;
		const { excelToTable } = await import('$lib/utils/excelToTable');
		const result = await excelToTable(excelWorkbook.Sheets[sheet]);
		officeHtml = DOMPurify.sanitize(result.html);
	}

	async function loadPreview(nextKey: string) {
		loadedKey = nextKey;
		loading = true;
		error = '';
		clearPreview();
		try {
			const data = await getFileContentById(item.id);
			if (!data) throw new Error('Unable to load file content.');
			rawData = data;

			if (isModel3dFile(filename)) {
				modelData = data;
			} else if (mime.startsWith('image/') || imageExts.has(ext)) {
				imageUrl = makeUrl(
					data,
					mime.startsWith('image/') ? mime : `image/${ext === 'svg' ? 'svg+xml' : ext}`
				);
			} else if (mime.startsWith('video/') || videoExts.has(ext)) {
				videoUrl = makeUrl(data, mime.startsWith('video/') ? mime : `video/${ext}`);
			} else if (mime.startsWith('audio/') || audioExts.has(ext)) {
				audioUrl = makeUrl(data, mime.startsWith('audio/') ? mime : `audio/${ext}`);
			} else if (mime === 'application/pdf' || ext === 'pdf') {
				pdfData = data;
			} else if (sqliteExts.has(ext)) {
				sqliteData = data;
			} else if (ext === 'docx') {
				docxData = data;
			} else if (ext === 'xlsx' || ext === 'xls') {
				const XLSX = await import('xlsx');
				excelWorkbook = XLSX.read(new Uint8Array(data), { type: 'array' });
				excelSheetNames = excelWorkbook.SheetNames;
				if (excelSheetNames.length) await loadExcelSheet(excelSheetNames[0]);
			} else if (ext === 'pptx') {
				const { pptxToImages } = await import('$lib/utils/pptxToHtml');
				officeSlides = (await pptxToImages(data)).images;
			} else if (mime.startsWith('text/') || textExts.has(ext)) {
				textContent = new TextDecoder('utf-8', { fatal: false }).decode(data);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function download() {
		try {
			const data = rawData ?? (await getFileContentById(item.id));
			if (!data) throw new Error('Unable to download file content.');
			const url = URL.createObjectURL(new Blob([data], { type: mime }));
			const anchor = document.createElement('a');
			anchor.href = url;
			anchor.download = filename;
			anchor.click();
			URL.revokeObjectURL(url);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	onDestroy(clearPreview);
</script>

<Modal bind:show size="lg">
	<div
		class="flex h-[78vh] min-h-[28rem] w-full flex-col overflow-hidden p-3 text-gray-700 dark:text-gray-200"
	>
		<div class="flex h-10 shrink-0 items-center justify-between gap-3 px-1 pb-2">
			<div class="min-w-0">
				<div class="truncate text-sm font-medium">{filename}</div>
				<div class="truncate text-[0.6875rem] text-gray-400">{mime}</div>
			</div>
			<div class="flex shrink-0 items-center gap-1.5">
				<button
					type="button"
					class="rounded-lg border border-gray-200 px-2.5 py-1 text-xs hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
					on:click={download}
				>{$i18n.t('Download')}</button
				>
				<button
					type="button"
					class="flex size-7 items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
					on:click={() => (show = false)}
					aria-label={$i18n.t('Close')}
				><XMark className="size-4" /></button
				>
			</div>
		</div>

		<div class="custom-file-preview min-h-0 flex-1 overflow-hidden rounded-xl">
			{#if loading}
				<div class="flex h-full items-center justify-center"><Spinner className="size-5" /></div>
			{:else if error}
				<div
					class="flex h-full items-center justify-center p-8 text-center text-sm text-red-500"
				>
					{error}
				</div>
			{:else if modelData !== null}
				<Model3DPreview {filename} data={modelData} />
			{:else if imageUrl !== null || videoUrl !== null || audioUrl !== null || pdfData !== null || sqliteData !== null || docxData !== null || textContent !== null || officeHtml !== null || officeSlides !== null}
				<FilePreview
					selectedFile={filename}
					fileLoading={false}
					fileImageUrl={imageUrl}
					fileVideoUrl={videoUrl}
					fileAudioUrl={audioUrl}
					filePdfData={pdfData}
					fileSqliteData={sqliteData}
					fileDocxData={docxData}
					fileContent={textContent}
					fileOfficeHtml={officeHtml}
					fileOfficeSlides={officeSlides}
					{excelSheetNames}
					{selectedExcelSheet}
					onSheetChange={loadExcelSheet}
					readOnly={true}
				/>
			{:else}
				<div
					class="flex h-full flex-col items-center justify-center gap-2 p-8 text-center text-sm text-gray-500"
				>
					<div>{$i18n.t('No preview available for this file type.')}</div>
					<button
						type="button"
						class="rounded-lg bg-black px-3 py-1.5 text-xs text-white dark:bg-white dark:text-black"
						on:click={download}
					>{$i18n.t('Download')}</button
					>
				</div>
			{/if}
		</div>
	</div>
</Modal>
