/**
 * Reusable state management for CreativeModal component
 *
 * @example
 * ```svelte
 * <script>
 *   import { createCreativeModal } from '$lib/stores/creativeModal.svelte';
 *   const creativeModal = createCreativeModal();
 * </script>
 *
 * <button onclick={() => creativeModal.open(rawUrl, 'My Creative')}>
 *   View Creative
 * </button>
 *
 * <CreativeModal
 *   bind:isOpen={creativeModal.isOpen}
 *   creativeUrl={creativeModal.creativeUrl}
 *   title={creativeModal.title}
 * />
 * ```
 */
export function createCreativeModal() {
	let isOpen = $state(false);
	let creativeUrl = $state('');
	let title = $state('');

	return {
		get isOpen() {
			return isOpen;
		},
		set isOpen(value: boolean) {
			isOpen = value;
		},
		get creativeUrl() {
			return creativeUrl;
		},
		get title() {
			return title;
		},

		/**
		 * Open modal with a creative
		 * @param rawUrl - Pre-built CDN URL for the raw creative file
		 * @param creativeTitle - Display title for the modal
		 */
		open(rawUrl: string, creativeTitle: string) {
			creativeUrl = rawUrl;
			title = `${creativeTitle} - Ad Creative`;
			isOpen = true;
		},

		/**
		 * Close the modal
		 */
		close() {
			isOpen = false;
		}
	};
}
