# Medical News Feed Sources - Complete List

## 📰 ALL 76 CONFIGURED NEWS SOURCES

Your system is configured to pull from these medical news websites:

### 🌍 GENERAL MEDICAL NEWS (14 sources)
1. **WHO News** - World Health Organization
2. **NIH News** - National Institutes of Health
3. **CDC Newsroom** - Centers for Disease Control
4. **Medscape** - General medical news
5. **MedicalXpress** - Medical research news
6. **News-Medical** - Health & medicine news
7. **ScienceDaily Health & Medicine**
8. **JAMA Network** - Medical research journal
9. **STAT News** - Healthcare news
10. **BMJ News** - British Medical Journal
11. **Healthline Health News**
12. **Healthcare Dive** - Healthcare industry
13. **Healio** - Medical news network
14. **MobiHealthNews** - Digital health

### ❤️ CARDIOLOGY (8 sources)
15. **TCTMD** - Cardiovascular intervention
16. **SCAI** - Society for Cardiovascular Angiography
17. **DI Cardiology** - Diagnostic & interventional
18. **Cardiac Interventions Today**
19. **ESC Press Office** - European Society of Cardiology
20. **JAMA Cardiology**
21. **Cardiology Advisor**
22. **ACC (American College of Cardiology)**

### 🧠 NEUROSURGERY & NEUROLOGY (5 sources)
23. **AANS Neurosurgeon** - American Association of Neurological Surgeons
24. **JAMA Neurology**
25. **Neurology Today**
26. **Practical Neurology**
27. **Neurovascular Today**

### 🦴 ORTHOPEDICS & SPINE (7 sources)
28. **RYOrtho** - Orthopedic news
29. **Ortho Spine News**
30. **Becker's Spine Review**
31. **OrthoBuzz (JBJS)** - Journal of Bone & Joint Surgery
32. **Spine Market Group**
33. **AAOS Now** - American Academy of Orthopedic Surgeons
34. **Pediatric Orthopedics Today**

### 🔬 RADIOLOGY & IMAGING (8 sources)
35. **RSNA News** - Radiological Society of North America
36. **Diagnostic Imaging**
37. **Radiology Today**
38. **Imaging Technology News**
39. **Interventional News** - Interventional radiology
40. **SIR** - Society of Interventional Radiology
41. **DOTmed News** - Medical equipment
42. **Medical Imaging Technology**

### 🎗️ ONCOLOGY (5 sources)
43. **OncLive** - Oncology news
44. **Cancer Network News**
45. **OncoDaily**
46. **ASCO Post** - American Society of Clinical Oncology
47. **Targeted Oncology**

### 🏥 HOSPITAL & HEALTHCARE SYSTEMS (5 sources)
48. **Becker's Hospital Review**
49. **Modern Healthcare**
50. **Advisory Board** - Healthcare strategy
51. **Healthcare IT News**
52. **FierceHealthcare**

### 🤖 SURGICAL ROBOTICS & DEVICES (6 sources)
53. **Intuitive Surgical News** - da Vinci robots
54. **Medtronic News**
55. **Stryker News**
56. **Medical Device Network**
57. **Mass Device** - Medical device news
58. **MD+DI** - Medical Device & Diagnostic Industry

### 🩺 SPECIALTY MEDICAL (18 sources)
59. **Dermatology Times**
60. **Renal & Urology News**
61. **Endocrine News**
62. **Gastroenterology & Endoscopy News**
63. **Pulmonology Advisor**
64. **Infectious Disease Advisor**
65. **Rheumatology Advisor**
66. **Diabetes Care Community**
67. **Endocrinology Advisor**
68. **Hematology Advisor**
69. **Nephrology News & Issues**
70. **Pain Medicine News**
71. **Emergency Medicine News**
72. **Anesthesiology News**
73. **ENT & Audiology News**
74. **Ophthalmology Times**
75. **Psychiatric Times**
76. **Family Practice News**

---

## 🔧 How It Works

The system:
1. **Auto-discovers RSS feeds** from these websites
2. **Fetches articles concurrently** (10 sites at once)
3. **Completes in ~30 seconds** (used to take 5+ minutes!)
4. **Updates every 15 minutes** automatically

## 📝 To Add More Sources

Edit `/Users/mustafaahmed/News feed/sites.yaml`:

```yaml
sites:
  - name: Your Site Name
    url: https://example.com
    feeds:
      - https://example.com/rss.xml  # Optional explicit feed
```

Then restart the server!

---

## 🎯 Quick Access

- **View all sites**: http://127.0.0.1:8000/sites
- **Search articles**: http://127.0.0.1:8000/articles?q=keyword
- **Filter by site**: http://127.0.0.1:8000/articles?site=WHO%20News

