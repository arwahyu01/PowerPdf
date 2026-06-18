# DeepSeek Prompt for PowerPDF

You are a senior Python engineer and product-minded software architect.

You are working inside an existing Flask-based PDF web app. Your job is to inspect the current codebase first, preserve working behavior, and then extend the app into a powerful PDF workstation inspired by the iLovePDF menu structure.

## Objective

Build a modern, responsive, user-friendly, production-grade PDF web application that mirrors the **tool categories and UX organization** of iLovePDF, while implementing every feature that is realistically safe and maintainable using **Python-only PDF manipulation** in this phase.

Do **not** add OCR, document conversion, AI summarization, translation, or cloud-dependent workflows yet unless they can be done cleanly without external binaries or services.

## Reference Menu Structure

Use iLovePDF as the product reference for information architecture and feature grouping. The app should expose tools in a similar category layout:

- Organize PDF
  - Merge PDF
  - Split PDF
  - Remove pages
  - Extract pages
  - Organize PDF
  - Scan to PDF
- Optimize PDF
  - Compress PDF
  - Repair PDF
  - OCR PDF
- Convert to PDF
  - JPG to PDF
  - WORD to PDF
  - POWERPOINT to PDF
  - EXCEL to PDF
  - HTML to PDF
- Convert from PDF
  - PDF to JPG
  - PDF to WORD
  - PDF to POWERPOINT
  - PDF to EXCEL
  - PDF to PDF/A
- Edit PDF
  - Rotate PDF
  - Add page numbers
  - Add watermark
  - Crop PDF
  - Edit PDF
  - PDF Forms
- PDF Security
  - Unlock PDF
  - Protect PDF
  - Sign PDF
  - Redact PDF
  - Compare PDF
- PDF Intelligence
  - AI Summarizer
  - Translate PDF

## Hard Constraints

- Use Python for backend logic.
- Keep the implementation Python-only for PDF manipulation in this phase.
- Do not depend on LibreOffice, Ghostscript, Tesseract, Node pipelines, Java tools, or cloud APIs.
- Do not introduce fake implementations, placeholder code, or empty TODOs in production code.
- Preserve the existing app structure when it is useful.
- Improve the codebase rather than rewriting good existing functionality without reason.
- Optimize for correctness, maintainability, and reliability first.

## Important Scope Rule

Implement the menu structure first, then fill in the Python-only features that are realistically achievable.

For features that are not cleanly achievable with Python-only tooling, do one of the following:

- exclude them from the first implementation phase
- keep them visible only as disabled or future tools in the UI, if that makes the UX clearer
- explicitly document why they are deferred

Do not force weak implementations for conversion/OCR/AI/security-signing features if the result would be unreliable.

## First Step

Before coding, inspect the repository and identify:

- what features already exist
- what is already stable and should be preserved
- what is missing
- what can be added cleanly with Python-only tooling
- which iLovePDF-style menu groups should be added or expanded in the UI

## UI Requirements

The UI must feel like a serious PDF workstation:

- modern
- attractive
- responsive
- mobile-friendly
- intuitive
- fast to understand
- pleasant to use for repeated document work

UI should include:

- clear category navigation similar to iLovePDF
- card-based tool grid
- drag and drop upload
- thumbnail-based page editor
- visible destructive action warnings
- preview modal
- loading states
- toast notifications
- accessible controls and readable labels
- polished but not cluttered layout

## Python-Only Feature Scope

Implement every feature below that is realistic with Python-only tooling and fits cleanly into the app.

### Organize PDF

- Merge PDF files
- Split PDF by selected pages
- Split PDF by page ranges
- Extract selected pages into a new PDF
- Remove selected pages
- Reorder pages with drag and drop
- Rotate pages individually and in bulk
- Duplicate pages
- Insert pages from another PDF
- Reverse page order
- Move selected pages up/down if useful in the UI
- Organize PDF as a full page-management workspace

### Edit PDF

- Crop pages
- Add page numbers
- Add text watermark
- Add image watermark if feasible without external binaries
- Replace a page with another page if feasible
- Normalize or adjust page dimensions if feasible

### Metadata and Structure

- Read metadata
- Edit metadata
- Inspect basic document information
- Preserve bookmarks/outlines when feasible
- Add or edit bookmarks/outlines if feasible and safe
- Preserve annotations/hyperlinks when feasible

### Security and Validation

- Encrypt PDF with password
- Decrypt/remove encryption when the password is valid
- Validate uploaded PDFs before processing
- Reject invalid, corrupted, or malformed inputs clearly
- Handle password errors and file-read errors gracefully

### Preview and UX

- Thumbnail-based page preview
- Full-page preview modal
- Visual badges for rotation, deletion, selection, and inserted pages
- Undo/redo for edit actions if practical
- Clear loading states
- Clear success/error feedback
- Clean download flow

## Explicitly Deferred for Now

Keep these out of the first implementation unless you can do them cleanly with Python-only tooling and keep them reliable:

- OCR PDF
- Scan to PDF
- Word / PowerPoint / Excel / HTML conversion
- PDF to Word / PowerPoint / Excel conversion
- AI Summarizer
- Translate PDF
- Advanced PDF signing with certificates and trust chains
- Complex PDF forms editor
- Full side-by-side PDF comparison engine

## Architecture Requirements

- Separate PDF processing logic from route handlers and UI logic.
- Use deterministic functions with explicit inputs and outputs.
- Keep page order, page indices, and document state consistent.
- Minimize unnecessary memory use.
- Avoid duplicate logic.
- Make error handling explicit.
- Clean temporary buffers and file objects.
- Reuse the current project patterns where appropriate.

## Reliability Requirements

- Prevent duplicate or invalid page operations.
- Avoid off-by-one errors in page indexing.
- Preserve page order and state across rerenders.
- Handle empty selections safely.
- Do not silently swallow failures.
- Make every destructive action visible to the user.

## Implementation Plan

1. Inspect the current codebase and map existing features.
2. Study the iLovePDF menu structure and mirror the category layout in the UI.
3. Identify the missing Python-only PDF manipulation features.
4. Extend or refactor the PDF engine layer if needed.
5. Wire routes or local handlers to the existing UI.
6. Improve UI/UX without breaking current workflows.
7. Add validation, error handling, and edge-case protection.
8. Verify end-to-end behavior on realistic PDF files.
9. Cross-check the full feature list before declaring completion.

## Mandatory Cross-Check

Before finishing, verify all of the following:

- Every feature exposed in the UI has a working backend or local path.
- Every backend route has a valid UI entry point or deliberate justification if hidden.
- Upload, validation, processing, and download flows work end-to-end.
- Page order is still correct after reorder, insert, delete, rotate, duplicate, reverse, and split.
- Selection state and preview state remain stable after rerendering.
- Corrupted files, invalid PDFs, empty input, and oversized files are handled cleanly.
- No incomplete route, dead button, or broken state path remains.
- No TODOs remain in production code unless explicitly requested.
- The final implementation was checked against realistic PDF files.

## Output Requirements

When you work:

- Start with a concise implementation plan.
- Then implement in small safe steps.
- After each major step, cross-check the result.
- Finish with a short report that lists:
  - what was implemented
  - what was intentionally excluded
  - why anything was excluded
  - what files were changed

If a feature cannot be done cleanly with Python-only tooling, exclude it explicitly and explain why instead of forcing a weak solution.
