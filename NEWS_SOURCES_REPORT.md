# Medical News Sources Report

**Date:** January 6, 2026
**Status:** ✅ Analysis Complete

---

## Executive Summary

This report provides a detailed breakdown of the 75+ medical news sources configured in `sites.yaml`. An initial connectivity and extraction test was performed on a sample of 20 sites to assess their status.

### Key Findings

- **Total Sites Configured:** 78
- **Sites Tested:** 20 (26% of total)
- **Working Sites (in sample):** 9 (45% of tested)
- **Sites with Errors (in sample):** 10 (50% of tested)
- **Sites without Feeds (in sample):** 1 (5% of tested)

Of the 20 sites tested, **9 were confirmed to be working properly**, successfully providing a total of **1,912 articles**. However, a significant number of sites returned errors, primarily HTTP 403 (Forbidden) and 404 (Not Found), indicating that many feeds are either no longer available or are protected by anti-scraping measures.

**Recommendation:** A full test of all 78 sites is recommended to get a complete picture of which sources are viable. The `test_sources.py` script can be modified to run on all sites.

---

## Confirmed Working News Sources (from sample)

The following 9 medical websites were confirmed to be working and are successfully extracting news articles:

| Site Name | Category | Articles Found |
|---|---|---|
| NIH News | General Medical News | 10 |
| CDC Newsroom | General Medical News | 1780 |
| News-Medical | News Aggregators | 10 |
| ScienceDaily Health & Medicine | News Aggregators | 60 |
| STAT News | News Aggregators | 20 |
| BMJ News | News Aggregators | 6 |
| Healthcare Dive | News Aggregators | 10 |
| MobiHealthNews | News Aggregators | 6 |
| DI Cardiology | Cardiology | 10 |

---

## Detailed Breakdown of All News Sources

Below is a comprehensive list of all 78 configured news sources, categorized by specialty. The status is based on the initial sample test; sites not in the sample are marked as "Not Tested".

### General Medical News (4 sites)

| Site Name | Status | Details |
|---|---|---|
| WHO News | ❌ **Error** | HTTP 0 (Connection Error) |
| NIH News | ✅ **Working** | 10 articles found |
| CDC Newsroom | ✅ **Working** | 1780 articles found from one feed; one feed returned 404 |
| Medscape | ❌ **Error** | HTTP 403 (Forbidden) |

### News Aggregators (10 sites)

| Site Name | Status | Details |
|---|---|---|
| MedicalXpress | ❌ **Error** | HTTP 400 (Bad Request) |
| News-Medical | ✅ **Working** | 10 articles found |
| ScienceDaily Health & Medicine | ✅ **Working** | 60 articles found |
| JAMA Network | ❌ **Error** | HTTP 403 (Forbidden) |
| STAT News | ✅ **Working** | 20 articles found |
| BMJ News | ✅ **Working** | 6 articles found |
| Healthline Health News | ⚠️ **No Feeds** | No RSS feeds configured |
| Healthcare Dive | ✅ **Working** | 10 articles found |
| Healio | ✅ **Working** | 0 articles found (feed is active but empty) |
| MobiHealthNews | ✅ **Working** | 6 articles found |

### Cardiology (8 sites)

| Site Name | Status | Details |
|---|---|---|
| TCTMD | ❌ **Error** | HTTP 403 (Forbidden) on both feeds |
| SCAI | ✅ **Working** | 0 articles found (feed is active but empty) |
| DI Cardiology | ✅ **Working** | 10 articles found |
| Cardiac Interventions Today | ❌ **Error** | HTTP 404 (Not Found) |
| ESC Press Office | ✅ **Working** | 0 articles found (feed is active but empty) |
| JAMA Cardiology | ❌ **Error** | HTTP 403 (Forbidden) |
| Cardiology Advisor | Not Tested | - |
| Medscape Cardiology | Not Tested | (Commented out in config) |

### Neurosurgery & Neurology (5 sites)

