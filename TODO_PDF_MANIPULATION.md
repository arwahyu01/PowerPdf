# TODO PDF Manipulation Project

Use this checklist while building the app. Mark items only after verification.

## Core

- [ ] Audit existing codebase and confirm current PDF capabilities
- [ ] Define final feature scope for Python-only PDF manipulation
- [ ] Keep conversion, OCR, and AI features out of scope for now
- [ ] Decide which PDF libraries will be used

## Document Organization

- [ ] Merge PDFs
- [ ] Split PDFs by selected pages
- [ ] Extract selected pages
- [ ] Remove pages
- [ ] Reorder pages via drag and drop
- [ ] Rotate pages
- [ ] Duplicate pages
- [ ] Insert pages from another PDF
- [ ] Reverse page order

## Editing

- [ ] Crop pages
- [ ] Add page numbers
- [ ] Add text watermark
- [ ] Add image watermark if feasible
- [ ] Normalize page size if feasible
- [ ] Replace page

## Metadata and Security

- [ ] Read metadata
- [ ] Edit metadata
- [ ] Preserve bookmarks/outlines if possible
- [ ] Add bookmarks/outlines if feasible
- [ ] Encrypt PDF
- [ ] Decrypt PDF with password
- [ ] Remove encryption for accessible PDFs

## Preview and UX

- [ ] Thumbnail rendering
- [ ] Full page preview modal
- [ ] Loading states
- [ ] Toast feedback
- [ ] Undo and redo for editing actions
- [ ] Mobile responsive layout
- [ ] Modern and intuitive navigation

## Reliability

- [ ] Validate uploaded files
- [ ] Handle corrupted PDFs safely
- [ ] Prevent duplicate operations
- [ ] Fix off-by-one page index risks
- [ ] Clean temporary buffers and files
- [ ] Add error messages that help the user recover

## Verification

- [ ] Test merge with multiple PDFs
- [ ] Test split with a page range and selected pages
- [ ] Test reorder after delete and insert
- [ ] Test rotation preservation on export
- [ ] Test encrypted file handling
- [ ] Test invalid upload handling
- [ ] Cross-check output against expected PDF structure
- [ ] Confirm no incomplete routes or dead buttons remain

