export interface AccountFormResult {
	section?: string;
	message?: string;
	success?: boolean;
}

export interface FollowedApp {
	id: number;
	store_id: string;
	created_at: string | Date;
	app_name: string | null;
}

export interface AppSummary {
	name: string | null;
	icon: string | null;
	installs: number | null;
}

export interface FollowedCompany {
	id: number;
	company_id: number;
	created_at: string | Date;
	company_name: string | null;
	company_domain: string | null;
}

export interface TrackedKeyword {
	id: number;
	store_id: string;
	keyword_text: string;
	created_at: string | Date;
	app_name: string | null;
}

export interface RequestedSdkScan {
	id: number;
	store_id: string;
	created_at: string | Date | null;
	app_name: string | null;
}
