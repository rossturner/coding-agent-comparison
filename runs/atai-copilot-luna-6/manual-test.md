# Manual test

Tested by hand on 2026-10-02.

| Check | Result |
|---|---|
| Sidebar file chooser accepts images | ✗ It only offers `.pdf` files, so images can't be chosen from the sidebar. |
| Images selected in the main file view | ✓ Images can be selected in the main Stirling PDF view, and the tool can then run on them. |
| Tool produces a result | ✓ The download button became available. |
| Download filename and extension | ✗ Saved as `coloring_book_{first image filename}.jpg`, although the file is a PDF. |
| Output PDF is valid | ✓ Opens once renamed to `.pdf`. |

## Defects

1. The sidebar file chooser only accepts `.pdf`, so images can't be picked
   from there.
2. The downloaded file gets the first image's `.jpg` extension instead of `.pdf`.
