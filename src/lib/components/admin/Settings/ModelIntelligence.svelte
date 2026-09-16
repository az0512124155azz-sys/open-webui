<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		benchmarkModel,
		getConnectionHealth,
		getDuplicateModels,
		routeModels,
		warmupModels
	} from '$lib/apis/model-intelligence';

	let health: any = null;
	let duplicates: any = null;
	let routeResult: any = null;
	let routePrompt = '';
	let routeTask = '';
	let benchmarkModelId = '';
	let benchmarkResult: any = null;
	let warmupIds = '';
	let busy = '';

	const token = () => localStorage.token ?? '';

	const refresh = async () => {
		busy = 'health';
		try {
			health = await getConnectionHealth(token());
			duplicates = await getDuplicateModels(token());
		} catch (error) {
			toast.error(String(error));
		} finally {
			busy = '';
		}
	};

	const runRoute = async () => {
		busy = 'route';
		try {
			routeResult = await routeModels(token(), {
				prompt: routePrompt,
				task: routeTask || undefined,
				prefer_local: true,
				limit: 5
			});
		} catch (error) {
			toast.error(String(error));
		} finally {
			busy = '';
		}
	};

	const runBenchmark = async () => {
		if (!benchmarkModelId.trim()) {
			toast.error('Enter a model id');
			return;
		}
		busy = 'bench';
		try {
			benchmarkResult = await benchmarkModel(token(), { model: benchmarkModelId.trim() });
		} catch (error) {
			toast.error(String(error));
		} finally {
			busy = '';
		}
	};

	const runWarmup = async () => {
		const model_ids = warmupIds
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean);
		if (!model_ids.length) {
			toast.error('Enter model ids');
			return;
		}
		busy = 'warm';
		try {
			await warmupModels(token(), { model_ids, max_warm: 3, execute: true });
			toast.success('Warmup requested');
		} catch (error) {
			toast.error(String(error));
		} finally {
			busy = '';
		}
	};

	onMount(refresh);
</script>

<div class="space-y-5">
	<div>
		<h2 class="text-sm font-medium text-gray-900 dark:text-white">Model Intelligence</h2>
		<p class="mt-1 text-xs text-gray-500">
			Router, health, duplicates, warmup, local benchmarks. No automatic destructive actions.
		</p>
	</div>

	<section class="rounded-xl border border-gray-100 p-3 dark:border-white/[0.06]">
		<div class="mb-2 flex items-center justify-between">
			<div class="text-xs font-medium">Connection Health</div>
			<button class="text-xs text-gray-400" type="button" on:click={refresh} disabled={busy !== ''}
				>Refresh</button
			>
		</div>
		{#if health}
			<div class="text-sm font-medium capitalize">{health.status}</div>
			<ul class="mt-2 space-y-1 text-xs text-gray-500">
				{#each health.checks || [] as check}
					<li>{check.label} — {check.status}{#if check.latency_ms} ({check.latency_ms} ms){/if}</li>
				{/each}
			</ul>
		{/if}
	</section>

	<section class="rounded-xl border border-gray-100 p-3 dark:border-white/[0.06]">
		<div class="text-xs font-medium">Duplicate detector (diagnostic only)</div>
		{#if duplicates?.findings?.length}
			<ul class="mt-2 space-y-1 text-xs text-amber-700 dark:text-amber-200">
				{#each duplicates.findings as finding}
					<li>{finding.message}: {(finding.entries || []).join(', ')}</li>
				{/each}
			</ul>
		{:else}
			<div class="mt-2 text-xs text-gray-400">No duplicate groups detected</div>
		{/if}
	</section>

	<section class="space-y-2 rounded-xl border border-gray-100 p-3 dark:border-white/[0.06]">
		<div class="text-xs font-medium">Smart Model Router</div>
		<input
			class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
			placeholder="task: coding | reasoning | translation | vision | simple"
			bind:value={routeTask}
		/>
		<textarea
			class="min-h-16 w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
			placeholder="Prompt / task description"
			bind:value={routePrompt}
		/>
		<button
			type="button"
			class="rounded-lg bg-gray-900 px-3 py-1.5 text-xs text-white dark:bg-white dark:text-gray-900"
			disabled={busy === 'route'}
			on:click={runRoute}>Recommend models</button
		>
		{#if routeResult}
			<div class="text-xs text-gray-500">Task: {routeResult.task}</div>
			<ul class="text-xs">
				{#each routeResult.recommendations || [] as item}
					<li>{item.id || item.name} · score {item.route_score}</li>
				{/each}
			</ul>
		{/if}
	</section>

	<section class="space-y-2 rounded-xl border border-gray-100 p-3 dark:border-white/[0.06]">
		<div class="text-xs font-medium">Local benchmark</div>
		<input
			class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
			placeholder="model id e.g. qwen2.5:3b"
			bind:value={benchmarkModelId}
		/>
		<button
			type="button"
			class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs dark:border-white/10"
			disabled={busy === 'bench'}
			on:click={runBenchmark}>Run sample</button
		>
		{#if benchmarkResult}
			<div class="text-xs">
				{benchmarkResult.tokens_per_sec ?? '—'} tok/s · {benchmarkResult.elapsed_sec}s
			</div>
			<div class="text-[11px] text-gray-400">{benchmarkResult.disclaimer}</div>
		{/if}
	</section>

	<section class="space-y-2 rounded-xl border border-gray-100 p-3 dark:border-white/[0.06]">
		<div class="text-xs font-medium">Warmup manager</div>
		<input
			class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
			placeholder="model ids, comma-separated"
			bind:value={warmupIds}
		/>
		<button
			type="button"
			class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs dark:border-white/10"
			disabled={busy === 'warm'}
			on:click={runWarmup}>Warm selected (limit 3)</button
		>
	</section>
</div>
