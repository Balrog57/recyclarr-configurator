class CinemaTheme:
    """Design System pour une ambiance Home Cinéma Premium."""
    PRIMARY = "#FF4D00"        # Orange Cinéma vibrant
    PRIMARY_DARK = "#CC3E00"   
    SECONDARY = "#00B4D8"      # Bleu accent
    ACCENT = "#FFB703"         # Ambre/Or
    BACKGROUND = "#050505"     # Noir profond
    SURFACE = "#111111"        # Gris très foncé
    SURFACE_LIGHT = "#1A1A1A"  # Gris foncé
    BORDER = "#2A2A2A"         # Bordure subtile
    
    TEXT_PRIMARY = "#FFFFFF"   
    TEXT_SECONDARY = "#888888" 
    TEXT_DISABLED = "#444444"
    
    SUCCESS = "#2D6A4F"
    ERROR = "#9B2226"
    
    RADARR_COLOR = "#FFC300"
    SONARR_COLOR = "#00A8E8"
    WARNING = "#E9C46A"
    INFO = "#2196f3"
    BORDER_FOCUS = "#FF4D00"


# Stylesheet global
GLOBAL_STYLESHEET = f"""
QMainWindow {{
    background-color: {CinemaTheme.BACKGROUND};
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {CinemaTheme.BACKGROUND};
    color: {CinemaTheme.TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 13px;
}}

QGroupBox {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {CinemaTheme.PRIMARY};
}}

QPushButton {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 700;
    font-size: 13px;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {CinemaTheme.PRIMARY_DARK};
}}

QPushButton:pressed {{
    background-color: {CinemaTheme.PRIMARY};
}}

QPushButton:disabled {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_DISABLED};
}}

QListWidget, QTreeWidget {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 8px;
    padding: 8px;
    outline: none;
}}

QListWidget::item, QTreeWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 0;
}}

QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
}}

QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {CinemaTheme.PRIMARY};
}}

QLabel {{
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QLabel[class="h2"] {{
    font-size: 24px;
    font-weight: bold;
    color: {CinemaTheme.PRIMARY};
    margin-bottom: 8px;
}}

QLabel[class="h3"] {{
    font-size: 18px;
    font-weight: bold;
    color: {CinemaTheme.SECONDARY};
}}

QTabWidget::pane {{
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    background-color: {CinemaTheme.SURFACE};
}}

QTabBar::tab {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_SECONDARY};
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}
"""
