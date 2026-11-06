# Gravely manuals

Source PDFs come from [oldgravelys.net](http://www.oldgravelys.net/) (watermarked on the covers). The number prefix is the oldgravelys.net catalog number.

**The PDFs live in SharePoint, not git:** [`Shared Documents/gravely-tractor-kb`](https://ccfedu.sharepoint.com/sites/MPRSchool/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FMPRSchool%2FShared%20Documents%2Fgravely-tractor-kb) on the MPRSchool site. Keep local copies here for re-OCR; `.gitignore` excludes them. The `../*.pdf` links in the Markdown resolve once everything is uploaded to SharePoint with the same layout.

Contents:
- **`md/`:** one Markdown file per tractor manual, ready for the KB. Each has frontmatter (series, doc type, date, pages, source PDF, text source) and a `## Page N` section per page.
- **`text/`:** raw extracted text, one file per manual.
- **[attachments/](attachments/README.md):** 203 attachment manuals. The 105 relevant to the riding tractors are OCR'd into `attachments/md/`.
- **[parts-index.csv](parts-index.csv):** about 13,400 part rows from every parts table, tractors and attachments together, with columns manual, series, date, page, section, item, part #, qty, description.
- **[8000-vs-G-interchange.md](8000-vs-G-interchange.md):** which 8000-series parts carry over to the Professional G series.

How the text was made:
- PDFs with a usable text layer: extracted directly.
- Scanned PDFs: OCR'd with Windows' built-in engine (`Windows.Media.Ocr`) at 200 dpi, with table rows rebuilt from word positions.

OCR text is good but not perfect. **Always confirm a part number against the PDF page before ordering.** Each text file marks pages with `===== Page N =====`, so you can find the matching PDF page.

> The oldgravelys.net filenames label 0512–0514 "G Series", but the covers say **9000 Series Grounds Maintenance Tractor**. They're listed under 9000 below.

## 8000 series (riders, pre-1987)

| # | Type | Date | Pages |
|---|---|---|---|
| 0499 | Parts Catalog | Aug 1978 | 37 |
| 0500 | Parts Catalog | Aug 1979 | 41 |
| 0501 | Illustrated Parts List | Aug 1981 | 32 |
| 0502 | Operator's Manual | Sep 1978 | 23 |
| 0503 | Operator's Manual | Aug 1980 | 30 |
| 0504 | Service Manual | Mar 1985 | 68 |
| 0505 | Operator's Manual | Jul 1985 | 35 |
| 0506 | Illustrated Parts List | Jul 1985 | 52 |
| 0507 | IPL Addendum, "8000-G Series" (form 41241) | Jan 1986 | 3 |

## 9000 series (Grounds Maintenance Tractor, 1979)

| # | Type | Date | Pages |
|---|---|---|---|
| 0512 | Operator's Manual (form 31196) | May 1979 | 25 |
| 0513 | Parts Catalog (form 31195) | Jul 1979 | 26 |
| 0514 | Service Manual (form 31456) | May 1979 | 107 |

## Professional G series (12-G – 20-G, 24-G), 1986–2001

| # | Type | Date | Pages | Notes |
|---|---|---|---|---|
| 0515 | Operator's Manual (form 42639) | Nov 1986 | 33 | |
| 0226 | Operator's Manual | Jun 1987 | 33 | Replaces form 42639 |
| 0227 | Illustrated Parts List (form 43791, rev 10-87) | Jun 1987 | 52 | Earliest G parts list. It still names 8122 / 8123 / 8163-G (e.g. steering wheel) |
| 0228 | Operator's Manual, Professional 24-G | Jan 1989 | 27 | |
| 0522 | Illustrated Parts List | Feb 1989 | 38 | |
| 0523 | Illustrated Parts List | Aug 1989 | 50 | |
| 0516 | Operator's Manual | Jul 1989 | 28 | |
| 0524 | Illustrated Parts List | Sep 1990 | 46 | |
| 0517 | Operator's Manual | Dec 1990 | 28 | |
| 0525 | Illustrated Parts List | Dec 1990 | 38 | |
| 0526 | IPL Addendum (form 51702) | Mar 1991 | 3 | Reflector revisions, G and 24-G |
| 0518 | Operator's Manual | Jun 1992 | 33 | |
| 0630 | Attachments Operator's Manual Addendum (form 87843) | Jul 1994 | 4 | |
| 0519 | Operator's Manual | Feb 1995 | 35 | |
| 0527 | Parts Catalog | Apr 1995 | 62 | |
| 0520 | Owner/Operator Manual, models 987070/071/072 | Feb 1999 | 24 | Lists attachment 88701100 – 48" Snow Dozer Blade |
| 0528 | Parts Manual 08471600E, models 987070/071/072 | May 2001 | 48 | Ariens 8-digit part numbers |
| 0521 | Service Manual | undated | 48 | |

## Future: Gravely KB

The plan is a Gravely knowledge base on the ccfedu SharePoint. `md/` is the ingest-ready corpus, and `parts-index.csv` is the cross-manual lookup. The PDFs stay as the source of truth for diagrams.
