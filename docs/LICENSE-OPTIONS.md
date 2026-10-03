# SEIReader license options — decision recorded

Prepared **2026-10-03** for **SEIHouse Productions LLC, Ohio**. This is a product
licensing comparison and proposed policy, not the operative EULA or a legal opinion.

**Recommendation: option A, proprietary rights with an explicit SEIHouse app and
web embedding EULA, retaining the ability to sell commercial licenses later.**
It fits the current first-party app use and leaves the distribution decision with
the owner. Choose option C instead if unrestricted community and commercial reuse
of the font is an intended product goal. The [name check](NAME-CHECK.md) separately
flags a material SEEREADER candidate; none of these licenses resolves that issue.

**Decision recorded on 2026-10-03:** the owner selected proprietary ecosystem
licensing, confirmed personal/commercial creative use and customization for
ecosystem users, and reserved unrelated product embedding and standalone font
redistribution for separate permission. The current family becomes **SEIHouse Sans**.
The operative terms are in [LICENSE](../LICENSE); the comparison below records
the options considered before that decision and is not itself a license grant.

## Repository status before the decision

Before the decision, `README.md` and `FONT-LICENSE.txt` reserved rights pending a
choice. `package.json` was private and marked `UNLICENSED`. `make_fonts.py` supplied a short
copyright string, vendor ID `SEIH`, and `fsType=0`; the latter is a technical
embedding setting, not a substitute for permission from the owner.

The decision should cover the **ten SEIReader styles**, full OTF/WOFF2 files,
**thirty WOFF2 subsets**, and the runtime CSS/package deliveries. State explicitly
whether original SEIReader drawing rules, build scripts, and related documentation
are included. A root license must delimit scope: this repository also contains the
separate Display prototype, archived releases, third-party reference fonts, and
CLDR data. Their inclusion in the repository does not silently relicense them.
Literata/Rubik reference licenses and the Unicode data license remain applicable
to their own files. The design goals describe original drawing rules with reference
outlines used in comparison assets; counsel should verify provenance and assignments
before an external grant.

## Comparison

Options A and B are both proprietary. "Commercial" describes a sales model and
negotiated grant; it is not a standard license text. OFL also allows commercial use.

| Topic | A — rights reserved + first-party embedding EULA | B — commercial proprietary license | C — SIL OFL 1.1 |
| --- | --- | --- | --- |
| App use | Permit SEIHouse developers/authorized contractors to build and ship designated apps; users may render text inside them. Define desktop, mobile, offline, and WebView coverage. | Sell an explicit app/OEM grant to a named licensee, with agreed products/platforms and limits. A desktop grant alone should not imply app distribution rights. | Anyone may bundle the font with free or paid apps under OFL conditions. App code can retain its own license. |
| Web use | Explicitly permit self-hosted `@font-face`, CDN delivery, browser caching, and first-party domains/services. In-app permission alone leaves this ambiguous. | Offer a separate web grant or combine it with app rights. Specify domains, CDN/self-hosting, and any traffic limits. | Web delivery is allowed; preserve notices and apply the modification/RFN rules where needed. |
| Redistribution | Permit only necessary app bundles, installers, updates, web delivery, and approved build workflows. No general font-download or standalone redistribution grant. | Licensees redistribute only as agreed, such as app bundles. Reseller, font-download, or sublicensing rights require express terms. | Free redistribution of the font is allowed with notices/license; selling it alone is prohibited, while software bundles may be sold. |
| Derivatives | Reserve changes to the owner and authorized engineers; expressly allow approved conversion, subsetting, and build processing. End users get no general derivative grant. | Permit or prohibit editing, conversion, subsetting, custom versions, and transfer by specific contract terms. | Modification is allowed; distributed font derivatives remain OFL. RFNs can require renamed modified fonts or written permission to keep the name. |
| Pricing / control | No external sales required. Owner controls external permissions, release channels, and versions. | Fees, product scope, seats, term, support, and distribution limits are business choices. | No per-use royalties required for OFL rights. Recipients can use it commercially and share it. |
| Notices / distribution work | Ship the operative EULA/notice with runtime deliveries and expose it through an appropriate legal notice surface. | Deliver EULA plus an order/entitlement defining the purchased rights; preserve notices in allowed bundles. | Preserve copyright and OFL notices/license in distributed font packages and metadata. |

