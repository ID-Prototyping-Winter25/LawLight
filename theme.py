from gradio.themes.base import Base


class CustomTheme(Base):
    def __init__(self):
        super().__init__()

        super().set(
            body_background_fill="#ECF7FF",
            body_background_fill_dark="black",
            input_background_fill="#EDF72A",
            input_background_fill_dark="#340ba5"
        )