<script lang="ts">
	import type { CompanyTree, CompanyDomain, ChildCompany } from '../types';
	import { countryCodeToEmoji } from './utils/countryCodeToEmoji';

	interface Props {
		companyTree: CompanyTree;
		hasHigherLevelParent: boolean;
		queriedIsMappedCompany: boolean;
		associatedDomains: CompanyDomain[];
		showTruncated?: boolean;
	}

	let {
		companyTree,
		hasHigherLevelParent,
		queriedIsMappedCompany,
		associatedDomains,
		showTruncated = false
	}: Props = $props();

	const getDomainSlice = (domains: CompanyDomain[]) =>
		showTruncated ? domains.slice(0, 4) : domains;
	const getChildrenSlice = (children: ChildCompany[]) =>
		showTruncated ? children.slice(0, 6) : children;
	const getChildDomainsSlice = (domains: CompanyDomain[]) =>
		showTruncated ? domains.slice(0, 3) : domains;
</script>

<div class="font-mono text-sm leading-6">
	{#if hasHigherLevelParent}
		<div class="flex items-center gap-2">
			{#if companyTree.parent?.company_logo_url}
				<img
					src="https://media.appgoblin.info/{companyTree.parent.company_logo_url}"
					alt={companyTree.parent.company_name || companyTree.parent.company_domain}
					class="w-5 h-5 rounded-sm"
					loading="lazy"
				/>
			{/if}
			<a class="font-semibold" href="/companies/{companyTree.parent?.company_domain}">
				{companyTree.parent?.company_name || companyTree.parent?.company_domain}
			</a>
			<span class="text-xs text-gray-500 ml-2">Parent</span>
		</div>
		<div class="ml-4 text-gray-500 flex items-center gap-2">
			<span>└─</span>
			{#if companyTree.company_logo_url}
				<img
					src="https://media.appgoblin.info/{companyTree.company_logo_url}"
					alt={companyTree.company_name || companyTree.company_domain || companyTree.queried_domain}
					class="w-4 h-4 rounded-sm"
					loading="lazy"
				/>
			{/if}
			<a
				class="font-semibold"
				href="/companies/{companyTree.company_domain || companyTree.queried_domain}"
				>{companyTree.company_name || companyTree.company_domain || companyTree.queried_domain}</a
			>
			<span class="text-xs">Company</span>
		</div>
		{#if associatedDomains.length > 0}
			{#each getDomainSlice(associatedDomains) as relatedDomain}
				<div class="ml-8 text-gray-500">
					└─ <a class="font-semibold" href="/companies/{relatedDomain.domain_name}"
						>{relatedDomain.domain_name}</a
					>{#if relatedDomain.is_primary}
						<span class="text-xs">(Primary)</span>{/if}
				</div>
				{#if relatedDomain.country.length > 0 || relatedDomain.org.length > 0}
					<div class="ml-12 text-xs text-gray-500">
						{#if relatedDomain.country.length > 0}
							<span class="mr-2">
								{#each relatedDomain.country as country}
									<span class="mr-1">{countryCodeToEmoji(country)}</span>
								{/each}
							</span>
						{/if}
						{#if relatedDomain.org.length > 0}
							<span>{relatedDomain.org.join(', ')}</span>
						{/if}
					</div>
				{/if}
			{/each}
			{#if showTruncated && associatedDomains.length > 4}
				<div class="ml-12 text-xs text-gray-500">
					...and {associatedDomains.length - 4} more domains
				</div>
			{/if}
		{/if}
		{#if companyTree.children.length > 0}
			{#each getChildrenSlice(companyTree.children) as child}
				<div class="ml-8 flex items-center gap-2">
					{#if child.company_logo_url}
						<img
							src="https://media.appgoblin.info/{child.company_logo_url}"
							alt={child.company_name || child.company_domain}
							class="w-4 h-4 rounded-sm"
							loading="lazy"
						/>
					{/if}
					<a class="font-semibold" href="/companies/{child.company_domain}"
						>{child.company_name || child.company_domain}</a
					>
				</div>
				{#if child.domains.length > 0}
					{#each getChildDomainsSlice(child.domains) as childDomain}
						<div class="ml-12 text-gray-500">
							└─ <a class="font-semibold" href="/companies/{childDomain.domain_name}"
								>{childDomain.domain_name}</a
							>
							{#if childDomain.is_primary}
								<span class="text-xs">(Primary)</span>
							{/if}
						</div>
						{#if childDomain.country.length > 0 || childDomain.org.length > 0}
							<div class="ml-16 text-xs text-gray-500">
								{#if childDomain.country.length > 0}
									<span class="mr-2">
										{#each childDomain.country as country}
											<span>{countryCodeToEmoji(country)}</span>
										{/each}
									</span>
								{/if}
								{#if childDomain.org.length > 0}
									<span>{childDomain.org.join(', ')}</span>
								{/if}
							</div>
						{/if}
					{/each}
					{#if showTruncated && child.domains.length > 3}
						<div class="ml-16 text-xs text-gray-500">
							...and {child.domains.length - 3} more domains
						</div>
					{/if}
				{/if}
			{/each}
			{#if showTruncated && companyTree.children.length > 6}
				<div class="ml-12 text-xs text-gray-500">
					...and {companyTree.children.length - 6} more child companies
				</div>
			{/if}
		{/if}
		{#if !queriedIsMappedCompany}
			<div class="ml-8 text-gray-500">
				└─ <a class="font-semibold" href="/companies/{companyTree.queried_domain}"
					>{companyTree.queried_domain}</a
				> <span class="text-xs">Queried Domain</span>
			</div>
		{/if}
	{:else}
		<div class="flex items-center gap-2">
			{#if companyTree.company_logo_url}
				<img
					src="https://media.appgoblin.info/{companyTree.company_logo_url}"
					alt={companyTree.company_name || companyTree.company_domain || companyTree.queried_domain}
					class="w-4 h-4 rounded-sm"
					loading="lazy"
				/>
			{/if}
			<a
				class="font-semibold"
				href="/companies/{companyTree.company_domain || companyTree.queried_domain}"
			>
				{companyTree.company_name || companyTree.company_domain || companyTree.queried_domain}
			</a>
			<span class="text-xs text-gray-500 ml-2">Company</span>
		</div>
		{#if associatedDomains.length > 0}
			{#each getDomainSlice(associatedDomains) as relatedDomain}
				<div class="ml-4 text-gray-500">
					└─ <a class="font-semibold" href="/companies/{relatedDomain.domain_name}"
						>{relatedDomain.domain_name}</a
					>{#if relatedDomain.is_primary}
						<span class="text-xs">(Primary)</span>{/if}
				</div>
				{#if relatedDomain.country.length > 0 || relatedDomain.org.length > 0}
					<div class="ml-8 text-xs text-gray-500">
						{#if relatedDomain.country.length > 0}
							<span class="mr-2">
								{#each relatedDomain.country as country}
									<span>{countryCodeToEmoji(country)}</span>
								{/each}
							</span>
						{/if}
						{#if relatedDomain.org.length > 0}
							<span>{relatedDomain.org.join(', ')}</span>
						{/if}
					</div>
				{/if}
			{/each}
			{#if showTruncated && associatedDomains.length > 4}
				<div class="ml-8 text-xs text-gray-500">
					...and {associatedDomains.length - 4} more domains
				</div>
			{/if}
		{/if}
		{#if companyTree.children.length > 0}
			{#each getChildrenSlice(companyTree.children) as child}
				<div class="ml-4 flex items-center gap-2">
					{#if child.company_logo_url}
						<img
							src="https://media.appgoblin.info/{child.company_logo_url}"
							alt={child.company_name || child.company_domain}
							class="w-4 h-4 rounded-sm"
							loading="lazy"
						/>
					{/if}
					<a class="font-semibold" href="/companies/{child.company_domain}"
						>{child.company_name || child.company_domain}</a
					>
				</div>
				{#if child.domains.length > 0}
					{#each getChildDomainsSlice(child.domains) as childDomain}
						<div class="ml-8 text-gray-500">
							└─ <a class="font-semibold" href="/companies/{childDomain.domain_name}"
								>{childDomain.domain_name}</a
							>
							{#if childDomain.is_primary}
								<span class="text-xs">(Primary)</span>
							{/if}
						</div>
						{#if childDomain.country.length > 0 || childDomain.org.length > 0}
							<div class="ml-12 text-xs text-gray-500">
								{#if childDomain.country.length > 0}
									<span class="mr-2">
										{#each childDomain.country as country}
											<span>{countryCodeToEmoji(country)}</span>
										{/each}
									</span>
								{/if}
								{#if childDomain.org.length > 0}
									<span>{childDomain.org.join(', ')}</span>
								{/if}
							</div>
						{/if}
					{/each}
					{#if showTruncated && child.domains.length > 3}
						<div class="ml-12 text-xs text-gray-500">
							...and {child.domains.length - 3} more domains
						</div>
					{/if}
				{/if}
			{/each}
			{#if showTruncated && companyTree.children.length > 6}
				<div class="ml-8 text-xs text-gray-500">
					...and {companyTree.children.length - 6} more child companies
				</div>
			{/if}
		{/if}
		{#if !queriedIsMappedCompany}
			<div class="ml-4 text-gray-500">
				└─ <a class="font-semibold" href="/companies/{companyTree.queried_domain}"
					>{companyTree.queried_domain}</a
				> <span class="text-xs">Queried Domain</span>
			</div>
		{/if}
	{/if}
</div>
