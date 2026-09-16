<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import {
		modelBounds,
		parseModel3d,
		trianglesToAsciiStl,
		type Triangle3D,
		type Vec3
	} from '$lib/utils/model3d';

	export let filename = 'model.stl';
	export let data: ArrayBuffer | string | null = null;
	export let allowExport = true;

	let canvas: HTMLCanvasElement | null = null;
	let container: HTMLDivElement | null = null;
	let triangles: Triangle3D[] = [];
	let error = '';
	let yaw = -0.55;
	let pitch = 0.35;
	let zoom = 1;
	let dragging = false;
	let lastX = 0;
	let lastY = 0;
	let resizeObserver: ResizeObserver | null = null;

	const rotate = (v: Vec3, center: Vec3): Vec3 => {
		const x = v[0] - center[0];
		const y = v[1] - center[1];
		const z = v[2] - center[2];
		const cy = Math.cos(yaw);
		const sy = Math.sin(yaw);
		const x1 = x * cy + z * sy;
		const z1 = -x * sy + z * cy;
		const cp = Math.cos(pitch);
		const sp = Math.sin(pitch);
		const y1 = y * cp - z1 * sp;
		const z2 = y * sp + z1 * cp;
		return [x1, y1, z2];
	};

	function draw() {
		if (!canvas || !container) return;
		const rect = container.getBoundingClientRect();
		const dpr = Math.min(window.devicePixelRatio || 1, 2);
		const width = Math.max(1, Math.floor(rect.width));
		const height = Math.max(1, Math.floor(rect.height));
		canvas.width = Math.floor(width * dpr);
		canvas.height = Math.floor(height * dpr);
		canvas.style.width = `${width}px`;
		canvas.style.height = `${height}px`;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx.clearRect(0, 0, width, height);
		if (!triangles.length) return;

		const { center, radius } = modelBounds(triangles);
		const scale = (Math.min(width, height) * 0.39 * zoom) / radius;
		const transformed = triangles.map((triangle) => {
			const points = triangle.map((vertex) => rotate(vertex, center)) as Triangle3D;
			return { points, depth: (points[0][2] + points[1][2] + points[2][2]) / 3 };
		});
		transformed.sort((a, b) => a.depth - b.depth);

		const dark = document.documentElement.classList.contains('dark');
		for (const { points } of transformed) {
			const [a, b, c] = points;
			const ab: Vec3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
			const ac: Vec3 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
			const nz = ab[0] * ac[1] - ab[1] * ac[0];
			const shade = Math.max(0.12, Math.min(0.88, 0.48 + nz / (radius * radius * 8)));
			const base = dark ? Math.round(90 + shade * 100) : Math.round(225 - shade * 72);
			ctx.beginPath();
			ctx.moveTo(width / 2 + a[0] * scale, height / 2 - a[1] * scale);
			ctx.lineTo(width / 2 + b[0] * scale, height / 2 - b[1] * scale);
			ctx.lineTo(width / 2 + c[0] * scale, height / 2 - c[1] * scale);
			ctx.closePath();
			ctx.fillStyle = `rgb(${base}, ${base}, ${base})`;
			ctx.fill();
			ctx.strokeStyle = dark ? 'rgba(255,255,255,.18)' : 'rgba(0,0,0,.16)';
			ctx.lineWidth = 0.65;
			ctx.stroke();
		}
	}

	$: if (data !== null) {
		try {
			triangles = parseModel3d(filename, data);
			error = triangles.length ? '' : 'No triangles were found in this model.';
		} catch (e) {
			triangles = [];
			error = e instanceof Error ? e.message : 'Unable to parse this 3D model.';
		}
		queueMicrotask(draw);
	}

	const resetView = () => {
		yaw = -0.55;
		pitch = 0.35;
		zoom = 1;
		draw();
	};

	const exportStl = () => {
		if (!triangles.length) return;
		const baseName = filename.replace(/\.[^.]+$/, '') || 'model';
		const blob = new Blob([trianglesToAsciiStl(baseName, triangles)], {
			type: 'model/stl'
		});
		const url = URL.createObjectURL(blob);
		const anchor = document.createElement('a');
		anchor.href = url;
		anchor.download = `${baseName}.stl`;
		anchor.click();
		URL.revokeObjectURL(url);
	};

	const pointerDown = (event: PointerEvent) => {
		dragging = true;
		lastX = event.clientX;
		lastY = event.clientY;
		canvas?.setPointerCapture(event.pointerId);
	};
	const pointerMove = (event: PointerEvent) => {
		if (!dragging) return;
		yaw += (event.clientX - lastX) * 0.009;
		pitch = Math.max(-1.45, Math.min(1.45, pitch + (event.clientY - lastY) * 0.009));
		lastX = event.clientX;
		lastY = event.clientY;
		draw();
	};
	const pointerUp = () => {
		dragging = false;
	};
	const wheel = (event: WheelEvent) => {
		event.preventDefault();
		zoom = Math.max(0.25, Math.min(6, zoom * Math.exp(-event.deltaY * 0.0012)));
		draw();
	};

	onMount(() => {
		resizeObserver = new ResizeObserver(draw);
		if (container) resizeObserver.observe(container);
		draw();
	});

	onDestroy(() => resizeObserver?.disconnect());
</script>

<div
	class="custom-model-preview relative flex h-full min-h-72 w-full flex-col overflow-hidden rounded-xl"
>
	<div
		class="flex h-9 shrink-0 items-center justify-between border-b border-black/5 px-3 dark:border-white/10"
	>
		<div class="min-w-0 truncate text-xs text-gray-600 dark:text-gray-300">
			{filename}
			{#if triangles.length}
				<span class="text-gray-400">· {triangles.length.toLocaleString()} triangles</span>
			{/if}
		</div>
		<div class="flex items-center gap-1.5">
			<button
				type="button"
				class="rounded-lg px-2 py-1 text-xs text-gray-500 hover:bg-black/5 dark:hover:bg-white/10"
				on:click={resetView}
			>
				Reset view
			</button>
			{#if allowExport && triangles.length}
				<button
					type="button"
					class="rounded-lg bg-black px-2.5 py-1 text-xs text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200"
					on:click={exportStl}
				>
					Export STL
				</button>
			{/if}
		</div>
	</div>

	<div class="relative min-h-0 flex-1 touch-none select-none" bind:this={container}>
		<canvas
			bind:this={canvas}
			class="absolute inset-0 cursor-grab active:cursor-grabbing"
			on:pointerdown={pointerDown}
			on:pointermove={pointerMove}
			on:pointerup={pointerUp}
			on:pointercancel={pointerUp}
			on:wheel={wheel}
		></canvas>
		{#if error}
			<div
				class="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-gray-500"
			>
				{error}
			</div>
		{/if}
		{#if triangles.length}
			<div
				class="pointer-events-none absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full bg-white/80 px-2.5 py-1 text-[0.65rem] text-gray-500 shadow-sm backdrop-blur dark:bg-black/60 dark:text-gray-400"
			>
				Drag to rotate · wheel/pinch to zoom
			</div>
		{/if}
	</div>
</div>