# Coloring Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Page Formatting tool that turns ordered images into one A4 PDF with a blank page behind every image page.

**Architecture:** Extend the existing image-to-PDF request with a false-by-default interleaving flag and insert matching blank pages in the existing PDFBox conversion path. Add a dedicated editor tool that submits all selected images in order through that endpoint with fixed print settings.

**Tech Stack:** Java, Spring Boot, PDFBox, OpenAPI-generated TypeScript and Python models, React, TypeScript, Vitest.

**Spec:** [2026-10-02-coloring-book-design.md](../specs/2026-10-02-coloring-book-design.md)

## Global Constraints

- `interleaveBlankPages` is opt-in and defaults to false; existing callers retain their current output.
- Use A4 pages, auto-orient each page to its image, and preserve image proportions without cropping or distortion.
- Preserve selected image order; add an empty page after every generated image page using the same page dimensions and orientation.
- Use the existing `POST /api/v1/convert/img/pdf` endpoint; do not add a second conversion endpoint or browser-side PDF generation.
- Do not add user-selectable page-size, fit, color, or blank-page settings.
- Supported image formats remain those accepted by the existing image-to-PDF endpoint.
- Regenerate API models from the Java OpenAPI spec; do not hand-edit generated models.
- Use `@app/*` imports for normal frontend code and render icons with the shared `<Icon>` component.
- Update only `frontend/editor/public/locales/en-US/translation.toml`; run `task pre-commit:fix` after changing translations.
- Run `task backend:check`, `task frontend:check`, `task engine:check`, and `task tool-models:check` for the affected code and generated models.

## Review Focus

- **One image:** the result is exactly two pages, with the image first and a blank page second. Pin this in Task 1.
- **Portrait and landscape images together:** retain file order, orient each A4 page correctly, and match each blank page to its preceding image page. Pin this in Task 1.
- **Multi-frame TIFF:** insert a blank after every generated frame, not after the entire TIFF. Pin this in Task 1.
- **Flag omitted by existing callers:** preserve the current un-interleaved output. Pin this in Task 1.
- **Empty or invalid input:** keep execution disabled with no selected images; surface conversion errors without producing a partial result. Pin these in Tasks 1 and 2.

---

### Task 1: Add Back-Side Pages to Image-to-PDF Conversion

**Files:**
- Modify: `app/core/src/main/java/stirling/software/SPDF/model/api/converters/ConvertToPdfRequest.java`
- Modify: `app/core/src/main/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFController.java`
- Modify: `app/common/src/main/java/stirling/software/common/util/PdfUtils.java`
- Test: `app/core/src/test/java/stirling/software/SPDF/model/api/converters/ConvertToPdfRequestTest.java`
- Test: `app/core/src/test/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFControllerMoreTest.java`
- Test: `app/common/src/test/java/stirling/software/common/util/PdfUtilsMoreTest.java`

**Interfaces:**
- Consumes the existing `PdfUtils.imageToPdf(files, fitOption, autoRotate, colorType, pdfDocumentFactory)` path and the existing `ConvertToPdfRequest`.
- Produces `ConvertToPdfRequest.interleaveBlankPages`, a Boolean field initialized to false, and an overload:

```java
byte[] imageToPdf(
        MultipartFile[] files,
        String fitOption,
        boolean autoRotate,
        String colorType,
        boolean interleaveBlankPages,
        CustomPDFDocumentFactory pdfDocumentFactory)
        throws IOException
```

- Retains the existing `imageToPdf` signature and behavior by delegating it to the new overload with `interleaveBlankPages=false`.

- [ ] **Step 1: Write the failing PDF-output and request tests**

In `PdfUtilsMoreTest`, add tests that use valid raster inputs and the existing two-frame TIFF fixture:

- One image produces exactly two pages: page 1 contains the image and page 2 is blank.
- Two ordered images produce four pages; pages 1 and 3 contain the images in input order, while pages 2 and 4 contain no image objects.
- Each blank page has the same media box as the image page before it. Include portrait and landscape inputs.
- A two-frame TIFF produces four interleaved pages, with each frame followed immediately by a blank page.
- An invalid image throws an `IOException` rather than returning a successful partial PDF.
- The existing overload still produces one page per generated image frame.

In `ConvertToPdfRequestTest`, assert the new field defaults to false and round-trips true. In `ConvertImgPDFControllerMoreTest`, assert that an omitted/false value passes false to `PdfUtils` and true passes true.

