# Coloring Book Tool Design

## Goal

Add a dedicated **Coloring book** tool under **Page Formatting**. It accepts one or more images in their selected order and returns a PDF with each image on an odd-numbered page and a blank page immediately after it. The output has exactly two pages for each image page, including a blank final page for duplex printing.

Each image is placed on an A4 page with its aspect ratio preserved. Page orientation follows the image orientation, so landscape images use landscape A4 pages. Images are centered and scaled to fit the page without distortion.

## User workflow

Users select image files through the existing FileContext file workflow and open **Coloring book** from the **Page Formatting** category. The tool submits the selected files in their current order. It requires at least one supported image and returns the resulting PDF through the standard processing and download flow. The tool has no additional controls.

If a selected input is not a supported image, or image decoding fails, the operation returns an error through the standard tool error display. A multi-frame image such as TIFF produces one image page per frame, with a blank page after every frame.

## Architecture

The frontend gets a dedicated registry entry and focused tool component for **Coloring book**. It uses the established file selection, operation state, error display, preview, and download behavior. The tool entry is grouped under `SubcategoryId.PAGE_FORMATTING` and is associated with its dedicated backend endpoint.

The backend adds a multipart endpoint in the existing image conversion controller area. It accepts one or more images and returns a PDF. PDF generation reuses the existing image decoding, EXIF handling, color conversion, and aspect-preserving A4 placement behavior. After every image page, including pages created from multi-frame images, generation adds a blank page with matching dimensions.

For every image page, the endpoint must invoke placement with `fitOption=maintainAspectRatio` and `autoRotate=true` (or use a dedicated helper that guarantees those same results). The general Image to PDF endpoint defaults to fill-page placement and auto-rotation off, so those defaults do not satisfy this tool's contract.

The new endpoint remains separate from the general Image to PDF endpoint, so the coloring-book behavior has a distinct API contract and can be enabled or disabled independently.

## Processing contract

- Inputs are one or more supported image files, in submission order.
- Each input image page is placed on an A4 page, preserving aspect ratio and centering the image.
- Landscape images use landscape A4 pages; portrait images use portrait A4 pages.
- Placement uses aspect-preserving fit and automatic orientation regardless of the general Image to PDF endpoint defaults.
- Every image page is followed by a blank page of the same dimensions.
- Output page count is twice the number of generated image pages. Multi-frame images count once per frame.
- Invalid, empty, or undecodable inputs produce an operation error rather than a partial PDF.

## Error handling

The endpoint validates that at least one image was submitted and relies on the existing image decoding path to reject unsupported or malformed data. Failures are returned through the established API error mechanism. The frontend displays them through its standard tool operation error state; it does not generate substitute output.

## Verification

Backend coverage will verify image order, the image/blank alternation, final blank-page presence, total page count, matching page dimensions, and aspect-preserving placement. It will include a multi-frame image case and invalid input handling. Frontend coverage will verify registration in Page Formatting, image selection submission to the dedicated endpoint, and normal output/error handling.

## Scope

This change adds only the dedicated coloring-book workflow. It does not change behavior or defaults in the general Image to PDF converter, expose page-size or fit controls, or add PDF inputs to the new tool.
