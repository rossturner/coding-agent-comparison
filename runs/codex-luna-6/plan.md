# Coloring Book Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Page Formatting tool that converts ordered images to an A4 PDF with an image page followed by a blank page for duplex printing.

**Architecture:** Add a dedicated conversion endpoint and a PDF utility path that reuses existing image decoding and placement with `maintainAspectRatio` and auto-rotation enabled. Register a focused frontend tool that sends selected images in order through FileContext and uses the normal operation result flow.

**Tech Stack:** Java 25, Spring Boot 4, PDFBox, React, TypeScript, Mantine, Vitest, JUnit.

**Spec:** `docs/superpowers/specs/2026-10-01-coloring-book-tool-design.md`

## Global Constraints

- Preserve input order and place each generated image page on A4 with aspect ratio preserved.
- Use `fitOption=maintainAspectRatio` and `autoRotate=true`; generic Image to PDF defaults do not meet this tool's contract.
- Add one blank page after every generated image page, with matching dimensions.
- Do not change the general Image to PDF endpoint behavior.
- Update frontend translations in `en-US` only.
- Use `@app/*` imports and route file selection through FileContext.
- Keep the API models generated from the Java OpenAPI spec with `task frontend:tool-models`.

## Review Focus

- Multiple inputs must preserve their submitted order; test rendered image markers on alternating pages.
- Multi-frame TIFFs must produce one image/blank pair per frame; test page count and frame order.
- Portrait and landscape inputs must use portrait and landscape A4 respectively; test page dimensions and preserved image bounds.
- An empty request or a non-image/malformed file must fail without returning partial output; test endpoint validation and utility failure.
- A frontend selection containing supported images must submit every image in the visible order; test multipart fields and file names.

---

### Task 1: Add coloring-book PDF generation

**Files:**
- Modify: `app/common/src/main/java/stirling/software/common/util/PdfUtils.java`
- Create: `app/common/src/test/java/stirling/software/common/util/PdfUtilsColoringBookTest.java`

**Interfaces:**
- Produces: `PdfUtils.imageToPdfWithBlankPages(MultipartFile[] files, CustomPDFDocumentFactory pdfDocumentFactory) throws IOException`, returning PDF bytes.
- The method generates full-color image pages, uses aspect-preserving A4 placement with automatic orientation, and inserts a same-sized blank page after each generated image page.

- [ ] **Step 1: Write failing PDF utility tests**

Create tests for two ordered PNG inputs, a portrait plus a landscape image, a multi-frame TIFF, a non-image upload, and a malformed image. Load successful output bytes with PDFBox. Assert that every odd page contains its matching image marker, every even page has no image/content, each blank page matches the prior page dimensions, page count is twice the generated image-page count, and image bounds preserve the source aspect ratio. Assert that invalid inputs throw without returning partial output.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `./gradlew :common:test --tests 'stirling.software.common.util.PdfUtilsColoringBookTest'`

Expected: FAIL because `imageToPdfWithBlankPages` is not implemented.

- [ ] **Step 3: Implement the PDF utility path**

Implement `imageToPdfWithBlankPages` by sharing the current image decoding, EXIF orientation, color conversion, TIFF frame handling, and page placement. Invoke placement with `maintainAspectRatio` and `autoRotate=true`. Add each blank page immediately after its corresponding image page using that page's media box; do not alter existing `imageToPdf` defaults or behavior.

- [ ] **Step 4: Re-run the focused tests**

Run: `./gradlew :common:test --tests 'stirling.software.common.util.PdfUtilsColoringBookTest'`

Expected: PASS for order, blank-page alternation, frame handling, orientation, aspect ratio, and malformed input.

- [ ] **Step 5: Commit the utility and tests**

```bash
git add app/common/src/main/java/stirling/software/common/util/PdfUtils.java app/common/src/test/java/stirling/software/common/util/PdfUtilsColoringBookTest.java
git commit -m "feat: generate coloring book PDFs"
```

### Task 2: Expose a dedicated image-to-coloring-book endpoint

**Files:**
- Create: `app/core/src/main/java/stirling/software/SPDF/model/api/converters/ColoringBookRequest.java`
- Modify: `app/core/src/main/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFController.java`
- Create: `app/core/src/test/java/stirling/software/SPDF/controller/api/converters/ConvertColoringBookControllerTest.java`
- Generate: `frontend/editor/src/core/types/toolApiTypes.ts`
- Generate: `frontend/editor/src/core/types/toolIO.ts`

