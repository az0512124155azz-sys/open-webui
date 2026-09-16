<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { generateSkillDraft } from '$lib/apis/skills/generate';
	import { createNewSkill } from '$lib/apis/skills';

	const dispatch = createEventDispatcher();

	let prompt = '';
	let model = 'qwen2.5:3b';
	let generating = false;
	let saving = false;
	let draft: any = null;
	let enableAfterSave = false;

	const token = () => localStorage.token ?? '';

	const generate = async () => {
		if (prompt.trim().length < 8) {
			toast.error('Describe the skill in more detail');
			return;
		}
		generating = true;
		draft = null;
		try {
			const result = await generateSkillDraft(token(), {
				prompt: prompt.trim(),
				model: model.trim() || undefined,
				language: 'he'
			});
			draft = { ...(result?.draft ?? {}), is_active: false };
			toast.success('Draft ready — review before saving');
		} catch (error) {
			toast.error(String(error));
		} finally {
			generating = false;
		}
	};

	const save = async () => {
		if (!draft?.id || !draft?.content) {
			toast.error('Draft is incomplete');
			return;
		}
		saving = true;
		try {
			const payload = {
				id: draft.id,
				name: draft.name,
				description: draft.description || '',
				content: draft.content,
				is_active: Boolean(enableAfterSave),
				meta: {
					examples: draft.examples || [],
					source: 'ai-draft',
					source_prompt: draft.source_prompt || prompt
				},
				access_grants: []
			};
			const res = await createNewSkill(token(), payload);
			if (!res) throw new Error('Save failed');
			toast.success(enableAfterSave ? 'Skill saved and enabled' : 'Skill saved (disabled)');
			dispatch('saved', res);
		} catch (error) {
			toast.error(String(error));
		} finally {
			saving = false;
		}
	};
</script>

<section class="rounded-2xl border border-gray-100 p-4 dark:border-white/[0.06]">
	<div class="mb-3">
		<h3 class="text-sm font-medium text-gray-900 dark:text-white">Create Skill with AI</h3>
		<p class="mt-1 text-xs text-gray-500">
			Local model drafts a skill. Nothing is saved or enabled until you confirm.
		</p>
	</div>

	<label class="mb-3 block">
		<span class="mb-1 block text-xs text-gray-500">What should this skill do?</span>
		<textarea
			class="min-h-24 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none dark:border-white/10"
			bind:value={prompt}
			placeholder="לדוגמה: תיצור לי Skill שעוזר לתקן פרויקטי Android"
		/>
	</label>

	<label class="mb-3 block">
		<span class="mb-1 block text-xs text-gray-500">Local Ollama model</span>
		<input
			class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-none dark:border-white/10"
			bind:value={model}
			placeholder="qwen2.5:3b"
		/>
	</label>

	<button
		type="button"
		class="rounded-xl bg-gray-900 px-3 py-2 text-sm text-white disabled:opacity-50 dark:bg-white dark:text-gray-900"
		disabled={generating}
		on:click={generate}
	>
		{generating ? 'Generating draft…' : 'Generate draft'}
	</button>

	{#if draft}
		<div class="mt-4 space-y-3 rounded-xl bg-gray-50 p-3 dark:bg-white/[0.03]">
			<div class="text-xs font-medium text-amber-700 dark:text-amber-200">
				Preview only — not saved yet
			</div>
			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">ID</span>
				<input
					class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
					bind:value={draft.id}
				/>
			</label>
			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">Name</span>
				<input
					class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
					bind:value={draft.name}
				/>
			</label>
			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">Description</span>
				<input
					class="w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
					bind:value={draft.description}
				/>
			</label>
			<label class="block">
				<span class="mb-1 block text-xs text-gray-500">Instructions</span>
				<textarea
					class="min-h-40 w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-sm dark:border-white/10"
					bind:value={draft.content}
				/>
			</label>
			<label class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
				<input type="checkbox" bind:checked={enableAfterSave} />
				Enable after save (optional)
			</label>
			<button
				type="button"
				class="rounded-xl bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50"
				disabled={saving}
				on:click={save}
			>
				{saving ? 'Saving…' : 'Save skill'}
			</button>
		</div>
	{/if}
</section>
