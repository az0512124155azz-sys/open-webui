// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
}

declare module 'svelte' {
	/**
	 * The root layout installs the application i18n store under this stable
	 * context key. Keeping the overload here gives every consumer the same
	 * concrete store contract instead of Svelte 5's safe `unknown` default.
	 */
	export function getContext(key: 'i18n'): typeof import('$lib/i18n').default;
}

export {};