**Interfaces:**
- Consumes: `PdfUtils.imageToPdfWithBlankPages(MultipartFile[], CustomPDFDocumentFactory)` from Task 1.
- Produces: `POST /api/v1/convert/img/pdf/coloring-book`, accepting multipart field `fileInput` with one or more images and returning one PDF.
- The endpoint has `@ToolIO(accepts = ToolFormat.IMAGE, imageIOInput = true, produces = ToolFormat.PDF, arity = ToolArity.MISO)` and rejects a missing or empty image array.

- [ ] **Step 1: Write failing endpoint tests**

Test that a valid ordered image array delegates to `PdfUtils.imageToPdfWithBlankPages` and returns a PDF response, and that a null or empty array is rejected. Verify the response filename is derived from the first input with a `_coloring_book.pdf` suffix.

- [ ] **Step 2: Run endpoint tests and confirm failure**

Run: `./gradlew :stirling-pdf:test --tests 'stirling.software.SPDF.controller.api.converters.ConvertColoringBookControllerTest'`

Expected: FAIL because the request model and endpoint do not exist.

- [ ] **Step 3: Add the request model and endpoint**

Define `ColoringBookRequest` with required `MultipartFile[] fileInput`. Add an `@AutoJobPostMapping` endpoint at `/img/pdf/coloring-book` in `ConvertImgPDFController`, annotate it with `@StandardPdfResponse`, `@ToolIO`, and an OpenAPI operation description, validate the input array, delegate to Task 1, and return the PDF bytes.

- [ ] **Step 4: Re-run endpoint tests**

Run: `./gradlew :stirling-pdf:test --tests 'stirling.software.SPDF.controller.api.converters.ConvertColoringBookControllerTest'`

Expected: PASS.

- [ ] **Step 5: Generate frontend API models**

Run: `task frontend:tool-models`

Expected: generated `ToolEndpoint` includes `/api/v1/convert/img/pdf/coloring-book`; its request parameters contain no scalar fields, and `toolIO.ts` identifies image input and PDF output.

- [ ] **Step 6: Commit the endpoint and generated contract**

```bash
git add app/core/src/main/java/stirling/software/SPDF/model/api/converters/ColoringBookRequest.java app/core/src/main/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFController.java app/core/src/test/java/stirling/software/SPDF/controller/api/converters/ConvertColoringBookControllerTest.java frontend/editor/src/core/types/toolApiTypes.ts frontend/editor/src/core/types/toolIO.ts
git commit -m "feat: expose coloring book conversion endpoint"
```

### Task 3: Add and register the Coloring book frontend tool

