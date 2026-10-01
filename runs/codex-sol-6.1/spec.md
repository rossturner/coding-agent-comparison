# Coloring book tool design

## Intent and agreed behavior

Add an OSS tool named **Coloring book** under **Page Formatting**. Users supply an ordered set of images and receive one PDF suitable for duplex printing, with a blank back for every image sheet.

The user approved A4 pages with preserved image proportions, followed by the dedicated backend endpoint approach and the frontend, error handling, and verification design.

The output contract is:

- Every page is A4 portrait (approximately 595.276 by 841.890 PDF points).
- Each image is centered and scaled to the largest size that fits the page, preserving its proportions. White space can remain; there is no extra inset margin.
- Images retain the current selected file order. No implicit filename sorting occurs.
- Image pages occupy positions 1, 3, 5, and so on. Each is followed by a genuinely empty page of the same size, including the final image.
- For N decoded images, output contains exactly 2N pages.
- Original colors are preserved. This tool assembles supplied artwork; it does not generate line art or transform photographs into coloring outlines.
- Landscape images fit inside portrait pages; output orientation stays consistent for printing.

Use the existing backend image decoder capabilities and format discovery rather than inventing a parallel supported-format list. Existing TIFF support expands frames in file order and frame order; each decoded frame receives its own blank back. Do not add animated-image frame extraction beyond existing decoder behavior.

## Architecture and alternatives

Implement a dedicated batch endpoint using shared backend image conversion and PDF placement helpers. One request produces the complete document. The endpoint owns the fixed coloring book behavior; callers cannot disable blank backs or change page sizing.

Alternatives considered:

1. Add a blank-page setting to the general image converter. This reuses its endpoint but couples coloring book behavior to general conversion settings and exposes irrelevant options.
2. Generate the PDF in the browser with PDFium. This avoids a new backend endpoint but puts image decoding and output document memory pressure on the client and complicates support for existing backend image formats.

The dedicated endpoint fits the standard tool pipeline while retaining one explicit output contract. Existing converter callers keep their existing behavior. Shared helper changes must preserve their defaults and avoid converting to bytes and reopening a PDF solely to insert blank pages where document-level composition can be reused.

## Backend components and API

Add a focused controller and multipart request model in the core backend's existing general API structure. Endpoint: `POST /api/v1/general/coloring-book`, with frontend endpoint key `coloring-book`. OpenAPI operation IDs and frontend endpoint keys are separate identifiers; follow the existing generation conventions rather than assuming they are identical.

The request contains ordered repeated `fileInput` parts and no user settings. The response is one `application/pdf` attachment with a safe filename ending in `_coloring_book.pdf`, derived through existing filename utilities.

Use `AutoJobPostMapping` and existing resource scheduling conventions. Declare `ToolIO` as image input, PDF output, and many-input/single-output arity, with ImageIO input discovery. Regenerate committed frontend API and IO artifacts using `task frontend:tool-models`, which consumes backend Swagger. An annotation alone does not update frontend compatibility: unknown endpoints otherwise accept undeclared formats. Review the generated diff and confirm this endpoint has ImageIO-derived extensions and MISO arity in `toolIO.ts` and the corresponding request contract in `toolApiTypes.ts`.

The controller binds and validates the request, delegates document generation to focused shared image/PDF code, and returns the response through existing response helpers. Reuse the current image decoding, EXIF orientation handling, and proportional placement behavior. Use the repository's document factory and deterministic cleanup for documents, image streams, and readers on both success and failure. Decode sequentially rather than retaining all decoded image buffers.

The shared composition boundary must clearly state the ordering, page dimensions, blank-back behavior, resource ownership, and failure semantics in its caller-facing contract. Avoid unrelated refactoring.

## Frontend components and flow

Register tool ID `coloringBook` in `core/data/useTranslatedToolRegistry.tsx` with the standard tools category, `PAGE_FORMATTING` subcategory, batch input, endpoint metadata, and an existing suitable registered icon.

Add a core tool component and its parameter and operation hooks using `useBaseTool`, `createToolFlow`, and `useToolOperation` with the current batch operation configuration conventions. All application imports use `@app/*`.

