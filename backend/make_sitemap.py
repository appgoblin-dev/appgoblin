"""Script to generate sitemaps for AppGoblin."""

import pathlib
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

import pandas as pd

from config import MODULE_DIR, get_logger
from dbcon.connections import get_db_connection
from dbcon.queries import get_sitemap_apps, get_sitemap_companies

logger = get_logger(__name__)

SITEMAP_DIR = MODULE_DIR.parent / pathlib.Path("frontend/static")

STATIC_URLS = [
    "https://appgoblin.info",
    "https://appgoblin.info/ad-creatives",
    "https://appgoblin.info/blog",
    "https://appgoblin.info/about",
    "https://appgoblin.info/fastest-growing-apps/google/overall",
    "https://appgoblin.info/fastest-growing-apps/ios/overall",
    "https://appgoblin.info/companies",
    "https://appgoblin.info/collections/new_monthly/google/overall",
    "https://appgoblin.info/collections/new_weekly/apple/overall",
    "https://appgoblin.info/collections/new_weekly/google/overall",
    "https://appgoblin.info/collections/new_monthly/apple/overall",
    "https://appgoblin.info/collections/new_monthly/google/overall",
    "https://appgoblin.info/collections/new_yearly/apple/overall",
    "https://appgoblin.info/collections/new_yearly/google/overall",
    "https://appgoblin.info/rankings/store/1/collection/1/category/1/US",
    "https://appgoblin.info/rankings/store/2/collection/4/category/120/US",
]


def set_df_sitemap_columns(
    df: pd.DataFrame, priority: float, changefreq: str = "weekly"
) -> pd.DataFrame:
    """Set sitemap-specific columns in DataFrame.

    Args:
        df: Input DataFrame
        priority: URL priority (0.0-1.0)
        changefreq: Update frequency (default: weekly)

    Returns:
        DataFrame with sitemap columns added

    """
    df["priority"] = priority
    df["changefreq"] = changefreq
    return df


