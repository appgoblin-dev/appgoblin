<script lang="ts">
	export let creative: {
		md5_hash: string;
		file_extension: string;
		advertiser_store_id: string;
		advertiser_icon_url_100: string;
		advertiser_name?: string | null;
		publisher_count: number;
		first_seen: string;
		last_seen: string;
	};
	export let index: number;
	export let titlePrefix = 'Popular Creative';
	export let badgeLabel = 'Most Popular';
	export let compact = false;
	export let dense = false;
	export let onOpen: (rawUrl: string, title: string) => void;

	const mediaFill = dense && compact;
	const mediaAspectClass = mediaFill
		? 'flex-1 min-h-0'
		: dense
			? 'aspect-[4/3]'
			: compact
				? 'aspect-square'
				: 'aspect-video';
	const bodyPaddingClass = dense ? 'p-3 md:p-4' : compact ? 'p-4 md:p-5' : 'p-4';
	const badgeClass = dense ? 'px-3 py-1 text-xs' : 'px-3 py-1 text-sm';
	const playButtonClass = dense ? 'w-11 h-11 md:w-12 md:h-12' : compact ? 'w-14 h-14' : 'w-12 h-12';
	const playIconClass = dense ? 'w-6 h-6 md:w-7 md:h-7' : compact ? 'w-9 h-9' : 'w-8 h-8';
	const appIconClass = dense ? 'w-12 h-12 md:w-14 md:h-14' : compact ? 'w-16 h-16' : 'w-14 h-14';
	const titleClass = compact
		? 'text-sm md:text-base font-semibold truncate hover:underline'
		: 'text-sm font-semibold truncate hover:underline';
	const statValueClass = dense
		? 'text-base md:text-xl font-bold text-emerald-400'
		: compact
			? 'text-lg md:text-2xl font-bold text-emerald-400'
			: 'text-sm md:text-xl font-bold text-emerald-400';

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<div
	class="h-full bg-white dark:bg-surface-900 rounded-lg border-2 border-pink-200 dark:border-pink-800 overflow-hidden hover:shadow-xl transition-shadow duration-300 flex flex-col"
>
	<div class={`bg-gradient-to-r from-pink-500 to-rose-500 text-white font-bold ${badgeClass}`}>
		#{index + 1}
		{badgeLabel}
	</div>

	<button
		onclick={() =>
			onOpen(
				`https://media.appgoblin.info/creatives/raw/${creative.md5_hash.substring(0, 3)}/${creative.md5_hash}.${creative.file_extension}`,
				`${titlePrefix} #${index + 1}`
			)}
		class={`relative w-full bg-gradient-to-br from-purple-200 to-pink-200 dark:from-purple-900 dark:to-pink-900 cursor-pointer group overflow-hidden ${mediaAspectClass}`}
		title="Click to play video"
	>
		<img
			src={`https://media.appgoblin.info/creatives/thumbs/${creative.md5_hash}.jpg`}
			alt={`${titlePrefix} ${index + 1}`}
			class="w-full h-full object-cover"
			onerror={(e) => {
				const target = e.currentTarget as HTMLImageElement;
				target.style.display = 'none';
			}}
		/>
		<div
			class="absolute inset-0 flex items-center justify-center bg-surface-100-900/20 group-hover:bg-surface-100-900/10 transition-all duration-200"
		>
			<div
				class={`${playButtonClass} bg-white rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-200 shadow-lg`}
			>
				<svg class={`${playIconClass} text-pink-600 ml-1`} fill="currentColor" viewBox="0 0 20 20">
					<path
						d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
					/>
				</svg>
			</div>
		</div>
	</button>

	<div class={`${bodyPaddingClass} space-y-2 flex flex-col ${mediaFill ? '' : 'flex-1'}`}>
		<a
			href={`/apps/${creative.advertiser_store_id}`}
			class="flex items-center gap-2 mb-3 hover:opacity-80 transition-opacity"
		>
			<img
				src={`https://media.appgoblin.info/app-icons/${creative.advertiser_store_id}/${creative.advertiser_icon_url_100}`}
				alt="App icon"
				class={`${appIconClass} rounded-lg shadow-sm`}
				onerror={(e) => ((e.currentTarget as HTMLImageElement).src = '/default_company_logo.png')}
			/>
			<div class="min-w-0">
				<div class={titleClass}>
					{creative.advertiser_name ?? creative.advertiser_store_id}
				</div>
				<div class="text-xs text-surface-500 dark:text-surface-400 truncate">
					{creative.advertiser_store_id}
				</div>
			</div>
		</a>
		<div class="flex justify-between items-center">
			<span class="text-sm text-surface-600 dark:text-surface-400">Publishers</span>
			<span class={statValueClass}>
				{creative.publisher_count}
			</span>
		</div>
		<div
			class="text-xs text-surface-500 dark:text-surface-500 pt-2 border-t border-surface-200 dark:border-surface-700 mt-auto"
		>
			<div class="flex justify-between gap-2">
				<span>First seen:</span>
				<span class="font-semibold">{formatDate(creative.first_seen)}</span>
			</div>
			<div class="flex justify-between gap-2">
				<span>Last seen:</span>
				<span class="font-semibold">{formatDate(creative.last_seen)}</span>
			</div>
		</div>
	</div>
</div>
