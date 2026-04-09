def build_v5_stylesheet() -> str:
    return """
QWidget#V5MainWindow {
    background-color: #1a1d23;
}

QWidget#v5Navigation {
    background-color: #14181d;
    border-right: 1px solid #2a2f36;
}

QWidget#v5StackedWidget {
    background: transparent;
}

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

QFrame#V5SystemCard {
    border-radius: 12px;
    border: 1px solid #303640;
    background-color: #252b34;
}

QLabel#V5SectionTitle {
    color: #f3f6fb;
    font-size: 26px;
    font-weight: 650;
}

QLabel#V5InfoKey {
    color: #b8c0cc;
    font-size: 15px;
}

QLabel#V5InfoValue {
    color: #f2f5fb;
    font-size: 18px;
    font-weight: 600;
}

QFrame#V5ActionCard {
    border-radius: 12px;
    border: 1px solid #2f3640;
    background-color: #262c35;
}

QFrame#V5ActionCard:hover {
    border: 1px solid #5a7ecc;
    background-color: #2d3542;
}

QLabel#V5ActionTitle {
    color: #f1f4fa;
    font-size: 21px;
    font-weight: 600;
}

QLabel#V5ActionDesc {
    color: #b4becd;
    font-size: 14px;
}

QLabel#V5ActionArrow {
    color: #d5dcec;
    font-size: 30px;
    font-weight: 600;
}
"""
