<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getUserValvesById, updateUserValvesById } from '$lib/apis/functions';

	const FUNCTION_ID = 'automatic_hebrew_translation';

	let loading = true;
	let enabled = false;
	let engine: 'libretranslate' | 'ollama' = 'libretranslate';
	let libretranslateUrl = 'http://libretranslate:5000';
	let ollamaModel = 'qwen2.5:3b';
	let showOriginal = true;
	let applyTo: 'both' | 'user' | 'assistant' = 'both';

	const token = () => localStorage.token ?? '';

	const load = async () => {
		loading = true;
		try {
			const values = (await getUserValvesById(token(), FUNCTION_ID)) ?? {};
			enabled = values.enabled ?? false;
			engine = values.engine ?? 'libretranslate';
			libretranslateUrl = values.libretranslate_url ?? 'http://libretranslate:5000';
			ollamaModel = values.ollama_model ?? 'qwen2.5:3b';
			showOriginal = values.show_original ?? true;
			applyTo = values.apply_to ?? 'both';
		} catch (error) {
			console.error(error);
			toast.error('Failed to load translation settings');
		} finally {
			loading = false;
		}
	};

	export const save = async () => {
		if (loading) return;
		try {
			await updateUserValvesById(token(), FUNCTION_ID, {
				enabled,
				engine,
				libretranslate_url: libretranslateUrl.trim() || 'http://libretranslate:5000',
				ollama_model: ollamaModel.trim() || 'qwen2.5:3b',
				show_original: showOriginal,
				apply_to: applyTo
			});
		} catch (error) {
			console.error(error);
			toast.error('Failed to save translation settings');
			throw error;
		}
	};

	onMount(load);
</script>

<section class="mt-6 border-t border-gray-100 pt-5 dark:border-white/10">
	<div class="mb-4">
		<h3 class="text-sm font-medium text-gray-900 dark:text-white">Translation</h3>
		<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
			Automatically translate Hebrew prompts to English for the model and translate English
			responses back to Hebrew. Translation stays on your local machine.
		</p>
	</div>

	{#if loading}
		<div class="py-3 text-xs text-gray-500">Loading translation settings…</div>
	{:else}
		<div class="space-y-4">
			<label class="flex items-start justify-between gap-4">
				<div>
					<div class="text-sm text-gray-800 dark:text-gray-200">
						Enable automatic Hebrew translation
					</div>
					<div class="mt-0.5 text-xs text-gray-500">
						Applies transparently before and/or after model inference.
					</div>
				</div>
				<input class="mt-1 h-4 w-4" type="checkbox" bind:checked={enabled} />
			</label>

			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<label class="block">
					<span class="mb-1 block text-xs text-gray-500">Translation engine</span>
					<select
						class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none dark:border-white/10"
						bind:value={engine}
					>
						<option value="libretranslate">LibreTranslate</option>
						<option value="ollama">Ollama model</option>
					</select>
				</label>

				<label class="block">
					<span class="mb-1 block text-xs text-gray-500">Apply translation to</span>
					<select
						class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none dark:border-white/10"
						bind:value={applyTo}
					>
						<option value="both">Both directions</option>
						<option value="user">User messages only</option>
						<option value="assistant">Model responses only</option>
					</select>
				</label>
			</div>

			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">LibreTranslate URL</span>
				<input
					class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10"
					type="text"
					bind:value={libretranslateUrl}
					placeholder="http://libretranslate:5000"
				/>
			</label>

			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">Ollama translation model</span>
				<input
					class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10"
					type="text"
					bind:value={ollamaModel}
					placeholder="qwen2.5:3b"
				/>
			</label>

			<label class="flex items-start justify-between gap-4">
				<div>
					<div class="text-sm text-gray-800 dark:text-gray-200">
						Show original text alongside translation
					</div>
					<div class="mt-0.5 text-xs text-gray-500">
						Adds the original English response in a collapsed “Show original” section.
					</div>
				</div>
				<input class="mt-1 h-4 w-4" type="checkbox" bind:checked={showOriginal} />
			</label>
		</div>
	{/if}
</section>
