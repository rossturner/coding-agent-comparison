# Coloring book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Coloring book under Page Formatting, producing one A4 portrait PDF with an empty back after every supplied image.

**Architecture:** A dedicated multipart backend endpoint composes images and blank backs through existing PDFBox image helpers. A standard core frontend tool uses an opt-in strict batch policy and generated input metadata. Original images survive the mobile upload flow while this tool is active.

**Tech Stack:** Spring Boot 4.1.1, JDK 25 toolchain, PDFBox, ImageIO, React, TypeScript, Mantine, Vitest, JUnit.

**Spec:** `docs/superpowers/specs/2026-10-01-coloring-book-design.md`

## Global Constraints

- Every page is A4 portrait (approximately 595.276 by 841.890 PDF points).
- For N decoded images, output contains exactly 2N pages.
- Original colors are preserved. Landscape images fit inside portrait pages.
- Images retain the current selected file order. No implicit filename sorting occurs.
- Each decoded TIFF frame receives a blank back; retain existing non-TIFF animation behavior.
- FileContext remains the authority for input selection, ordering, processing results, undo, and resource lifecycle.
- All application imports use `@app/*`.
- Add user-facing translations only to `frontend/editor/public/locales/en-US/translation.toml`.
- No settings panel is needed. No AI engine changes or new product dependencies.
- Existing converter and shared hook behavior remains the default for other tools.
- Run `task frontend:check` and `task backend:check`; run `task pre-commit:fix` after translation changes. Do not run frontend production builds manually.
- Follow actual Spring/Jackson imports in this checkout; Jackson code, if needed, uses `tools.jackson`.

## Review Focus

- A valid image mixed with an empty or unsupported file must fail as a whole batch, including direct hook execution.
- Opening one of several images in the viewer must not shrink the book or alter its order.
- A corrupt later TIFF frame must fail without returning earlier pages as a successful partial book.
- Mobile upload must preserve an original image for this tool even when global scanner conversion is enabled.
- A misleading image filename/MIME type must not bypass backend decoding validation; reported names must be safe.

## Execution setup

- [ ] Read the spec and this plan, repository instructions, and the required execution, isolation, and test-driven development skills. Check working tree state before modifying anything. Preserve the approved spec and plan in the execution checkout.
- [ ] Use the execution method selected by the user. Complete each task's red/green cycle and relevant quality gates before its implementation commit. Use repository Task commands for full gates; targeted test invocations below are diagnostic runs, not substitutes for those gates.

## Task 1: Compose image pages with blank backs

**Files:**
- Modify: `app/common/src/main/java/stirling/software/common/util/PdfUtils.java`
- Modify only where needed for stream ownership: `app/common/src/main/java/stirling/software/common/util/ImageProcessingUtils.java`
- Create test: `app/common/src/test/java/stirling/software/common/util/ColoringBookPdfTest.java`

**Interfaces:**
- Consumes: existing `PdfUtils.imageToPdf(...)`, `addImageToDocument(...)`, ImageIO/EXIF decoder, `CustomPDFDocumentFactory.createNewDocument()`.
- Produces: `PdfUtils.createColoringBook(MultipartFile[] files, CustomPDFDocumentFactory pdfDocumentFactory): byte[]`, throwing `IOException` for decode failures and `IllegalArgumentException` for invalid batches. It owns and closes its document; inputs remain caller-owned. Preserve the existing five-argument `imageToPdf` signature and behavior.

