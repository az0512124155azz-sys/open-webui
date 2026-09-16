<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		disablePlugin,
		enablePlugin,
		getPluginPermissions,
		getPlugins,
		uninstallPlugin
	} from '$lib/apis/plugins';

	let loading = true;
	let plugins: any[] = [];
	let permissions: any[] = [];
	let selected: any = null;
	let busyId = '';

	const token = () => localStorage.token ?? '';

	const refresh = async () => {
		loading = true;
		try {
			const [pluginRes, permissionRes] = await Promise.all([
				getPlugins(token()),
				getPluginPermissions(token())
			]);
			plugins = pluginRes?.plugins ?? [];
			permissions = permissionRes?.permissions ?? [];
		} catch (error) {
			console.error(error);
			toast.error('Failed to load plugins');
		} finally {
			loading = false;
		}
	};

	const toggle = async (plugin: any) => {
		busyId = plugin.id;
		try {
			if (plugin.is_active) await disablePlugin(token(), plugin.id);
			else await enablePlugin(token(), plugin.id);
			await refresh();
		} catch (error) {
			toast.error(String(error));
		} finally {
			busyId = '';
		}
	};

	const remove = async (plugin: any) => {
		if (!confirm(`Uninstall plugin ${plugin.name}?`)) return;
		busyId = plugin.id;
		try {
			await uninstallPlugin(token(), plugin.id);
			selected = null;
			await refresh();
			toast.success('Plugin uninstalled');
		} catch (error) {
			toast.error(String(error));
		} finally {
			busyId = '';
		}
	};

	onMount(refresh);
</script>

<div class="space-y-4">
	<div>
		<h2 class="text-sm font-medium text-gray-900 dark:text-white">Plugins</h2>
		<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
			Registry on top of Open WebUI Functions. Permissions are explicit; broken plugins are rejected on
			install.
		</p>
	</div>

	{#if loading}
		<div class="text-xs text-gray-500">Loading plugins…</div>
	{:else if !plugins.length}
		<div
			class="rounded-xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-white/10"
		>
			No plugins installed yet.
		</div>
	{:else}
		<div class="space-y-2">
			{#each plugins as plugin}
				<button
					type="button"
					class="w-full rounded-xl border border-gray-100 p-3 text-left dark:border-white/[0.06]"
					on:click={() => (selected = plugin)}
				>
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="truncate text-sm font-medium text-gray-900 dark:text-white">
								{plugin.name}
							</div>
							<div class="mt-0.5 text-xs text-gray-500">
								{plugin.id} · v{plugin.version || '—'} · {plugin.status}
							</div>
						</div>
						<span class="text-[10px]">{plugin.is_active ? 'enabled' : 'disabled'}</span>
					</div>
				</button>
			{/each}
		</div>
	{/if}

	{#if selected}
		<div class="rounded-xl border border-gray-100 p-4 dark:border-white/[0.06]">
			<div class="text-sm font-medium text-gray-900 dark:text-white">{selected.name}</div>
			<div class="mt-1 text-xs text-gray-500">{selected.description || 'No description'}</div>
			<div class="mt-3 text-xs">Permissions: {(selected.permissions || []).join(', ') || 'none'}</div>
			<div class="mt-4 flex gap-2">
				<button
					type="button"
					class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs dark:border-white/10"
					disabled={busyId === selected.id}
					on:click={() => toggle(selected)}
					>{selected.is_active ? 'Disable' : 'Enable'}</button
				>
				<button
					type="button"
					class="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-600"
					disabled={busyId === selected.id}
					on:click={() => remove(selected)}>Uninstall</button
				>
			</div>
		</div>
	{/if}

	{#if permissions.length}
		<details class="rounded-xl border border-gray-100 p-3 text-xs dark:border-white/[0.06]">
			<summary class="cursor-pointer font-medium">Permission catalog</summary>
			<ul class="mt-2 space-y-1 text-gray-500">
				{#each permissions as permission}
					<li>{permission.id} — {permission.description}</li>
				{/each}
			</ul>
		</details>
	{/if}
</div>