def create_sitemap(df: pd.DataFrame, filename: str) -> None:
    """Create individual sitemap XML file from DataFrame.

    Args:
        df: DataFrame containing URL data
        filename: Output filename

    """
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # Direct string formatting instead of XML DOM operations
    template = """    <url>
        <loc>{url}</loc>
    </url>"""

    # Bulk append using list comprehension
    xml_lines.extend(template.format(**row) for _, row in df.iterrows())

    xml_lines.append("</urlset>")

    # Single write operation
    with pathlib.Path(SITEMAP_DIR / filename).open("w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))


def create_static_sitemap() -> str:
    """Create a sitemap for static pages.

    Returns:
        Filename of the generated static sitemap

    """
    # Static URLs to include
    static_urls = [
        "https://appgoblin.info",
        "https://appgoblin.info/about",
        "https://appgoblin.info/ad-creatives",
        "https://appgoblin.info/blog",
        "https://appgoblin.info/fastest-growing-apps/google/overall",
        "https://appgoblin.info/fastest-growing-apps/ios/overall",
        "https://appgoblin.info/companies",
        "https://appgoblin.info/collections/new_monthly/google/overall",
        "https://appgoblin.info/collections/new_weekly/apple/overall",
        "https://appgoblin.info/collections/new_weekly/google/overall",
        "https://appgoblin.info/collections/new_yearly/apple/overall",
        "https://appgoblin.info/collections/new_yearly/google/overall",
        "https://appgoblin.info/collections/new_weekly/apple/overall",
        "https://appgoblin.info/sdks",
        "https://appgoblin.info/rankings/store/1/collection/1/category/1/US",
        "https://appgoblin.info/rankings/store/2/collection/4/category/120/US",
    ]

    static_df = pd.DataFrame({"url": static_urls})
    static_df = set_df_sitemap_columns(static_df, priority=1.0)

    filename = "sitemap_static.xml"
    create_sitemap(static_df, filename)
    return f"https://appgoblin.info/{filename}"


def create_main_sitemap(sitemaps: list[str], filename: str) -> None:
    """Create main sitemap index file.

    Args:
        sitemaps: List of sitemap URLs to include
        filename: Output filename

    """
    # Start creating the sitemap index
    sitemap_index = Element(
        "sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )

    for sitemap in sitemaps:
        sitemap_elem = SubElement(sitemap_index, "sitemap")
        SubElement(sitemap_elem, "loc").text = sitemap

    # Convert to string and prettify
    raw_xml = tostring(sitemap_index, encoding="utf-8")
    dom = parseString(raw_xml)  # noqa: S318
    pretty_xml = dom.toprettyxml(indent="  ")

    # Write to file, excluding the first line with the XML declaration
    with pathlib.Path(SITEMAP_DIR / filename).open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("\n".join(pretty_xml.splitlines()[1:]))


def create_paginated_sitemaps(
    df: pd.DataFrame, base_filename: str, chunk_size: int = 20000
) -> list[str]:
    """Create multiple sitemap files by paginating large DataFrame.

    Args:
        df: Input DataFrame
        base_filename: Base name for output files
        chunk_size: Number of URLs per sitemap file

    Returns:
        List of generated sitemap filenames

    """
    chunk_size = 25000  # Adjust based on your needs
    filenames = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i : i + chunk_size]
        filename = f"{base_filename}_{i // chunk_size + 1}.xml"
        create_sitemap(chunk, filename)
        logger.info(f"Generated {filename}")
        filenames.append(f"https://appgoblin.info/{filename}")
    return filenames


dbcon = get_db_connection("madrone")

apps = get_sitemap_apps(dbcon)
apps = apps.head(100)


cdf = get_sitemap_companies(dbcon)

MIN_APP_COUNT = 10000

# Companies with URL slugs are more likely to be relevant
# (ie not typos from app-ads.txt)

is_ad_network = cdf["type_url_slug"].notna() & cdf["type_url_slug"].isin(
    ["ad-networks"]
)
is_not_ad_network = ~(is_ad_network) & cdf["type_url_slug"].notna()
cdf = cdf[((cdf["app_count"] > MIN_APP_COUNT) & is_ad_network) | is_not_ad_network]


# about 6
company_types = (
    cdf.groupby("type_url_slug")["app_count"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
company_types["url"] = (
    "https://appgoblin.info/companies/types/" + company_types["type_url_slug"]
)
company_types = set_df_sitemap_columns(company_types, 0.9)

# about 50
company_categories = (
    cdf.groupby("app_category")["app_count"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
company_categories["url"] = (
    "https://appgoblin.info/companies/categories/" + company_categories["app_category"]
)
company_categories = set_df_sitemap_columns(company_categories, 0.8)

# about 5 * 50
company_type_categories = (
    cdf.groupby(["type_url_slug", "app_category"])["app_count"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
company_type_categories["url"] = (
    "https://appgoblin.info/companies/types/"
    + company_type_categories["type_url_slug"]
    + "/"
    + company_type_categories["app_category"]
)
company_type_categories = set_df_sitemap_columns(company_type_categories, 0.7)


# about 1700
companies = (
    cdf.groupby("company_domain")["app_count"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
companies["url"] = "https://appgoblin.info/companies/" + companies["company_domain"]
companies = set_df_sitemap_columns(companies, 0.8)


# about 5k
apps["url"] = "https://appgoblin.info/apps/" + apps["store_id"]
apps = set_df_sitemap_columns(apps, 0.5, "monthly")

static_pages = pd.DataFrame({"url": STATIC_URLS})
static_pages = set_df_sitemap_columns(static_pages, 1.0, "weekly")

allurls = pd.concat(
    [
        static_pages,
        company_types,
        company_categories,
        company_type_categories,
        companies,
        apps,
    ],
    ignore_index=True,
)

create_sitemap(allurls, "sitemap.xml")