- [ ] **Write failing composition tests.** Generate small distinguishable PNG/JPEG fixtures and a two-frame TIFF in memory. Assert one input yields two pages and three ordered inputs yield six. Compare each media box with `PDRectangle.A4` within 0.01 points. Render even pages and assert all pixels are white; inspect their content/resources to ensure no painted image. Render odd pages to identify input order.
- [ ] **Add geometry and failure assertions.** For portrait, square, and landscape fixtures, inspect the image placement matrix against `scale=min(A4.width/image.width, A4.height/image.height)` and centered offsets within 0.01 points. Assert colored interior pixels remain colored and landscape pages stay portrait. Assert TIFF frames appear on pages 1 and 3. Assert empty/null batches, empty files, valid-plus-corrupt files, and a corrupt later TIFF frame throw without returning output. Test mismatched MIME/filename data and EXIF-oriented JPEG placement using an existing fixture where available or an in-memory EXIF fixture.
- [ ] **Run the tests red.** Run `./gradlew :common:test --tests '*ColoringBookPdfTest'`. Expected: missing `createColoringBook` or failed behavioral assertions.
- [ ] **Implement composition.** Add the public method above. Delegate to a private composition overload carrying a `boolean blankBacks`, fixed `maintainAspectRatio`, `autoRotate=false`, and `color`. Keep the existing public converter delegation at `blankBacks=false`. Thread the private flag through single-image and TIFF-frame append paths; append `new PDPage(PDRectangle.A4)` immediately after each successfully drawn image when enabled. Validate every file, identify failing inputs with sanitized names, and close documents/readers/streams on failure. Repair stream ownership in the existing decoder only where this path requires it; do not create a parallel decoder or serialize/reload the intermediate PDF.
- [ ] **Run green and regressions.** Run `./gradlew :common:test --tests '*ColoringBookPdfTest' --tests '*PdfUtils*'`, then `task backend:format` and `task backend:check`. Expected: passing tests and gate; inspect formatting diff for unrelated edits.
- [ ] **Commit this deliverable.** Stage only the listed implementation/test files that changed; commit `feat: compose coloring book PDFs with blank backs`.

## Task 2: Expose the dedicated API and generated contracts

**Files:**
- Create: `app/core/src/main/java/stirling/software/SPDF/controller/api/ColoringBookController.java`
- Create: `app/core/src/main/java/stirling/software/SPDF/model/api/general/ColoringBookRequest.java`
- Create test: `app/core/src/test/java/stirling/software/SPDF/controller/api/ColoringBookControllerTest.java`
- Regenerate: `SwaggerDoc.json`, `frontend/editor/src/core/types/toolApiTypes.ts`, `frontend/editor/src/core/types/toolIO.ts`

**Interfaces:**
- Consumes: Task 1 `PdfUtils.createColoringBook(files, pdfDocumentFactory)`.
- Produces: `ColoringBookRequest.getFileInput(): MultipartFile[]`; controller `createColoringBook(@ModelAttribute ColoringBookRequest request): ResponseEntity<byte[]>` at `POST /api/v1/general/coloring-book`.
- Generated endpoint: `ToolApiParams['/api/v1/general/coloring-book']`; generated file field `fileInput`; endpoint availability key `coloring-book`.

- [ ] **Write failing controller tests.** Assert ordered multipart input reaches composition, successful response is a PDF attachment ending `_coloring_book.pdf`, empty input fails before filename indexing, and decode failures propagate through existing API error conventions. Include a path-like source filename and verify a safe attachment name. Verify endpoint annotations declare IMAGE, ImageIO input discovery, PDF, and MISO.
- [ ] **Run red.** Run `./gradlew :stirling-pdf:test --tests '*ColoringBookControllerTest'`. Expected: missing controller/request or failed assertions.
- [ ] **Implement request and controller.** Use existing Lombok request conventions and Swagger schema for required ordered `fileInput`. Use `@RequestMapping('/api/v1/general')`, `AutoJobPostMapping` with multipart consumption and `ResourceWeight.LARGE_WEIGHT`, `ToolIO`, and `StandardPdfResponse` as in the image converter. Inject the document factory, delegate to Task 1, and return through `WebResponseUtils.bytesToWebResponse` and existing safe filename helpers. Declare caller-facing contract comments only when they add information.
- [ ] **Run green and generate metadata.** Run the controller test, `task backend:format`, and `task frontend:tool-models`. Inspect generated contracts for the exact endpoint, `fileInput`, ImageIO extensions, and MISO. Preserve generated changes for this endpoint and investigate unrelated generation drift rather than hand-editing generated declarations.
- [ ] **Verify gates and commit.** Run `task backend:check` and `task frontend:check` for changed generated frontend files. Commit `feat: expose coloring book API and tool contracts` with only the listed files.

## Task 3: Make strict batches explicit in the shared operation hook

**Files:**
- Modify: `frontend/editor/src/core/hooks/tools/shared/toolOperationTypes.ts`
- Modify: `frontend/editor/src/core/hooks/tools/shared/useToolOperation.ts`
- Create test: `frontend/editor/src/core/hooks/tools/shared/useToolOperation.strictBatch.test.ts`
- Modify translation: `frontend/editor/public/locales/en-US/translation.toml`

