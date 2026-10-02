# Coloring book tool design

## Goal

Add a **Coloring book** tool to the editor's **Page Formatting** group. It accepts an ordered set of images and returns one PDF suitable for duplex printing: each image occupies an odd-numbered page, and the following even-numbered page is blank.

## User-visible behavior

- The user selects one or more supported image files. Their selected order is preserved.
- The tool creates one A4 page for each image page produced by the existing image converter. The page orientation follows the image. The image is centered and scaled to fit while preserving its aspect ratio; it is not cropped or distorted.
- A white, empty page follows every image page. Each blank page has the same dimensions and orientation as its preceding image page.
- A multi-frame image such as TIFF follows the existing converter's behavior: each generated image page is followed by its own blank page.
- The result is one PDF. No page-size, fit, or color settings are added to the tool UI.

For two input images, the page sequence is:

| PDF page | Contents |
|---|---|
| 1 | First image |
| 2 | Blank |
| 3 | Second image |
| 4 | Blank |

## Architecture and data flow

1. Add `coloringBook` to `CORE_REGULAR_TOOL_IDS` in `frontend/editor/src/core/types/toolId.ts`, then register the tool under `SubcategoryId.PAGE_FORMATTING` in the core editor registry.
2. Use the existing multi-file tool flow to collect the selected image files and submit them together, in order, to `POST /api/v1/convert/img/pdf`.
3. The tool sends the existing image conversion parameters `fitOption=maintainAspectRatio`, `autoRotate=true`, and `colorType=color`, plus `interleaveBlankPages=true`.
4. Extend `ConvertToPdfRequest` with an optional `interleaveBlankPages` boolean. When enabled, `ConvertImgPDFController` passes the setting to the image-to-PDF processing path. After each generated image page, that path adds an empty white page using the image page's dimensions.
5. Return the existing endpoint's single-PDF response through the standard tool operation flow.

The flag is opt-in and defaults to false. Existing callers, including the general Convert tool, therefore retain their current output unless they explicitly send it.

## Errors and input constraints

- The editor requires at least one selected image before enabling execution.
- Image decoding or PDF-generation errors use the existing endpoint error response and standard tool error handling. A failed single request does not expose a partial PDF.
- Supported image formats remain those accepted by the existing image-to-PDF endpoint.

## Tests and documentation

- Backend tests cover the request flag's default and enabled behavior, preserving the existing result when the flag is omitted.
- PDF output tests verify that each generated image page is followed by an empty page, the total page count is twice the generated image-page count, input order is retained, and each blank page matches its preceding page's dimensions. Include mixed portrait/landscape inputs and multi-frame input where supported.
- Frontend tests cover request fields and input ordering, the tool's recognized ID and Page Formatting registration, and image-file support.
- Regenerate API models for both the frontend and engine from the Java OpenAPI spec using `task tool-models`. The new field must appear as `interleaveBlankPages` in the frontend request type and `interleave_blank_pages` in the generated engine request model.
- Add the tool's user-facing English strings to `frontend/editor/public/locales/en-US/translation.toml`.
- Document `interleaveBlankPages` in the image-to-PDF API description.

Run `task backend:check`, `task frontend:check`, and `task engine:check` for the changed areas. Confirm generated models with `task tool-models:check`. After modifying the translation file, run `task pre-commit:fix` as required by the repository's translation workflow.

## Out of scope

- A separate image-to-PDF endpoint or browser-side PDF generation.
- User-selectable paper sizes, fit modes, colors, or blank-page behavior.
- Changes to the general Convert tool's default behavior.
