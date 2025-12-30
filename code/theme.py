from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


class CustomTheme(Base):
    def __init__(self):
        super().__init__(
            font=(fonts.GoogleFont("Inter"), "sans-serif"),
            font_mono=(fonts.GoogleFont("Roboto Mono"), "monospace"),
            text_size=sizes.text_md,
        )

        self.set( 
            body_background_fill="transparent",
            body_text_color="#1F232A",
            background_fill_primary="transparent",
            block_background_fill="transparent",
            block_border_width="0px",
            block_label_background_fill="transparent",
            layout_gap="0px",

            # Input-Bereich
            input_background_fill="#2E5D87",
            input_border_color="transparent",
        )