Pass `ignoreViewerScope: true` to `useBaseTool`, as Merge does, so opening one image in the viewer cannot shrink the book to that image. Preserve the ordered batch across workbench changes. In this design, the selected batch means the tool's displayed loaded-file list in FileContext order: `useViewScopedFiles(true)` returns that full list, rather than the separate `ui.selectedFileIds` subset. Users exclude a loaded file by removing it from the displayed batch; highlighting one file must not change book membership.

The shared operation hook currently filters unsupported and zero-byte files both when deriving eligible files and when executing. Add a narrowly scoped, opt-in strict batch policy for Coloring book, with existing behavior as the default for other tools. In strict mode, keep selected inputs visible and validate the full batch before compatibility or zero-byte filtering; any invalid selected input blocks the operation with an actionable error. Apply the policy in the operation hook so direct operation and automation callers receive the same all-or-nothing behavior. Files outside the displayed batch are not inputs and are not errors.

The user flow is:

1. Select supported images through the existing file selection flow.
2. Review and reorder the selection through existing file controls; the displayed order is the submitted order.
3. Read a short explanation: images fit A4 pages and every image gets a blank back for duplex printing.
4. Click **Create coloring book**.
5. Review, preview, download, or undo the single PDF result through the standard tool review flow.

At least one image is required. No settings panel is needed. Use existing endpoint availability and loading gates. FileContext remains the authority for input selection, ordering, processing results, undo, and resource lifecycle.

Support original image files from local/library selection and the existing mobile upload entry point while this tool is active. MobileUploadModal currently converts images to PDFs by default; add a narrow option passed through its picker integration to preserve received images for Coloring book, overriding that conversion for this flow. Keep existing mobile scanner behavior elsewhere. Previously converted PDFs remain invalid inputs and are visibly rejected; this tool does not attempt to recover original images from PDFs.

Add user-facing translations only to `frontend/editor/public/locales/en-US/translation.toml`, the locale format actually present in this checkout. Use the existing icon component and theme tokens without introducing custom icon markup or literal colors. No platform-specific overrides are required.

## Validation and failure behavior

Reject absent or empty batches, empty files, unsupported inputs, and unreadable images. Identify the offending input safely in user-facing errors using existing error conventions. Fail the whole operation when an input cannot be decoded; never return an apparently successful partial book or silently skip a file.

Backend validation remains authoritative even when frontend filtering prevents invalid selections. Use the standard tool error handler and restore loading state after failures. Do not return an incomplete PDF or retain leaked temporary resources. Authentication and authorization use the existing application rules.

## Verification and acceptance criteria

Backend tests inspect generated PDFs for:

- One image producing two A4 portrait pages, including the final blank back.
- Multiple distinguishable images producing 2N pages in input order.
- Portrait, landscape, and square images being centered and fitted without distortion or cropping.
- Even-numbered pages having no image objects or painted content and rendering entirely white.
- Preserved image colors and existing EXIF orientation behavior.
- TIFF frames each receiving a blank back in frame order.
- Empty batches, empty uploads, unsupported data, and corrupt images failing without partial output.
- Existing image conversion tests remaining passing after any shared helper changes.

Frontend tests verify the ordered multipart batch, minimum input requirement, tool registration/category, and standard result/error integration where meaningful seams exist. Include a valid image mixed with an empty or unsupported selected input: the batch must fail visibly without sending a reduced request or producing a book. Verify the same strict behavior through direct operation execution, batch preservation when switching to the viewer, and original image retention through mobile upload. Verify generated endpoint compatibility restricts inputs to the advertised supported extensions. Avoid tests that merely repeat implementation details.

Run `task frontend:check` and `task backend:check` after implementation changes. Run `task pre-commit:fix` after translation changes and inspect any resulting diff. Do not run frontend production builds manually.

Verify the running local UI with the supplied local administrator credentials, without writing credentials into source, documentation, or test fixtures. Confirm category placement, image selection and reordering, creation, preview, download, undo, and failure recovery. Inspect a downloaded mixed-orientation sample for image/blank alternation and the final blank page. If local services or browser automation are unavailable, record that verification limit explicitly.

## Scope boundaries

No AI engine changes, line-art generation, covers, numbering, borders, margins setting, paper-size setting, orientation setting, grayscale setting, printer control, or booklet imposition. Printing uses the user's existing PDF viewer or printer workflow. No unrelated changes to the general image converter or platform architecture.