- [ ] **Step 2: Run the backend tests to verify the new behavior is missing**

Run: `task backend:test`

Expected: FAIL because the request field and interleaving overload/behavior are not implemented.

- [ ] **Step 3: Add the false-by-default request field and wire the controller**

Add `Boolean interleaveBlankPages = false` to `ConvertToPdfRequest` with an OpenAPI schema description and default value. Update the image-to-PDF endpoint description to document the optional duplex blank-page behavior. In `ConvertImgPDFController.convertToPdf`, pass `Boolean.TRUE.equals(request.getInterleaveBlankPages())` to the new `PdfUtils.imageToPdf` overload.

- [ ] **Step 4: Insert a matching blank page after each generated image page**

Add the new `PdfUtils.imageToPdf` overload and keep the existing overload delegating with false. Pass the flag through both `appendSingleImage` and `appendTiffFrames`. Add a flag-aware image-page helper that appends an empty `PDPage` using the generated image page's media box immediately after the image content is written. Keep the existing helper behavior unchanged for calls that do not request interleaving.

- [ ] **Step 5: Run backend tests and quality checks**

Run: `task backend:test`

Expected: PASS, including output order, blank-page placement and dimensions, TIFF frames, error handling, and the false-by-default behavior.

Run: `task backend:check`

Expected: PASS.

- [ ] **Step 6: Commit the backend change**