**Files:**
- Modify: `frontend/editor/src/core/types/toolId.ts`
- Modify: `frontend/editor/src/core/data/useTranslatedToolRegistry.tsx`
- Create: `frontend/editor/src/core/tools/ColoringBook.tsx`
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookParameters.ts`
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.ts`
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts`
- Modify: `frontend/editor/src/core/utils/urlMapping.ts`
- Modify: `frontend/editor/src/core/data/urlSeoOverrides.json`
- Modify: `frontend/editor/public/locales/en-US/translation.toml`
- Modify: `frontend/editor/src/core/tests/stubbed/all-tool-pages-load.spec.ts`
- Modify: `frontend/editor/src/core/data/automatableToolsHaveOperationConfig.test.tsx`
- Create: `frontend/editor/src/core/utils/urlMapping.test.ts`

**Interfaces:**
- Consumes: generated endpoint `/api/v1/convert/img/pdf/coloring-book` from Task 2.
- Produces: regular tool ID and registry key `coloringBook`, `coloringBookOperationConfig` using `defineMultiFileTool`, operation type `coloringBook`, ordered `fileInput` multipart fields, and URL alias `/coloring-book`.
- The tool has no user-adjustable parameters; it belongs to `ToolCategoryId.STANDARD_TOOLS` and `SubcategoryId.PAGE_FORMATTING`, accepts multiple image files, and uses the standard result flow.

- [ ] **Step 1: Write failing operation, registry, and URL tests**

Test that the operation targets the generated endpoint, includes every input as repeated `fileInput` fields in original order, and sends no fit/color settings. Assert the translated catalog registers `coloringBook` under Page Formatting with the endpoint and operation config. Assert `/coloring-book` maps to `coloringBook`.

- [ ] **Step 2: Run the focused frontend tests and confirm failure**

Run: `cd frontend/editor && npx vitest run src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts src/core/data/automatableToolsHaveOperationConfig.test.tsx src/core/utils/urlMapping.test.ts`

Expected: FAIL because the operation, tool ID, registry entry, and URL mapping do not exist.

- [ ] **Step 3: Implement the operation and tool identity**

Add `coloringBook` to `CORE_REGULAR_TOOL_IDS`. Create an empty parameter model with `{}` defaults and always-valid parameters. Use `defineMultiFileTool` to append selected files to `fileInput`, operation type `coloringBook`, endpoint `/api/v1/convert/img/pdf/coloring-book`, and standard PDF response handling. Expose `useColoringBookOperation` with the standard translated error handler.

- [ ] **Step 4: Implement the tool component, registry, and route**

Create `ColoringBook.tsx` using `useBaseTool` with a minimum of one file and viewer scope ignored so the full selected image set is processed. Use the standard file, execute, result, undo, and error flow without a settings step. Register `coloringBook` with the existing `book-open` icon, Page Formatting category, unlimited files, endpoint-based image eligibility, operation config, `automationSettings: null`, and English name/description translations. Add `/coloring-book` and SEO metadata. Add the tool to the page-load smoke fixture.

- [ ] **Step 5: Re-run operation, registry, and URL tests**

Run: `cd frontend/editor && npx vitest run src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts src/core/data/automatableToolsHaveOperationConfig.test.tsx src/core/utils/urlMapping.test.ts`

Expected: PASS; the tool submits the selected images in order and is registered under Page Formatting.

- [ ] **Step 6: Run the page-load smoke test**

Run: `cd frontend/editor && npx playwright test src/core/tests/stubbed/all-tool-pages-load.spec.ts --project=stubbed`

Expected: the new tool page loads without runtime errors.

- [ ] **Step 7: Commit the frontend tool**

```bash
git add frontend/editor/src/core/types/toolId.ts frontend/editor/src/core/data/useTranslatedToolRegistry.tsx frontend/editor/src/core/tools/ColoringBook.tsx frontend/editor/src/core/hooks/tools/coloringBook frontend/editor/src/core/utils/urlMapping.ts frontend/editor/src/core/data/urlSeoOverrides.json frontend/editor/public/locales/en-US/translation.toml frontend/editor/src/core/tests/stubbed/all-tool-pages-load.spec.ts frontend/editor/src/core/data/automatableToolsHaveOperationConfig.test.tsx frontend/editor/src/core/utils/urlMapping.test.ts
git commit -m "feat: add Coloring book page formatting tool"
```

### Task 4: Run required quality checks and close generated changes

**Files:**
- Verify the Java backend, frontend, generated tool models, and changed translations.

**Interfaces:**
- Consumes: completed endpoint and frontend tool from Tasks 1–4.
- Produces: verified backend/frontend implementation with committed generated models and translations.

- [ ] **Step 1: Run backend quality checks**

Run: `task backend:check`

Expected: backend tests, formatting, lint, and type/build checks pass.

- [ ] **Step 2: Run frontend quality checks**

Run: `task frontend:check`

Expected: frontend tests, lint, typecheck, and formatting checks pass.

- [ ] **Step 3: Verify generated models**

Run: `task frontend:tool-models:check`

Expected: generated API contracts are current.

- [ ] **Step 4: Format changed translations**

Run: `task pre-commit:fix`

Expected: translation formatting/conversion completes with only the required English source change.

- [ ] **Step 5: Review the final diff**

Run: `git diff --check && git status --short`

Expected: no whitespace errors; the status contains only check-generated or formatting changes related to this feature.

- [ ] **Step 6: Commit required check-generated changes**

If Step 5 reports check-generated or formatting changes, stage only those exact paths and commit them with `chore: update generated coloring book contracts`. If Step 5 reports a clean tree, mark this step skipped.
