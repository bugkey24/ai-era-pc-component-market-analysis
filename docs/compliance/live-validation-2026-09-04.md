# Live Scraping Validation Report — 2026-09-04

**Release:** v1.3.1 · **Commit:** `c4b63ac` (data collection) + v1.3.1 fixes · **Environment:** local Windows machine, residential IP
**Method:** Tokopedia Apollo-cache parsing (`window.__cache`), robots-guarded by `RobotsGuard` (fail-closed)

---

## 1. Collection Summary

| Category | Search keyword | Raw listings | After name-signature filters | After preprocessing |
| -------- | -------------- | ------------ | ---------------------------- | ------------------- |
| GPU | `rtx` | — | 82 | 79 |
| RAM | `ddr5` | — | 63 | 61 |
| SSD | `nvme` | — | 175 | 175 |
| **Total** | | **375** | **320** | **315** |

Raw find-page yield was 375 listings. Data-quality auditing for v1.3.1 added
name-signature filters that removed **55 misclassified or accessory listings**:

- 24 PC motherboards listed under the RAM/SSD breadcrumbs (AM5/LGA/socket/
  chipset tokens in titles)
- 19 laptops and prebuilt PCs under the GPU breadcrumb (Lenovo LOQ/Legion,
  HP Victus, MSI Thin, ASUS TUF A/F-series, "PC Build/Rakitan", AIO desktops)
- 2 PCIe↔M.2 adapter cards, 1 storage bag, 9 duplicate/other accessory rows

All removals are encoded in `TokopediaScraper` exclusion patterns and covered
by regression tests (`tests/test_scrapers.py::test_live_noise_filtered`,
`test_motherboard_signatures_filtered`, `test_genuine_modules_not_caught_by_board_signature`).

Review corpus: **64 real reviews from 29 products** across all 3 categories
(`data/snapshot/reviews_tokopedia.csv`). No synthetic or dummy content anywhere.

## 2. robots.txt Compliance

| Platform | Snapshot status | Verdict |
| -------- | --------------- | ------- |
| Tokopedia | Re-fetched 2026-09-04 — byte-identical (normalized) to 2026-09-03 snapshot | ✅ `/find/*?page` + `/*/review` explicitly allowed; all fetches pass `RobotsGuard` |
| Shopee | Re-fetched 2026-09-04 — **refreshed**; Googlebot section expanded, `User-agent: *` rules unchanged (`Crawl-delay: 1`, `/search*searchPrefill`, `*-i.*/similar`) | ⚠️ Not scraped (anti-bot risk); no live requests made |
| Blibli | Re-fetched 2026-09-04 — byte-identical to 2026-09-03 snapshot | ❌ Search/review surfaces disallowed; no live requests made |

Every Tokopedia request consulted the RFC 9309 engine in
`src/scrapers/robots_guard.py` before fetching; no disallowed URL was requested.

## 3. Corrections Discovered During This Audit

1. **TOPSIS rank assignment bug (fixed in v1.3.1):** `rank()` assigned the
   descending-score *permutation* as the Rank column instead of its inverse,
   so published rankings could show Rank 1 with a lower Score than Rank 2
   whenever the best alternative was not row 0. All rankings regenerated;
   regression test added (`test_rank_ordering_is_monotonic_in_score`).
2. **Sentiment distribution corrected:** the single non-positive review is
   *neutral* (rating 3), not negative — genuine distribution is
   **63 positive / 1 neutral / 0 negative**. Held-out accuracy remains not
   measurable (documented honestly).
3. **Notebook §7 no longer trains a hand-written "demo" model** — it trains
   on the real 64-review corpus and reports `accuracy = None` when the
   held-out split is not measurable.

## 4. Reproducibility

The committed snapshot (`data/snapshot/`) contains the filtered 320-product
dataset and the 64-review corpus; the notebook reproduces every figure in
[`../09-live-experiment-results.md`](../09-live-experiment-results.md) with
zero network requests.