```bash
git add app/core/src/main/java/stirling/software/SPDF/model/api/converters/ConvertToPdfRequest.java \
  app/core/src/main/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFController.java \
  app/common/src/main/java/stirling/software/common/util/PdfUtils.java \
  app/core/src/test/java/stirling/software/SPDF/model/api/converters/ConvertToPdfRequestTest.java \
  app/core/src/test/java/stirling/software/SPDF/controller/api/converters/ConvertImgPDFControllerMoreTest.java \
  app/common/src/test/java/stirling/software/common/util/PdfUtilsMoreTest.java
git commit -m "feat: support blank backs for image PDFs" \
  -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Add the Coloring Book Editor Tool

**Files:**
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookParameters.ts`
- Create: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.ts`
- Test: `frontend/editor/src/core/hooks/tools/coloringBook/useColoringBookOperation.test.ts`
- Create: `frontend/editor/src/core/tools/ColoringBook.tsx`
- Modify: `frontend/editor/src/core/types/toolId.ts`
- Modify: `frontend/editor/src/core/constants/convertSupportedFornats.ts`
- Modify: `frontend/editor/src/core/data/useTranslatedToolRegistry.tsx`
- Test: `frontend/editor/src/core/data/automatableToolsHaveOperationConfig.test.tsx`
- Test: `frontend/editor/src/core/tests/ToolFileSelection.test.tsx`
- Modify: `frontend/editor/public/locales/en-US/translation.toml`
- Generate: `frontend/editor/src/core/types/toolApiTypes.ts`
- Generate: `engine/src/stirling/models/tool_models.py`

**Interfaces:**
- Consumes Task 1's endpoint field `interleaveBlankPages` and its false-by-default behavior.
- Produces a no-setting `ColoringBookParameters` type, an operation using `defineMultiFileTool`, and a registry entry with stable ID `coloringBook`, endpoint `img-to-pdf`, and subcategory `PAGE_FORMATTING`.
- The operation serializes `autoRotate=true`, `colorType=color`, `fitOption=maintainAspectRatio`, and `interleaveBlankPages=true`, with selected files appended under `fileInput` in order.
- `IMAGE_PDF_SUPPORTED_FORMATS` contains the extension set declared by backend `ToolFormat.IMAGE`: `png`, `jpg`, `jpeg`, `gif`, `webp`, `bmp`, `tif`, `tiff`, `svg`, `psd`, `ai`, and `eps`.

- [ ] **Step 1: Write the failing operation, catalog, and empty-selection tests**

In `useColoringBookOperation.test.ts`, call the exported form-data builder with two distinct `File` objects and assert:

- `formData.getAll("fileInput")` returns those files in the same order.
- `autoRotate`, `colorType`, `fitOption`, and `interleaveBlankPages` serialize to `"true"`, `"color"`, `"maintainAspectRatio"`, and `"true"`.

In `automatableToolsHaveOperationConfig.test.tsx`, assert that `regularTools.coloringBook` exists, has `SubcategoryId.PAGE_FORMATTING`, uses `["img-to-pdf"]`, and has an operation config. Assert `supportedFormats` equals exactly `["png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "svg", "psd", "ai", "eps"]`.

In `ToolFileSelection.test.tsx`, render the Coloring book tool with no selected files and assert its execute button is disabled.

- [ ] **Step 2: Regenerate frontend and engine API models**

Run: `task tool-models`

Expected: `ConvertToPdfRequest` gains `interleaveBlankPages` in `toolApiTypes.ts`, and `ImgToPdfParams` gains `interleave_blank_pages` in `tool_models.py`.

- [ ] **Step 3: Run frontend tests to verify the editor tool is missing**

Run: `task frontend:test`

Expected: FAIL because the Coloring book operation, component, ID, and catalog entry are not implemented.

- [ ] **Step 4: Add the no-settings operation and parameter hook**

In `useColoringBookParameters.ts`, define `ColoringBookParameters` as `BaseParameters`, use `{}` as its default, and bind it to endpoint name `"img-to-pdf"`.

In `useColoringBookOperation.ts`, define `ENDPOINT` as `"/api/v1/convert/img/pdf" satisfies ToolEndpoint`. Use `ToolApiParams[typeof ENDPOINT]` for the request type. Implement `coloringBookToApiParams` with the four fixed settings from the Interfaces block, `coloringBookFromApiParams` returning `{}`, and `buildColoringBookFormData` using `objectToFormData` with `{ fileInput: files }`. Register the configuration with `defineMultiFileTool`, operation type `"coloringBook"`, file prefix `"coloring_book_"`, and the empty default parameters. Use the standard tool error handler.

- [ ] **Step 5: Add the Coloring book tool component**

Create `ColoringBook.tsx` using `useBaseTool` and `createToolFlow`, with no settings steps, the standard execute/review flow, and a one-image minimum. Use the existing `<Icon name="image" size="1.5rem" />`.

- [ ] **Step 6: Register the tool and its image input formats**

Add `"coloringBook"` to `CORE_REGULAR_TOOL_IDS`. Add `IMAGE_PDF_SUPPORTED_FORMATS` in `convertSupportedFornats.ts` using the exact endpoint image-extension set from the Interfaces block; leave `CONVERT_SUPPORTED_FORMATS` unchanged.

Register `coloringBook` in `useTranslatedToolRegistry.tsx` under `ToolCategoryId.STANDARD_TOOLS` and `SubcategoryId.PAGE_FORMATTING`; set `maxFiles: -1`, `supportedFormats: IMAGE_PDF_SUPPORTED_FORMATS`, `endpoints: ["img-to-pdf"]`, `operationConfig: asRegistryConfig(coloringBookOperationConfig)`, and `automationSettings: null`.

Add only the required English strings for the tool title and description, image-selection placeholder, submit button, result title, and error message to `en-US/translation.toml`.

- [ ] **Step 7: Run frontend tests and translation formatting**

Run: `task frontend:test`

Expected: PASS, including request fields/order, catalog registration, supported image formats, and disabled execution with no selected files.

Run: `task pre-commit:fix`

Expected: PASS; translation formatting and repository pre-commit fixes complete.

- [ ] **Step 8: Verify generated models and all affected quality gates**

Run: `task tool-models:check`

Expected: PASS for both generated API model consumers.

Run: `task frontend:check`

Expected: PASS.

Run: `task engine:check`

Expected: PASS.

- [ ] **Step 9: Commit the editor tool**

```bash
git add frontend/editor/src/core/hooks/tools/coloringBook \
  frontend/editor/src/core/tools/ColoringBook.tsx \
  frontend/editor/src/core/types/toolId.ts \
  frontend/editor/src/core/constants/convertSupportedFornats.ts \
  frontend/editor/src/core/data/useTranslatedToolRegistry.tsx \
  frontend/editor/src/core/data/automatableToolsHaveOperationConfig.test.tsx \
  frontend/editor/src/core/tests/ToolFileSelection.test.tsx \
  frontend/editor/src/core/types/toolApiTypes.ts \
  frontend/editor/public/locales/en-US/translation.toml \
  engine/src/stirling/models/tool_models.py
git commit -m "feat: add Coloring Book PDF tool" \
  -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
