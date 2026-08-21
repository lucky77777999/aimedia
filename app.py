import html
import random
import string
from urllib.parse import quote

import requests
import streamlit as st
from openai import OpenAI


# =========================
# 页面配置
# =========================
st.set_page_config(
    page_title="AI 全媒体创作平台",
    page_icon="🚀",
    layout="wide"
)


# =========================
# Secrets 配置
# 请在 Streamlit Cloud -> Settings -> Secrets 中填写
# =========================
try:
    DEEPSEEK_API_KEY = ["DEEPSEEK_API_KEY"]
    JSONBIN_BIN_ID = ["6a80551ada38895dfee82522"]
    JSONBIN_MASTER_KEY = ["$2a$10$HOZJwC6Hm8pTMwDgKyG1T.BZk7tu7IrHW/W91BLEcGuClfn.BlEH."]
    XIANYU_LINK = ["XIANYU_LINK"]
    ADMIN_PASSWORD = ["ADMIN_PASSWORD"]
except Exception:
    st.error("缺少 Secrets 配置，请到 Streamlit Cloud 的 Settings → Secrets 填写。")
    st.stop()

ALIPAY_IMG = "pay.jpg"       # GitHub 中的图片文件名
SERVICE_PRICE = 2
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

ai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


# =========================
# 页面样式
# =========================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7f8fa;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }

    .header-banner {
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        padding: 26px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 22px;
    }

    .header-banner h1 {
        color: white;
        margin: 0;
        font-size: 32px;
    }

    .header-banner p {
        color: #eeeeee;
        margin: 8px 0 0;
    }

    .paywall-box {
        background: #fff0f6;
        border: 2px dashed #ff4d6d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-top: 18px;
    }

    .locked-box {
        background: #eeeeee;
        border-radius: 10px;
        padding: 35px 20px;
        text-align: center;
        color: #555555;
        margin-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# JSONBin 数据函数
# =========================
def default_data():
    return {
        "unused_passwords": [],
        "used_passwords": []
    }


def load_data():
    try:
        response = requests.get(
            JSONBIN_URL + "/latest",
            headers={"X-Master-Key": JSONBIN_MASTER_KEY},
            timeout=15
        )
        response.raise_for_status()

        record = response.json().get("record", {})

        if not isinstance(record, dict):
            record = default_data()

        record.setdefault("unused_passwords", [])
        record.setdefault("used_passwords", [])

        return record

    except Exception as exc:
        st.error(f"读取卡密数据失败：{exc}")
        return default_data()


def save_data(data):
    try:
        response = requests.put(
            JSONBIN_URL,
            json=data,
            headers={
                "X-Master-Key": JSONBIN_MASTER_KEY,
                "Content-Type": "application/json"
            },
            timeout=15
        )
        response.raise_for_status()
        return True

    except Exception as exc:
        st.error(f"保存卡密数据失败：{exc}")
        return False


def generate_codes(count=50):
    """生成不容易混淆的随机卡密。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codes = set()

    while len(codes) < count:
        code = "".join(random.choices(alphabet, k=8))
        codes.add(code)

    return list(codes)


# =========================
# AI 函数
# =========================
def call_deepseek(service, user_input):
    if "普通文字问答" in service:
        prompt = (
            "请准确、清晰地回答下面的问题，使用简洁的分点结构：\n"
            f"{user_input}"
        )

    elif "高级文字深度分析" in service:
        prompt = (
            "请对下面的内容进行结构化深度分析，包含背景、问题、原因、"
            "影响和建议：\n"
            f"{user_input}"
        )

    elif "短视频" in service:
        prompt = (
            "请为下面的主题制作一套短视频脚本，包含标题、开场钩子、"
            "分镜、台词、时长和结尾行动号召：\n"
            f"{user_input}"
        )

    else:
        prompt = user_input

    try:
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一名可靠的中文 AI 助手。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            stream=False
        )

        return response.choices[0].message.content

    except Exception as exc:
        return f"AI 调用失败：{exc}"


def generate_image(prompt):
    image_url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt)}?width=1024&height=1024&nologo=true"
    )

    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return image_url

    except Exception:
        return None


# =========================
# 侧边栏
# =========================
with st.sidebar:
    st.markdown("### 🚀 AI 创作平台")

    page = st.radio(
        "页面",
        ["创作大厅", "老板后台"]
    )

    if page == "老板后台":
        admin_input = st.text_input(
            "管理员密码",
            type="password"
        )

        if admin_input != ADMIN_PASSWORD:
            st.warning("请输入正确的管理员密码。")
            st.stop()


# =========================
# 创作大厅
# =========================
if page == "创作大厅":
    st.markdown(
        """
        <div class="header-banner">
            <h1>🚀 AI 全媒体创作平台</h1>
            <p>文字问答 · 深度分析 · AI 绘画 · 短视频脚本</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(f"所有服务统一收费：{SERVICE_PRICE} 元/次")

    service = st.radio(
        "选择服务类型",
        [
            "普通文字问答",
            "高级文字深度分析",
            "AI绘画·高清出图",
            "AI生成短视频脚本"
        ]
    )

    if service == "普通文字问答":
        placeholder = "例如：帮我写一封请假条"
    elif service == "高级文字深度分析":
        placeholder = "例如：分析新能源汽车市场趋势"
    elif service == "AI绘画·高清出图":
        placeholder = "例如：赛博朋克城市中的猫，高清插画"
    else:
        placeholder = "例如：年轻人不想结婚的短视频主题"

    user_input = st.text_area(
        "输入您的需求",
        height=130,
        placeholder=placeholder
    )

    if st.button("🚀 开始生成", use_container_width=True):
        if not user_input.strip():
            st.warning("请先输入需求。")
        else:
            with st.spinner("正在生成，请稍候……"):
                if "AI绘画" in service:
                    image_url = generate_image(user_input)

                    if image_url:
                        st.session_state["ai_result"] = {
                            "type": "image",
                            "value": image_url
                        }
                    else:
                        st.error("图片生成失败，请稍后重试。")

                else:
                    result = call_deepseek(service, user_input)
                    st.session_state["ai_result"] = {
                        "type": "text",
                        "value": result
                    }

    # 生成结果
    if "ai_result" in st.session_state:
        result = st.session_state["ai_result"]

        st.markdown("---")
        st.subheader("🎉 结果已生成")

        unlock_pwd = st.text_input(
            "输入解锁密码",
            type="password",
            placeholder="购买后输入一次性密码"
        )

        data = load_data()
        unused = data.get("unused_passwords", [])
        used = data.get("used_passwords", [])

        unlocked = False

        if unlock_pwd:
            if unlock_pwd in used:
                st.error("该密码已经使用过，请重新购买。")

            elif unlock_pwd in unused:
                # 注意：JSONBin 不保证并发原子操作。
                # 小规模测试可用，正式业务建议改用数据库事务。
                unused.remove(unlock_pwd)
                used.append(unlock_pwd)

                data["unused_passwords"] = unused
                data["used_passwords"] = used

                if save_data(data):
                    unlocked = True
                    st.success("密码验证成功，本次密码已作废。")
                else:
                    st.error("密码状态保存失败，本次暂不解锁。")

            else:
                st.error("密码错误，请购买后重新输入。")

        if unlocked:
            if result["type"] == "image":
                st.image(
                    result["value"],
                    caption="AI 生成图片",
                    use_container_width=True
                )
                st.markdown(f"[下载原图]({result['value']})")

            else:
                st.markdown(result["value"])
                st.text_area(
                    "复制区",
                    value=result["value"],
                    height=260
                )

        else:
            st.markdown(
                """
                <div class="locked-box">
                    🔒 内容已锁定<br>
                    <small>购买 2 元服务后，输入一次性密码查看完整结果。</small>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="paywall-box">
                    <h3>本次服务：{SERVICE_PRICE} 元</h3>
                    <p>点击下方按钮前往闲鱼购买。</p>
                    <p>付款后，请按商品说明获取解锁密码。</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if XIANYU_LINK.startswith("http"):
                st.link_button(
                    "👉 前往闲鱼购买 2 元服务",
                    XIANYU_LINK,
                    use_container_width=True
                )
            else:
                st.error("闲鱼链接配置错误，请检查 XIANYU_LINK。")

            st.markdown("#### 其他付款方式")

            try:
                st.image(
                    ALIPAY_IMG,
                    caption="支付宝收款码",
                    width=250
                )
                st.caption("支付宝付款后请按照页面说明联系人工核验。")
            except Exception:
                st.warning("未找到支付宝图片，请检查文件名和路径。")


# =========================
# 老板后台
# =========================
elif page == "老板后台":
    st.title("🔧 卡密管理后台")

    st.warning(
        "当前代码只负责验证卡密，不会自动核验闲鱼或支付宝付款。"
    )

    data = load_data()
    unused = data.get("unused_passwords", [])
    used = data.get("used_passwords", [])

    st.info(
        f"未使用：{len(unused)} 个；"
        f"已使用：{len(used)} 个"
    )

    count = st.number_input(
        "生成数量",
        min_value=1,
        max_value=500,
        value=50,
        step=1
    )

    if st.button("🎲 生成随机卡密"):
        new_codes = generate_codes(int(count))
        data["unused_passwords"] = unused + new_codes

        if save_data(data):
            st.success("生成成功，请复制并通过合规方式发放。")
            st.code("\n".join(new_codes))

    st.markdown("---")

    if unused:
        st.subheader("未使用卡密")
        st.code("\n".join(unused))

    if used:
        with st.expander("已使用卡密"):
            st.code("\n".join(used))