| Site Name | Status | Details |
|---|---|---|
| AANS Neurosurgeon | Not Tested | - |
| JAMA Neurology | Not Tested | - |
| Neurology Today | Not Tested | - |
| Practical Neurology | Not Tested | - |
| Neurovascular Today | Not Tested | - |

### Orthopedics & Spine (8 sites)

| Site Name | Status | Details |
|---|---|---|
| RYOrtho | Not Tested | - |
| Ortho Spine News | Not Tested | - |
| Becker's Spine Review | Not Tested | - |
| OrthoBuzz (JBJS) | Not Tested | - |
| Spine Market Group | Not Tested | - |
| AAOS Now | Not Tested | - |
| Becker's ASC Gastroenterology & Endoscopy | Not Tested | - |
| Becker's Spine Robotics | Not Tested | - |

### Radiology & Imaging (6 sites)

| Site Name | Status | Details |
|---|---|---|
| RSNA News | Not Tested | - |
| Diagnostic Imaging | Not Tested | - |
| Radiology Today | Not Tested | - |
| Imaging Technology News | Not Tested | - |
| Interventional News | Not Tested | - |
| SIR | Not Tested | - |

### Oncology (5 sites)

| Site Name | Status | Details |
|---|---|---|
| OncLive | Not Tested | - |
| Cancer Network News | Not Tested | - |
| OncoDaily | Not Tested | - |
| ESMO Oncology News | Not Tested | - |
| ASCO Post | Not Tested | - |

### Gastroenterology (3 sites)

| Site Name | Status | Details |
|---|---|---|
| AGA News | Not Tested | - |
| MDEdge GI & Hepatology News | Not Tested | - |
| Becker's ASC Gastroenterology & Endoscopy | Not Tested | (Duplicate category, see Orthopedics) |

### Urology (2 sites)

| Site Name | Status | Details |
|---|---|---|
| Urology Times | Not Tested | - |
| Renal & Urology News | Not Tested | - |

### Pulmonology & Cardiothoracic (2 sites)

| Site Name | Status | Details |
|---|---|---|
| STS Newsroom | Not Tested | - |
| Chest Physician | Not Tested | - |

### Vascular Surgery (4 sites)

| Site Name | Status | Details |
|---|---|---|
| Vascular Specialist Online | Not Tested | - |
| Vascular News | Not Tested | - |
| Endovascular Today | Not Tested | - |
| SVS News | Not Tested | - |

### Ophthalmology (4 sites)

| Site Name | Status | Details |
|---|---|---|
| EyeWire News | Not Tested | - |
| Ophthalmology Times | Not Tested | - |
| Review of Ophthalmology | Not Tested | - |
| Ophthalmology Breaking News | Not Tested | - |

### Other Specialties (17 sites)

This category contains a mix of specialties, including ENT, Pain Management, Anesthesiology, Emergency Medicine, and Medical Robotics. All sites in this category were **Not Tested**.

---

## Analysis of Errors

The most common errors encountered during the test were:

- **HTTP 403 (Forbidden):** This indicates that the server is blocking the request, likely due to anti-scraping measures. Sites like Medscape and JAMA Network are known to be protective of their content.
- **HTTP 404 (Not Found):** The feed URL is no longer valid. This is common as websites reorganize their content.
- **HTTP 400 (Bad Request):** The server could not understand the request. This might be due to a malformed URL or a server-side issue.
- **Connection Error:** The script was unable to establish a connection with the server.

## Recommendations for Improvement

1.  **Full Site Test:** Run the `test_sources.py` script on all 78 sites to get a complete list of working and non-working sources.
2.  **Update `sites.yaml`:** Remove or comment out the sites that are consistently returning errors. For sites with 404 errors, search for the new feed URL.
3.  **Implement Browser-Based Scraping:** For sites that block direct feed access (403 errors), a browser-based scraping approach using a tool like Playwright or Selenium might be necessary. This is more complex but can bypass some anti-scraping measures.
4.  **Add More Sources:** Continuously search for new and reliable medical news RSS feeds to expand the reach of the aggregator.