OFL column: [official license](https://openfontlicense.org/open-font-license-official-text/)
and [usage/distribution FAQ](https://openfontlicense.org/ofl-faq/). Commercial grants
vary in practice: [Adobe's licensing guidance](https://helpx.adobe.com/in/fonts/web/font-licensing/webfont-licensing.html)
distinguishes web service rights from direct app embedding, and
[Fontspring's app-license offering](https://www.fontspring.com/app-fonts) expressly
addresses application distribution. These are examples, not proposed SEIReader terms.

## A — proprietary with an app/web embedding EULA

Reserve the owner's rights, then make the necessary permissions affirmative.
A bare "all rights reserved" notice supplies no useful license to a third-party
developer, distributor, or end user. The owner itself does not need to purchase
its own font license; contractors and recipients need a clear authorized scope.

The proposed EULA should define:

- The covered font files, versions, owner, authorized developers, and SEIHouse
  products. Expressly allow releases, updates, app stores, backups, offline copies,
  browser caches, and contracted hosting/build services needed to deliver them.
- Rendering arbitrary user text inside the covered apps, including editable text.
  Decide separately whether exported PDF/EPUB documents or customer-created
  products may carry embedded fonts; those rights should not be assumed.
- Permitted web distribution and domains, full fonts/subsets, conversions,
  compression, and any CDN access controls. Browser fonts are downloadable assets;
  an anti-extraction clause cannot make them technically inaccessible.
- Restrictions on independent reuse, font resale, general redistribution,
  sublicensing, and unapproved derivatives, subject to applicable law. Preserve
  normal user access to their own text/output without confusing it with font rights.
- Notices, term/termination, treatment of previously distributed app copies,
  warranty/liability terms, and an appropriate acceptance mechanism. Ohio governing
  law is a proposed contract choice for counsel, not automatic worldwide enforcement.

This route preserves the option to grant external licenses later. Counsel should
draft/review the operative text, including contractor authorization and downstream
distribution. Public repository access is not itself an unrestricted font grant.

## B — commercial proprietary licensing

Use the same rights-reserved foundation, with a customer license defining what is
bought. A practical offer could combine desktop, app, self-hosted web, and document
embedding rights, or sell them separately. Decide whether charges depend on products,
seats, domains, installs, traffic, subscription term, or a perpetual buyout; no prices
or thresholds are proposed here.

Provide clear permissions for affiliates, contractors, testing, build systems,
CDNs, app stores, and users of the licensed products. Define modification/subsetting,
redistribution, font-as-a-service use, transfer, support, updates, and renewal.
Commercial licensing adds entitlement and customer-support work; it is useful
when external sales are intended, but unnecessary infrastructure for current
first-party use. A paid license does not automatically transfer copyright ownership.

## C — SIL Open Font License 1.1 and Reserved Font Names

Use the unaltered OFL 1.1 text with an accurate copyright header and explicit
definition of the released Font Software. It does not require an application using
the font to become open source. It also does not require publishing all build
source merely because binaries are distributed; decide what source is included
in the licensed release. Do not add incompatible usage or noncommercial restrictions.
See [OFL FAQ](https://openfontlicense.org/ofl-faq/).

**An RFN is optional and is not a trademark registration.** Declaring `SEIReader`
as an RFN reserves that primary user-visible font name for the original version
and expressly authorized modified versions. Without an RFN, OFL imposes no
RFN-based rename requirement, though other rights may still apply. Unmodified
copies can retain the name even when redistributed by others: RFN does not give
the owner exclusive distribution. Copyright-holder names also cannot be used to
imply endorsement of modified versions without permission. See
[SIL's RFN guidance](https://openfontlicense.org/ofl-reserved-font-names/).

The owner can publish its own official subsets under its reserved name. Downstream
subsetting or conversion can create a Modified Version, requiring renaming or
written RFN permission. SIL's guidance allows functionally equivalent web-font
conversions to retain RFNs when its stated criteria are met; that is not a blanket
exemption for every optimizer or subset. Decide whether to provide a narrowly
defined RFN permission for approved downstream processing, or have users use the
official shipped subsets. Keep that permission separate from the unchanged OFL.
See [Webfonts and Reserved Font Names](https://openfontlicense.org/webfonts-and-reserved-font-names/).

Choose OFL only if third parties may legally reuse and redistribute the font,
including commercial competitors. The owner can issue additional licenses for
work it owns, but cannot simply withdraw OFL permissions from already released
copies that continue to comply. Contributor rights can complicate later relicensing;
obtain suitable contribution/assignment agreements. Counsel should assess this
before an open release.

## Ownership and legal limits to confirm

The LLC is the supplied owner, not proof that every contribution is assigned to it.
Confirm copyright years, designers/contributors, employment/contractor assignments,
and any third-party source or outline obligations. Under US practice, typeface
appearance itself is generally not copyrightable; original font-program expression
can qualify. Proprietary protection therefore depends on the actual protectable
work, contracts, and any other applicable rights, not a notice alone. See
[Copyright Office Circular 33](https://www.copyright.gov/circs/circ33.pdf) and
[Compendium section 723](https://copyright.gov/comp3/chap700/ch700-literary-works.pdf#page=53).
Counsel should assess protection and enforceability in intended markets.

## Metadata and validation after the decision

The next implementation must keep the chosen legal grant consistent across
`LICENSE`, `FONT-LICENSE.txt`, README, package metadata, font names, and ZIP/package
deliveries. Update only SEIReader; identify exclusions for the Display prototype,
reference fonts/data, and historic releases.

| Field | Required decision / truthful value |
| --- | --- |
| Name ID 0 | Approved copyright years and SEIHouse Productions LLC attribution. |
| Name ID 7 | A truthful trademark statement only if approved/applicable; no unverified registration claim. |
| Name ID 8 | Manufacturer: SEIHouse Productions LLC. |
| Name ID 9 | Approved designer credit; ownership does not identify the designer automatically. |
| Name IDs 11 / 12 | Actual manufacturer and designer URLs, respectively. No invented designer site. |
| Name ID 13 / 14 | Selected license description and a real, stable URL to its operative text. A proprietary license URL must be supplied or approved. |
| OS/2 vendor ID | Current `SEIH`; verify appropriateness/registry status before claiming a registered vendor identifier. |
| OS/2 fsType | Select the actual embedding policy below, not merely the license label. |

Microsoft defines `fsType=0` as installable embedding; `0x0002` requires explicit
owner permission, `0x0004` permits preview/print, and `0x0008` permits editable
embedding. Additional bits can forbid subsetting or limit embedding to bitmaps.
These flags do not encode app/domain/traffic limits, enforce an EULA, or establish
ownership. **OFL should use `0`. A proprietary license is not automatically `2`:**
choose the granted document-embedding rights and align flags with the approved
EULA. If using `2`, the app/web EULA must expressly supply the permission for the
authorized distribution. Do not set no-subsetting when the policy allows it.
[Microsoft OS/2 specification](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fstype)
and [name-table specification](https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids)
define the fields.

Rebuild all ten full styles and thirty subsets, verify that metadata survives
conversion/subsetting, preserve outlines/metrics/shaping, and check actual runtime
deliveries. Run the applicable FontBakery profiles and report their exact version,
scope, skips, and results. The existing 0.35 report uses OpenType and **offline**
universal checks; it does not verify online checks. Target **0 FAIL / 0 WARN**
without suppressing a real issue or widening rights solely to satisfy a checker.
If a selected proprietary policy conflicts with a profile requirement, report and
resolve that conflict before claiming completion. Update README, CHANGELOG, and
HEALTH-CHECK with the newly observed results, then commit as requested.

## Owner decision

Choose one:

- **A — proprietary with SEIHouse app/web embedding EULA** (recommended now;
  retain optional commercial licensing later).
- **B — commercial proprietary license** (define the intended external customer
  grant before implementation).
- **C — SIL OFL 1.1** (also choose whether `SEIReader` is an RFN, subject to name
  clearance, and whether any downstream RFN permission should be offered).

The owner chose A with the confirmed ecosystem creative-use grant above. Studio
design/manufacturing credit uses SEIHouse Productions LLC; project URLs point to
the official repository and the license URL points to its LICENSE. No individual
designer or trademark/vendor registration is invented. Name screening remains
separate from the license decision.
