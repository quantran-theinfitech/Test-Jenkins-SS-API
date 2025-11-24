import re
import urllib.parse

import tldextract

from app.api.v1.schemas.search_cross import SearchCrossRequest


def extract_full_domain_url(hp_url):
    """
    Extract full domain URL with protocol from hp_url
    Example: "https://www.fedex.com/ja-jp/home.html -> "https://www.fedex.com"
    """
    if not hp_url:
        return None
    try:
        parsed = urllib.parse.urlparse(hp_url)
        if not parsed.scheme:
            parsed = urllib.parse.urlparse(f"https://{hp_url}")

        full_domain = f"{parsed.scheme}://{parsed.netloc}"
        return full_domain
    except Exception:
        return None


def extract_domain(hp_url):
    site_hostings = [
        "jimdofree.com",
        "kensetumap.com",
        "itp.ne.jp",
        "fc2.com",
        "rakuten.co.jp",
        "amebaownd.com",
        "plala.or.jp",
        "gorp.jp",
        "jbplt.jp",
        "owst.jp",
        "coocan.jp",
        "zennichi.net",
        "jimdosite.com",
        "goope.jp",
        "biglobe.ne.jp",
        "gogo.jp",
        "kaipoke.biz",
        "peraichi.com",
        "bsj.jp",
        "studio.site",
        "sjnk-ag.com",
        "tkcnf.com",
        "shop-pro.jp",
        "omisenomikata.jp",
        "jimdo.com",
        "shokokai.or.jp",
        "big-advance.site",
        "jimdoweb.com",
        "shopinfo.jp",
        "webnode.jp",
        "hotpepper.jp",
        "p-kit.com",
        "hugedomains.com",
        "sjc.ne.jp",
        "wordpress.com",
        "ameblo.jp",
        "ocn.ne.jp",
        "wakwak.com",
        "stores.jp",
        "business.site",
        "eonet.ne.jp",
        "rakuten.ne.jp",
        "odn.ne.jp",
        "ecnet.jp",
        "ocnk.net",
        "localinfo.jp",
        "so-net.ne.jp",
        "ftw.jp",
        "hp-ez.com",
        "crayonsite.com",
        "line.me",
        "hanatown.net",
        "honda.co.jp",
        "server-shared.com",
        "xsrv.jp",
        "thebase.in",
        "care-net.biz",
        "tiki.ne.jp",
        "dti.ne.jp",
        "lit.link",
        "crayonsite.net",
        "med.or.jp",
        "leopalace21.com",
        "oo7.jp",
        "mystrikingly.com",
        "gnavi.co.jp",
        "p-world.co.jp",
        "athome.co.jp",
        "survey-smiles.com",
        "xdomain.jp",
        "v-hf.com",
        "onamae.com",
        "ec-net.jp",
        "storeinfo.jp",
        "k2-homes.com",
        "exblog.jp",
        "nissan-dealer.jp",
        "foodre.jp",
        "e-classa.net",
        "tmn-agent.com",
        "myreformjp.com",
        "themedia.jp",
        "hi-ho.ne.jp",
        "ans.co.jp",
        "webcrow.jp",
        "office-web.jp",
        "lixil-madolier.jp",
        "mypl.net",
        "en-gage.net",
        "localplace.jp",
        "eflora.co.jp",
        "regus-office.jp",
        "fujitv-flower.net",
        "e-house.co.jp",
        "synapse.ne.jp",
        "ooco.jp",
        "tokai.or.jp",
        "lifecorp.jp",
        "shinkin.co.jp",
        "cbiz.co.jp",
        "cloud-line.com",
        "hotstaff.co.jp",
        "wix.com",
        "i-e.jp",
        "biz-web.jp",
        "edion.com",
        "seesaa.net",
        "la9.jp",
        "park-direct.jp",
        "xrea.com",
        "zenkokuhojinkai.or.jp",
        "ti-da.net",
        "suzuki.co.jp",
        "create-sd.co.jp",
        "ecweb.jp",
        "century21.jp",
        "fujitsu.com",
        "myclinic.ne.jp",
        "fudousandata.jp",
        "nifty.com",
        "weblife.me",
        "bbiq.jp",
        "tabelog.com",
        "wind.ne.jp",
        "securesite.jp",
        "pikara.ne.jp",
        "job-gear.net",
    ]
    if not hp_url:
        return None
    extract = tldextract.extract(hp_url, include_psl_private_domains=True)
    # Treat google.com (including sites.google.com, www.google.com, etc.) as null
    if extract.suffix and extract.domain:
        registered_domain = f"{extract.domain}.{extract.suffix}"
        if registered_domain == "google.com":
            return None
    if not extract.suffix:
        if not extract.domain:
            return None
        return extract.domain
    if not extract.domain:
        return extract.suffix
    registered_domain = f"{extract.domain}.{extract.suffix}"

    # Check if the registered domain is in site_hostings, if so include subdomain
    if (
        registered_domain in site_hostings
        and extract.subdomain
        and extract.subdomain != "www"
    ):
        return f"{extract.subdomain}.{registered_domain}"

    return registered_domain


def normalized_domain_search_companies(search_condition: SearchCrossRequest):
    if search_condition.domain_name:
        search_condition.domain_name = [
            extract_domain(x)
            for x in split_string_by_newline(search_condition.domain_name)
        ]
    return search_condition


def extract_vanity_name_linkedin(linkedin_url):
    if not linkedin_url:
        return None
    pattern = r"(?<=linkedin.com/in/)[^/]+"
    match = re.search(pattern, linkedin_url)
    if match:
        return match.group(0)
    else:
        return None


def extract_profile_name_twitter(twitter_url):
    pattern = r"(?<=twitter.com/)[^/]+"
    match = re.search(pattern, twitter_url)
    if match:
        return match.group(0)
    else:
        return None


def extract_profile_name_github(github_url):
    pattern = r"(?<=github.com/)[^/]+"
    match = re.search(pattern, github_url)
    if match:
        return match.group(0)
    else:
        return None


def extract_profile_name_wantedly(wantedly_url):
    pattern = r"(?<=wantedly.com/id/)[^/]+"
    match = re.search(pattern, wantedly_url)
    if match:
        return match.group(0)
    else:
        return None


def extract_profile_name_facebook(fb_url):
    pattern = r"(?<=facebook.com/)[^/]+"
    match = re.search(pattern, fb_url)
    if match:
        return match.group(0)
    else:
        return None


def normalize_url(url):
    prefixes = ["http://", "https://", "www."]
    for prefix in prefixes:
        if url.startswith(prefix):
            url = url[len(prefix) :]  # noqa

    if url.endswith("/"):
        url = url[:-1]

    return url


def extract_profile_name(url):
    profile_name = extract_vanity_name_linkedin(url)
    if profile_name is None:
        profile_name = extract_profile_name_twitter(url)
    if profile_name is None:
        profile_name = extract_profile_name_github(url)
    if profile_name is None:
        profile_name = extract_profile_name_wantedly(url)
    if profile_name is None:
        profile_name = extract_profile_name_facebook(url)
    return profile_name if profile_name else normalize_url(url)


def normalized_sns_url_search_persons(search_condition: SearchCrossRequest):
    if search_condition.sns_url:
        sns_urls = [
            urllib.parse.unquote(x.strip())
            for x in search_condition.sns_url.split("\n")
            if x != ""
        ]
        search_condition.sns_url = [extract_profile_name(x) for x in sns_urls]
    return search_condition


def split_string_by_newline(input_string: str) -> list:
    result = [item for item in input_string.split("\n") if item]

    return result