**Interfaces:**
- Consumes: generated endpoint metadata and `toolAcceptsFile(endpoint, stub)`.
- Produces: optional `strictBatch?: boolean` on `BaseToolOperationConfig`; defaults to false. When true, `getEligibleFiles(params, files)` retains the supplied batch and `executeOperation(params, files)` rejects any incompatible/zero-byte member before filtering or API requests.

- [ ] **Write failing hook tests.** Use renderHook with mocked FileContext/API/resource seams. With strict mode, assert valid-plus-empty and valid-plus-PDF inputs remain visible, execution reports the offending filename, API is never called, no inputs are consumed, and loading is false. Call `executeOperation` directly to cover non-UI callers. Assert a valid batch preserves order; default mode retains current filtering behavior. Assert corrupted valid-looking data rejected by the backend produces an error and no successful consumption.
- [ ] **Run red.** Run `cd frontend && npx vitest run --root editor src/core/hooks/tools/shared/useToolOperation.strictBatch.test.ts`. Expected: strict-mode assertions fail or the new configuration property is missing.
- [ ] **Implement the opt-in policy.** Add the configuration property with a contract explaining all-or-nothing semantics. Keep invalid files in the memoized eligible list for strict mode. At execution validation, find invalid supplied members using existing compatibility rules and size checks, set a translated error with their names, and return before API execution. Preserve policy guards and existing default behavior. Add the error copy in en-US only.
- [ ] **Run green and gates.** Run the targeted hook tests, `task pre-commit:fix`, and `task frontend:check`. Inspect all auto-fix changes. Expected: strict tests and existing shared hook tests pass.
- [ ] **Commit.** Commit the listed changes as `feat: support all-or-nothing tool input batches`.

## Task 4: Add the Coloring book frontend tool

