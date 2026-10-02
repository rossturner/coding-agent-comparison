# Manual test checklist

Test each run's branch by hand in the running app (log in as admin/password),
and record the results in `runs/<run-id>/manual-test.md`.

1. The tool appears under Page Formatting as "Coloring book".
2. The file chooser in the tool's sidebar accepts image files. Note whether it
   opens Stirling PDF's own file chooser dialog or the operating system's
   file picker.
3. Images selected in the main file view can be used by the tool.
4. The tool runs on several images and produces a result.
5. The download has a `.pdf` extension and a sensible name.
6. The PDF opens. Images are on the odd pages, in the order selected, and every
   even page is blank.
7. Anything else that's broken or odd.
