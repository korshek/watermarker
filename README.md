# Main Watermark Settings

Watermark parameters can be adjusted for optimal visual effects. The key settings are:

- **`watermark_text`**: The watermark text. Default: `"Confidential-"`.
- **`amplitude`**: Wave amplitude (vertical displacement of the text).
- **`frequency`**: Wave frequency (higher frequency results in more waves).
- **`letter_spacing`**: The space between characters in the wave.
- **`opacity`**: Transparency of the watermark (values from `0` to `255`).
- **`font_size`**: Font size of the watermark text.
- **`angle`**: The rotation angle of the watermark text.
- **`density`**: The "step" between repetitions of the watermark on the page or image.

These parameters can be adjusted depending on the desired effect and the target file format.

---

## Function Descriptions

### 1. `snake_text_on_canvas`
Draws text in a wavy pattern on a canvas (for PDF). The vertical displacement (`dy`) for each character is calculated using the sine function.

### 2. `draw_snake_text_at`
Draws a "snake" of text with rotation and positioning on the canvas. This allows not only to create a wave but also to rotate it, adding an extra visual effect.

### 3. `create_watermark_pdf`
Generates a PDF with repeated waves of text. This PDF is then applied on top of the original document using `PyMuPDF`. The entire process is handled in memory via `BytesIO`.

### 4. `add_watermark_to_pdf`
Adds the watermark to all pages of the PDF. For each page, a separate PDF with the watermark is created and then applied on top of the original page.

### 5. `snake_text_on_image`
Draws a "snake" of text on an image. Unlike PDF, this process works directly on the image using the `Pillow` library.

### 6. `add_watermark_to_image`
Adds the wavy watermark to an image. A transparent layer is created first, on which the text wave is drawn, and then this layer is overlaid on the original image.

### 7. `add_watermark`
A wrapper function that determines the input file format (PDF or image) and calls the corresponding function to add the watermark. This allows the script to work with both file types, automatically selecting the appropriate method.

---

## Example Usage

To add a watermark to a file, use the following example. Specify the path to the input file and the desired output file path.

### For PDF:
```python
input_file = "/path/to/input.pdf"
output_file = "/path/to/output.pdf"
add_watermark(input_file, output_file)
