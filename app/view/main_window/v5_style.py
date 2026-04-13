def build_v5_stylesheet() -> str:
    return """
QWidget#DashboardInterface,
QWidget#V5DashboardContent {
    background: transparent;
}

QScrollArea#V5DashboardScroll {
    border: none;
    background: transparent;
}

QFrame#V5HeroCard {
    border-radius: 16px;
    border: 1px solid #2f3d56;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #293e66,
        stop: 0.5 #5965a5,
        stop: 1 #2a2f5f
    );
}

QLabel#V5HeroTitle {
    color: #f2f6ff;
    font-size: 44px;
    font-weight: 700;
}

QLabel#V5HeroSubtitle {
    color: rgba(242, 246, 255, 0.9);
    font-size: 22px;
    font-weight: 500;
}

QLabel#V5HeroVersion {
    color: rgba(242, 246, 255, 0.85);
    font-size: 14px;
    font-weight: 600;
}

QLabel#V5SectionTitle {
    font-size: 26px;
    font-weight: 650;
}

QLabel#V5InfoKey {
    font-size: 15px;
}

QLabel#V5InfoValue {
    font-size: 18px;
    font-weight: 600;
}

QLabel#V5ActionTitle {
    font-size: 21px;
    font-weight: 600;
}

QLabel#V5ActionDesc {
    font-size: 14px;
}

QLabel#V5ActionArrow {
    font-size: 30px;
    font-weight: 600;
}
"""
