import streamlit as st


def apply_page_styles():
    """페이지 스타일 적용"""
    st.set_page_config(
        page_title="Option Calculator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 스타일 추가 (스피너 버튼 제거 CSS 포함)
    st.markdown(
        """
    <style>
        .stMarkdown {
            padding: 10px 0px;
        }
        div.block-container {
            padding-top: 2rem;
        }
        .highlight {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 4px;
        }
        .profit {
            color: #1cd4c8;
        }
        .loss {
            color: #d41c78;
        }
        .main-text {
            font-size: 18px;
        }
        .header-text {
            font-size: 24px;
            font-weight: bold;
        }
        .center-text {
            text-align: center;
        }
        .sidebar-header {
            font-size: 20px;
            font-weight: bold;
        }
        .small-font {
            font-size: 14px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def apply_parameter_styles():
    """파라미터 스타일 적용"""
    st.markdown(
        """
    <style>
    /* 전체 폰트 굵게 설정 */
    .streamlit-container {
        font-weight: bold;
    }
    .positive { color: #1cd4c8; font-weight: bold; }
    .negative { color: #d41c78; font-weight: bold; }

    /* 파라미터 레이블 스타일 */
    .param-label {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* 옵션 레이블 스타일 */
    .option-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
        margin: 2px 0 3px 0 !important;
        padding-bottom: 0px !important;
        white-space: nowrap;
    }
    .leg-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        padding: 2px 6px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
        line-height: 1.4;
    }
    .leg-badge.positive {
        color: #087a72;
        background: rgba(28, 212, 200, 0.14);
        border: 1px solid rgba(28, 212, 200, 0.36);
    }
    .leg-badge.negative {
        color: #9a1558;
        background: rgba(212, 28, 120, 0.12);
        border: 1px solid rgba(212, 28, 120, 0.30);
    }
    .leg-name {
        color: #1f2937;
        font-size: 13px;
    }
    .leg-strike {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