**Files:**
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookParameters.ts`
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.ts`
- Create: `frontend/editor/src/core/tools/ColoringBook.tsx`
- Modify: `frontend/editor/src/core/types/toolId.ts`
- Modify: `frontend/editor/src/core/data/useTranslatedToolRegistry.tsx`
- Modify: `frontend/editor/public/locales/en-US/translation.toml`
- Create tests: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts`, `frontend/editor/src/core/tools/ColoringBook.test.tsx`

**Interfaces:**
- Consumes: generated endpoint contracts and Task 3 `strictBatch`.
- Produces: tool ID `coloringBook`; `ColoringBookParameters = Record<string, never>`; `defaultParameters: ColoringBookParameters = {}`; `useColoringBookParameters(): BaseParametersHook<ColoringBookParameters>`.
- Operation exports: `buildColoringBookFormData(parameters: ColoringBookParameters, files: File[]): FormData`, `coloringBookOperationConfig`, and `useColoringBookOperation()` using the standard hook return type.

- [ ] **Write failing mapping and tool tests.** Assert FormData.getAll('fileInput') exactly equals an intentionally reordered input list. Assert the registry declares STANDARD_TOOLS/PAGE_FORMATTING and the correct endpoint. Render the tool with mocked dependencies and assert minFiles=1, the full displayed batch survives viewer switching, and empty/unavailable states disable execution. Verify a successful PDF uses the standard review callbacks and undo path; invalid batches remain visible with errors.
- [ ] **Run red.** Run `cd frontend && npx vitest run --root editor src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts src/core/tools/ColoringBook.test.tsx`. Expected: missing modules or failed tool behavior assertions.
- [ ] **Implement parameter and operation hooks.** Parameters use `useBaseParameters` with endpointName `coloring-book`. Define the operation using `defineMultiFileTool`, endpoint `/api/v1/general/coloring-book`, `strictBatch:true`, operationType `coloringBook`, `preserveBackendFilename:true`, and generated API mapping via `objectToFormData({}, {fileInput:files})`. Use the standard translated error handler. Keep defaults stable and do not add synthetic user settings.
- [ ] **Implement tool and registration.** Use `useBaseTool(..., {minFiles:1, ignoreViewerScope:true})` and `createToolFlow`. Display the explanation that each image fits an A4 page with a blank back for duplex printing. Use button copy `Create coloring book`, standard review/preview/undo handlers, and disable viewer scope hints for this batch tool. Register a lazy component, operation config, no settings component, `maxFiles:-1`, and existing `book-open` icon. Add `coloringBook` to core tool IDs. Use existing FileEditor removal/reorder controls; the displayed loaded list is the batch, independent of highlights.
- [ ] **Run green and gates.** Run both targeted tests, `task pre-commit:fix`, and `task frontend:check`. Confirm generated input compatibility rejects PDF and accepts advertised image extensions.
- [ ] **Commit.** Commit the listed changes as `feat: add Coloring book to Page Formatting`.

## Task 5: Preserve original images in the mobile picker flow

**Files:**
- Modify: `frontend/editor/src/core/components/FileManager.tsx`
- Modify: `frontend/editor/src/core/components/filesPage/LibraryFilePicker.tsx`
- Modify: `frontend/editor/src/core/components/shared/MobileUploadModal.tsx`
- Modify test: `frontend/editor/src/core/components/filesPage/LibraryFilePicker.test.tsx`
- Create test: `frontend/editor/src/core/components/shared/MobileUploadModal.test.tsx`
- Create test: `frontend/editor/src/core/components/FileManager.test.tsx`

**Interfaces:**
- Produces: optional `preserveImages?: boolean` prop on LibraryFilePicker and MobileUploadModal, default false. FileManager obtains `selectedTool` ID from `useNavigationState()` and passes true only for `coloringBook`.
- Consumes: existing `onFilesReceived(files:File[])` and existing FilesModalContext ingestion. The option changes image conversion only; ingestion and storage still use their existing ownership paths.

- [ ] **Write failing upload tests.** With global scanner conversion enabled and preserveImages=true, trigger received image and assert the exact original File reaches onFilesReceived and the converter is not called. With preserveImages omitted, assert existing conversion still runs. Assert non-image input is unchanged. Test LibraryFilePicker forwards the option to its modal and FileManager enables it only for Coloring book.
- [ ] **Run red.** Run `cd frontend && npx vitest run --root editor src/core/components/shared/MobileUploadModal.test.tsx src/core/components/filesPage/LibraryFilePicker.test.tsx src/core/components/FileManager.test.tsx`. Expected: preservation assertions fail or new props are missing.
- [ ] **Implement the narrow option.** Thread preserveImages through the picker/modal and make conversion conditional on `!preserveImages` plus existing config. Keep displayed mobile conversion information consistent with actual behavior. Obtain tool identity in FileManager rather than teaching the generic modal a tool ID; do not change standalone AddToLibraryModal behavior.
- [ ] **Run green and gate.** Run the targeted tests and `task frontend:check`. Expected: original images preserved for Coloring book and previous scanner behavior retained elsewhere.
- [ ] **Commit.** Commit the listed changes as `fix: preserve coloring book images during mobile upload`.

## Task 6: Verify the assembled feature and review it

**Files:** No product files are planned here. If verification reveals a defect, fix the owning task's files and add its regression test before repeating the relevant gate.

**Interfaces:** Consumes the completed API, UI, metadata, strict-batch policy, and upload option.

- [ ] **Run final repository checks.** Run `task backend:check`, `task frontend:check`, and `task pre-commit`. Avoid repeating gates when no changes occurred since their last successful run; retain fresh evidence for the assembled branch. Confirm git diff checks and inspect generated artifacts and changes outside planned files.
- [ ] **Exercise the authenticated local UI.** Use the supplied local administrator credentials without persisting them. Confirm Coloring book appears under Page Formatting; load three distinguishable images with portrait/landscape/square dimensions, reorder them, switch viewer context, create the book, preview/download it, and undo. Confirm all six A4 portrait pages are in image/blank order with the final blank. Inspect the actual downloaded PDF using PDFBox or an available PDF inspection utility, not only browser thumbnails.
- [ ] **Exercise failures and mobile preservation.** Submit a valid image plus a corrupt or empty image through available UI/API paths and verify no partial book. Verify API empty input rejection and invalid input naming. Exercise the mobile modal receive seam with scanner conversion enabled; use its automated test if a phone transfer cannot be performed. Record any unavailable local service/browser/device coverage explicitly.
- [ ] **Request whole-branch review using the execution workflow's review skill.** Focus on resource cleanup, strict-policy defaults, ordered submission, PDF geometry, generated metadata, upload routing, and safe errors. Resolve verified findings and rerun affected checks.
- [ ] **Hand off the result.** Report implementation commits, verification evidence, and any material remaining limits. Do not deploy, push, or merge without authorization.
