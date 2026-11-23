"""Application-controlled source definitions, never loaded from upload metadata."""
from types import MappingProxyType
from .models import SourceDefinition


def _source(source_id, organization, canonical, machine, licensing, notes, trust="authoritative_organization"):
    return SourceDefinition(source_id=source_id, organization=organization,
        canonical_url=canonical, machine_readable_url=machine, licensing_url=licensing,
        licensing_notes=notes, trust_classification=trust)


_DEFINITIONS = MappingProxyType({source.source_id: source for source in (
    _source("nvd", "NIST National Vulnerability Database", "https://nvd.nist.gov/",
        "https://services.nvd.nist.gov/rest/json/cves/2.0", "https://nvd.nist.gov/general/faq",
        "Attribute NVD and original CVE contributors; review NVD/CVE terms and third-party rights before redistribution."),
    _source("cisa-kev", "CISA", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "https://www.cisa.gov/about/website-policies", "US-government material; preserve attribution and review third-party rights."),
    _source("mitre-attack", "MITRE ATT&CK", "https://attack.mitre.org/",
        "https://github.com/mitre-attack/attack-stix-data", "https://attack.mitre.org/resources/terms-of-use/",
        "MITRE ATT&CK terms apply; retain attribution, notices, and applicable license with redistributed content."),
    _source("mitre-cwe", "MITRE CWE", "https://cwe.mitre.org/",
        "https://cwe.mitre.org/data/downloads.html", "https://cwe.mitre.org/about/termsofuse.html",
        "MITRE permits use subject to retaining its copyright designation and license; CWE is a MITRE trademark."),
    _source("nist-csrc", "NIST CSRC", "https://csrc.nist.gov/publications", None,
        "https://www.nist.gov/open/license", "Review each publication's status, notices, and third-party rights; withdrawn/draft guidance is not automatically current."),
    _source("owasp", "OWASP Foundation", "https://owasp.org/",
        "https://github.com/OWASP/CheatSheetSeries", "https://cheatsheetseries.owasp.org/",
        "Review the specific OWASP project's license and attribution/share-alike requirements before redistribution."),
    _source("fixture-reference", "CyberShield offline fixtures", "https://example.com/", None,
        "https://creativecommons.org/publicdomain/zero/1.0/", "Original synthetic fixture text: CC0-1.0. Not an official security recommendation.", "synthetic_fixture"),
)})


class SourceRegistry:
    def get(self, source_id: str) -> SourceDefinition:
        try:
            return _DEFINITIONS[source_id]
        except (KeyError, TypeError):
            raise ValueError("Unregistered source; metadata cannot grant public trust.") from None

    def definitions(self) -> tuple[SourceDefinition, ...]:
        return tuple(_DEFINITIONS.values())
