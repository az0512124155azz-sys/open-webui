<script lang="ts">
	import { onMount } from 'svelte';
	import { config } from '$lib/stores';
	import { goto } from '$app/navigation';
	import Plugins from '$lib/components/admin/Settings/Plugins.svelte';

	onMount(async () => {
		if ($config && $config?.features?.enable_plugins === false) {
			await goto('/admin', { replaceState: true });
		}
	});
</script>

<div class="max-w-3xl px-4 py-6">
	<Plugins />
</div>
