"""



RoboVision Agent -- Unified Industrial Vision Alert Console.



Complete UI redesign: industrial console dark theme, 4 tabs with consistent layout.



"""







import atexit
import logging
logger = logging.getLogger(__name__)



import json



import os



import socket



import sys



import threading



import traceback



from pathlib import Path







import gradio as gr







from app.agent import run_agent, _is_chain_query



from app.core.media_router import detect_media






from ui.disposal_tab import build_disposal_tab



import core.mock as disposal_mock



disposal_mock.USE_MOCK = True







# ---------------------------------------------------------------------------



# environment



# ---------------------------------------------------------------------------



os.environ.setdefault("GRADIO_SERVER_NAME", "127.0.0.1")



os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"














# ---------------------------------------------------------------------------



# UI text dictionary



# ---------------------------------------------------------------------------



UI_TEXTS = {
    "zh": {
        "title": "RoboVision Agent",
        "subtitle": "工业视觉预警控制台 | YOLO + RAG + Qwen3-VL",
        "tab_detect": "视觉检测",
        "tab_rag": "RAG 知识问答",
        "tab_logs": "日志与报告",
        "tab_disposal": "事件处置",
        "detect_desc": "上传图片/视频或输入摄像头地址，选择任务，开始检测。",
        "file_label": "上传文件（图片 / 视频）",
        "source_label": "视频源 / 摄像头 / RTSP",
        "source_placeholder": "例如：0（摄像头）| D:/video.mp4 | rtsp://...",
        "task_label": "检测任务",
        "task_choices": ["自动判断", "通用物品检测", "火灾烟雾预警", "安全帽反光衣工检"],
        "text_label": "文本指令",
        "text_placeholder": "例如：检测图中所有目标 | 检查火灾风险 | 检测人员并查询安全规范",
        "advanced_label": "高级参数",
        "conf_label": "置信阈值",
        "stride_label": "帧间隔",
        "max_frames_label": "最大帧数",
        "run_btn": "▶ 开始检测",
        "waiting_text": "*等待输入...*",
        "summary_heading": "📊 检测摘要",
        "annotated_label": "🖼 标注结果（图像）",
        "video_label": "🎞 标注视频",
        "alarm_heading": "🚨 报警 / Alarms",
        "json_label": "📋 检测 JSON",
        "log_path_label": "📝 日志路径",
        "rag_desc": "向知识库提问，查询安全规范、处置流程、部署指南等。",
        "rag_question_label": "你的问题",
        "rag_question_placeholder": "例如：检测到烟雾后怎么处理？| 安全帽佩戴规范？| 如何部署到 Jetson？",
        "rag_topk_label": "检索片段数",
        "rag_llm_label": "使用 Qwen3-VL LLM",
        "rag_btn": "🤖 查询 Agent",
        "rag_answer_title": "💬 回答",
        "rag_answer_default": "*你的回答将在此显示...*",
        "rag_details_heading": "📋 详情 / Details",
        "rag_model_label": "模型信息",
        "rag_sources_label": "检索来源",
        "rag_chunks_label": "检索片段",
        "rag_sources_default": "*来源将在此显示...*",
        "rag_chunks_default": "*检索片段将在此显示...*",
        "rag_examples_label": "💡 示例问题",
        "rag_examples_text": "**🔥 火灾安全：** 检测到烟雾后怎么处理？| HIGH/MEDIUM/LOW 报警等级说明 | 火灾报警确认规则\n\n**🪖 PPE 规范：** 安全帽佩戴规范是什么？| 如何分级 PPE 违规？| 危险区域附近人员风险说明\n\n**🚀 部署：** 如何部署到 Jetson？| ONNX 导出注意事项 | 推荐硬件\n\n**📋 项目：** RoboVision Agent 能做什么？| 如何使用巡检报告？| 有哪些可用模型？",
        "logs_desc": "查询日志、报告、报警历史，或通过 Agent 自动生成报告。",
        "log_query_label": "日志查询",
        "log_query_placeholder": "例如：最近报警 | 巡检报告 | 火灾日志",
        "log_query_btn": "🤖 查询",
        "log_result_heading": "📊 结果 / Results",
        "log_result_default": "*等待查询...*",
        "log_alarm_heading": "🚨 报警截图",
        "log_report_label": "📝 报告路径",
        "log_stats_heading": "📱 统计概览",
        "footer": "RoboVision Agent v1.0 · YOLO + RAG + Qwen3-VL · Industrial Vision Alert Console",
        "switch_btn": "English / EN",
    },
    "en": {
        "title": "RoboVision Agent",
        "subtitle": "Industrial Vision Alert Console | YOLO + RAG + Qwen3-VL",
        "tab_detect": "Vision Detection",
        "tab_rag": "RAG Knowledge Q&A",
        "tab_logs": "Logs & Reports",
        "tab_disposal": "Event Disposal",
        "detect_desc": "Upload images/videos or enter a camera source, select a task, and start detection.",
        "file_label": "Upload File (Image / Video)",
        "source_label": "Video Source / Camera / RTSP",
        "source_placeholder": "e.g.: 0 (camera) | D:/video.mp4 | rtsp://...",
        "task_label": "Detection Task",
        "task_choices": ["Auto Detect", "General Object Detection", "Fire & Smoke Warning", "PPE Safety Helmet & Reflective Vest Check"],
        "text_label": "Text Instruction",
        "text_placeholder": "e.g.: Detect all targets in image | Check fire risk | Detect personnel and query safety regulations",
        "advanced_label": "Advanced Parameters",
        "conf_label": "Confidence Threshold",
        "stride_label": "Frame Stride",
        "max_frames_label": "Max Frames",
        "run_btn": "▶ Start Detection",
        "waiting_text": "*Waiting for input...*",
        "summary_heading": "📊 Detection Summary",
        "annotated_label": "🖼 Annotated Result",
        "video_label": "🎞 Annotated Video",
        "alarm_heading": "🚨 Alarms",
        "json_label": "📋 Detection JSON",
        "log_path_label": "📝 Log Path",
        "rag_desc": "Ask the knowledge base about safety regulations, disposal procedures, deployment guides, etc.",
        "rag_question_label": "Your Question",
        "rag_question_placeholder": "e.g.: How to handle detected smoke? | PPE wearing regulations? | How to deploy to Jetson?",
        "rag_topk_label": "Retrieval Top-K",
        "rag_llm_label": "Use Qwen3-VL LLM",
        "rag_btn": "🤖 Ask Agent",
        "rag_answer_title": "💬 Answer",
        "rag_answer_default": "*Your answer will appear here...*",
        "rag_details_heading": "📋 Details",
        "rag_model_label": "Model Info",
        "rag_sources_label": "Retrieval Sources",
        "rag_chunks_label": "Retrieved Chunks",
        "rag_sources_default": "*Sources will appear here...*",
        "rag_chunks_default": "*Retrieved chunks will appear here...*",
        "rag_examples_label": "💡 Example Questions",
        "rag_examples_text": "**🔥 Fire Safety:** How to handle detected smoke? | HIGH/MEDIUM/LOW alarm levels explained | Fire alarm confirmation rules\n\n**🪖 PPE Regulations:** What are the helmet wearing regulations? | How to grade PPE violations? | Personnel risk near hazardous areas\n\n**🚀 Deployment:** How to deploy to Jetson? | ONNX export notes | Recommended hardware\n\n**📋 Project:** What can RoboVision Agent do? | How to use inspection reports? | Available models?",
        "logs_desc": "Query logs, reports, alarm history, or auto-generate reports via Agent.",
        "log_query_label": "Log Query",
        "log_query_placeholder": "e.g.: Recent alarms | Inspection report | Fire log",
        "log_query_btn": "🤖 Query",
        "log_result_heading": "📊 Results",
        "log_result_default": "*Waiting for query...*",
        "log_alarm_heading": "🚨 Alarm Screenshots",
        "log_report_label": "📝 Report Path",
        "log_stats_heading": "📱 Statistics",
        "footer": "RoboVision Agent v1.0 · YOLO + RAG + Qwen3-VL · Industrial Vision Alert Console",
        "switch_btn": "中文 / ZH",
    },
}







# ===========================================================================



# CUSTOM CSS — Industrial Console Dark Theme



# ===========================================================================



custom_css = """



/* ======================================================



   RoboVision Industrial Console -- Design System v2



   ====================================================== */







/* --- Font Import --- */



@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');















/* --- Design Tokens --- */



:root {



    --brand-50:  #eff6ff; --brand-100: #dbeafe; --brand-200: #bfdbfe;



    --brand-300: #93c5fd; --brand-400: #60a5fa; --brand-500: #3b82f6;



    --brand-600: #2563eb; --brand-700: #1d4ed8; --brand-800: #1e40af;



    --brand-900: #1e3a8a; --brand-950: #172554;



    --accent:          #3b82f6;



    --accent-hover:    #2563eb;



    --accent-glow:     rgba(59,130,246,.38);



    --danger:          #ef4444;



    --danger-soft:     rgba(239,68,68,.18);



    --warning:         #f59e0b;



    --warning-soft:    rgba(245,158,11,.18);



    --success:         #22c55e;



    --success-soft:    rgba(34,197,94,.18);



    --surface-root:      #0b1120;



    --surface-elevated:  #111827;



    --surface-card:      #1a2332;



    --surface-card-alt:  #15202e;



    --surface-input:     #101a27;



    --surface-code:      #0a101c;



    --text-heading:      #f1f5f9;



    --text-body:         #cbd5e1;



    --text-secondary:    #94a3b8;



    --text-muted:        #64748b;



    --border-subtle:     #1e293b;



    --border-default:    #334155;



    --border-strong:     #475569;



    --border-accent:     #3b82f6;



    --radius-xs: 4px; --radius-sm: 8px; --radius-md: 12px;



    --radius-lg: 16px; --radius-xl: 20px;



    --shadow-sm:  0 1px 3px rgba(0,0,0,.5);



    --shadow-md:  0 4px 14px rgba(0,0,0,.55);



    --shadow-lg:  0 12px 40px rgba(0,0,0,.65);



    --shadow-glow: 0 0 28px var(--accent-glow);



    --ease-out:    cubic-bezier(.16,1,.3,1);



    --ease-in-out: cubic-bezier(.65,0,.35,1);



    --duration-fast:   150ms;



    --duration-normal: 250ms;



    --duration-slow:   400ms;



}







/* --- Page --- */



body {



    background: var(--surface-root) !important;



}



body::before {



    content: "";



    position: fixed; inset: 0; z-index: 0; pointer-events: none;



    background:



        radial-gradient(ellipse 60% 50% at 50% 0%, rgba(59,130,246,.03) 0%, transparent 70%),



        radial-gradient(ellipse 40% 40% at 100% 100%, rgba(30,64,175,.04) 0%, transparent 70%);



}



.gradio-container {



    max-width: 78vw !important; min-width: 960px !important; margin: 0 auto !important;



    padding: 0 !important;



    font-family: "Inter", "Noto Sans SC", "Microsoft YaHei", "微软雅黑", "SimSun", system-ui, -apple-system, sans-serif !important;



    background: var(--surface-root) !important; color: var(--text-body) !important;



}



.gradio-container .contain, .gradio-container .main {



    max-width: 100% !important; padding: 0 !important;



    background: var(--surface-root) !important; color: var(--text-body) !important;



}



.gradio-container > div, .gradio-container > div > div,



.gradio-container .gap, .gradio-container .panel {



    background: transparent !important; border: none !important;



}



.gradio-container .block, .gradio-container .form {



    background: var(--surface-root) !important; color: var(--text-body) !important;



}







/* --- Header --- */



.header-banner {



    position: relative;



    background:



        radial-gradient(ellipse 80% 140% at 20% -30%, rgba(59,130,246,.22) 0%, transparent 55%),



        radial-gradient(ellipse 60% 100% at 85% 120%, rgba(30,64,175,.28) 0%, transparent 55%),



        linear-gradient(135deg, #0f1d3a 0%, #13294b 30%, #1a3a6b 65%, #1d4ed8 100%) !important;



    color: #fff !important;



    padding: 32px 44px 24px !important;



    border-radius: 0 !important;



    margin-bottom: 0 !important;



    overflow: hidden;



    border-bottom: 1px solid rgba(255,255,255,.08) !important;



}



.header-banner::before {



    content: "";



    position: absolute; inset: 0;



    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,.012) 2px, rgba(255,255,255,.012) 4px);



    pointer-events: none;



}



.header-banner h1 {



    font-size: 1.9rem !important; font-weight: 800 !important;



    color: #fff !important; margin: 0 0 2px !important;



    letter-spacing: -.01em; position: relative; z-index: 1;



    text-shadow: 0 2px 12px rgba(0,0,0,.35);



}



.header-banner .subtitle {



    color: rgba(255,255,255,.7) !important; font-size: 0.94rem !important;



    margin: 0 !important; position: relative; z-index: 1;



    font-weight: 400; letter-spacing: .01em;



}







/* --- YOLO Badge --- */



.yolo-status-line { text-align: center !important; padding: 6px 0 !important; margin: 0 !important; }



.yolo-status-line p { margin: 0 !important; padding: 0 !important; }



.yolo-badge {



    display: inline-block; padding: 4px 14px; border-radius: 20px;



    font-size: 0.8rem; font-weight: 600; letter-spacing: .02em;



}



.yolo-badge.loading { background: var(--warning-soft); color: #fde68a; border: 1px solid rgba(245,158,11,.25); }



.yolo-badge.ready   { background: var(--success-soft); color: #bbf7d0; border: 1px solid rgba(34,197,94,.25); }







/* --- Tabs --- */



.tabs {



    background: var(--surface-elevated) !important;



    border-radius: 0 !important;



    box-shadow: var(--shadow-sm) !important;



    margin-bottom: 0 !important;



    border-bottom: 1px solid var(--border-subtle) !important;



}



.tab-nav { background: transparent !important; gap: 0 !important; }



.tab-nav button, .tab-nav .tab-nav-item {



    color: var(--text-secondary) !important;



    font-size: 0.88rem !important; font-weight: 500 !important;



    padding: 14px 24px !important; border-radius: 0 !important;



    border: none !important; border-bottom: 2px solid transparent !important;



    background: transparent !important;



    transition: color var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out) !important;



}



.tab-nav button:hover, .tab-nav .tab-nav-item:hover { color: var(--text-heading) !important; }



.tab-nav button.selected, .tab-nav .tab-nav-item.selected {



    color: var(--accent) !important; border-bottom-color: var(--accent) !important; background: transparent !important;



}



.tabs > .tabitem { width: 100% !important; min-width: 100% !important; padding: 20px 28px !important; }



.tabitem > .gap { width: 100% !important; }



.tabitem .gr-row { width: 100% !important; }







/* --- Cards --- */



.section-card {



    background: var(--surface-card) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-lg) !important;



    padding: 24px 28px !important;



    box-shadow: var(--shadow-sm) !important;



    margin-bottom: 18px !important;



    transition: box-shadow var(--duration-normal) var(--ease-out), border-color var(--duration-normal) var(--ease-out) !important;



}



.section-card:hover { box-shadow: var(--shadow-md) !important; border-color: var(--border-default) !important; }



.section-card-alt {



    background: var(--surface-card-alt) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-lg) !important;



    padding: 24px 28px !important;



    box-shadow: var(--shadow-sm) !important;



    margin-bottom: 18px !important;



    transition: box-shadow var(--duration-normal) var(--ease-out) !important;



}



.section-card-alt:hover { box-shadow: var(--shadow-md) !important; }







/* --- Headings --- */



.section-heading {



    font-size: 0.84rem !important; font-weight: 700 !important;



    color: var(--brand-400) !important;



    margin-bottom: 14px !important; padding-bottom: 8px !important;



    border-bottom: 2px solid var(--border-subtle) !important;



    text-transform: uppercase !important; letter-spacing: .06em !important;



}







/* --- Tab Desc --- */



.tab-desc {



    color: var(--text-secondary) !important; font-size: 0.86rem !important;



    margin-bottom: 18px !important; padding: 12px 20px !important;



    background: var(--surface-card-alt) !important;



    border-radius: var(--radius-sm) !important;



    border-left: 3px solid var(--accent) !important;



    line-height: 1.6 !important;



}







/* --- Buttons --- */



.primary-btn, button.primary {



    background: var(--accent) !important; color: #fff !important;



    border-radius: var(--radius-sm) !important; font-weight: 600 !important;



    font-size: 0.94rem !important; padding: 13px 36px !important;



    transition: all var(--duration-fast) var(--ease-out) !important;



    box-shadow: 0 2px 8px rgba(59,130,246,.35) !important;



    border: none !important; letter-spacing: .01em !important; cursor: pointer !important;



}



.primary-btn:hover, button.primary:hover {



    background: var(--accent-hover) !important;



    box-shadow: 0 4px 16px rgba(59,130,246,.5) !important;



    transform: translateY(-1px) !important;



}



.primary-btn:active, button.primary:active { transform: translateY(0) !important; }



button.secondary, .secondary-btn {



    background: var(--surface-card) !important;



    color: var(--text-body) !important;



    border: 1px solid var(--border-default) !important;



    border-radius: var(--radius-sm) !important;



    font-weight: 500 !important; font-size: 0.86rem !important;



    padding: 8px 18px !important;



    transition: all var(--duration-fast) var(--ease-out) !important;



}



button.secondary:hover, .secondary-btn:hover {



    background: var(--surface-card-alt) !important; border-color: var(--accent) !important; color: var(--accent) !important;



}







/* --- Result Summary --- */



.result-summary {



    background: linear-gradient(160deg, #14253d 0%, #0f1d30 100%) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-md) !important;



    padding: 22px 26px !important; font-size: 0.92rem !important;



    min-height: 180px !important; color: var(--text-body) !important;



    line-height: 1.75 !important;



    box-shadow: inset 0 1px 0 rgba(255,255,255,.02) !important;



}







/* --- RAG Answer --- */



.rag-answer {



    background: linear-gradient(160deg, #14253d 0%, #102038 100%) !important;



    border: 1px solid var(--accent) !important;



    border-radius: var(--radius-md) !important;



    padding: 26px 30px !important; font-size: 0.94rem !important;



    line-height: 1.85 !important; min-height: 260px !important;



    color: var(--text-body) !important;



    box-shadow: 0 0 30px rgba(59,130,246,.08) !important;



}







/* --- RAG Details --- */



.rag-details {



    background: var(--surface-card) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-sm) !important;



    padding: 14px 18px !important; font-size: 0.83rem !important;



    color: var(--text-secondary) !important;



    line-height: 1.55 !important; margin-bottom: 10px !important;



}







/* --- Gallery --- */



.alarm-gallery img, .alarm-gallery .thumbnail-item { border-radius: var(--radius-sm) !important; object-fit: cover !important; }



.gr-gallery { background: var(--surface-card) !important; border-radius: var(--radius-sm) !important; }







/* --- JSON --- */



.json-output {



    max-height: 300px !important; overflow-y: auto !important;



    font-size: 0.81rem !important;



    background: var(--surface-code) !important;



    color: #7dd3fc !important;



    border-radius: var(--radius-sm) !important;



    border: 1px solid var(--border-subtle) !important;



    padding: 16px 20px !important;



    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace !important;



    line-height: 1.6 !important;



}







/* --- Inputs --- */



input, textarea, select, .gr-input, .gr-textbox textarea, .gr-textbox input {



    border-radius: var(--radius-sm) !important;



    border: 1px solid var(--border-subtle) !important;



    background: var(--surface-input) !important;



    color: var(--text-body) !important;



    font-size: 0.9rem !important; font-family: inherit !important;



    transition: border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out) !important;



}



input:focus, textarea:focus, .gr-input:focus, .gr-textbox textarea:focus {



    border-color: var(--accent) !important;



    box-shadow: 0 0 0 3px rgba(59,130,246,.12) !important;



    outline: none !important;



}



.gr-textbox textarea { line-height: 1.7 !important; }



input::placeholder, textarea::placeholder { color: var(--text-muted) !important; opacity: .7 !important; }



.gr-dropdown { border-radius: var(--radius-sm) !important; background: var(--surface-input) !important; color: var(--text-body) !important; border: 1px solid var(--border-subtle) !important; }







/* --- Sliders --- */



.gr-slider input[type="range"] { accent-color: var(--accent) !important; }







/* --- Labels --- */



label, .gr-input-label, .gr-textbox > label, .gr-slider > label, .gr-checkbox > label, .gr-dropdown > label, .gr-file > label {



    color: var(--text-secondary) !important;



    font-size: 0.78rem !important; font-weight: 600 !important;



    text-transform: uppercase !important; letter-spacing: .05em !important;



    margin-bottom: 6px !important;



}







/* --- Layout --- */



.gradio-container .gr-row { gap: 20px !important; }



.gradio-container .gr-column { gap: 16px !important; }







/* --- Footer --- */



footer {



    text-align: center !important; color: var(--text-muted) !important;



    font-size: 0.73rem !important; padding: 14px 0 !important; margin-top: 20px !important;



    border-top: 1px solid var(--border-subtle) !important; letter-spacing: .02em !important;



}







/* --- Accordion --- */



.gr-accordion {



    background: var(--surface-card) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-md) !important;



    color: var(--text-body) !important;



    margin-bottom: 8px !important;



    transition: border-color var(--duration-fast) var(--ease-out) !important;



}



.gr-accordion:hover { border-color: var(--border-default) !important; }



.gr-accordion .label-wrap { font-weight: 600 !important; font-size: 0.88rem !important; color: var(--text-heading) !important; }



.gr-accordion .label-wrap.open { color: var(--accent) !important; }







/* --- Code --- */



.gr-code { border-radius: var(--radius-sm) !important; border: 1px solid var(--border-subtle) !important; background: var(--surface-code) !important; }



.gr-code .cm-editor { background: var(--surface-code) !important; font-family: "JetBrains Mono", "Fira Code", monospace !important; }



.gr-code .cm-editor .cm-content { color: #cbd5e1 !important; font-size: 0.84rem !important; line-height: 1.65 !important; }



.gr-code .cm-editor .cm-line { caret-color: #60a5fa !important; }







/* --- Markdown --- */



.prose, .markdown-text { color: var(--text-body) !important; }



.prose h1,.prose h2,.prose h3,.markdown-text h1,.markdown-text h2,.markdown-text h3 { color: var(--text-heading) !important; }



.prose code,.markdown-text code { background: var(--surface-code) !important; color: #7dd3fc !important; padding: 2px 6px !important; border-radius: var(--radius-xs) !important; font-family: "JetBrains Mono", monospace !important; font-size: 0.85em !important; }







/* --- Checkbox --- */



.gr-checkbox .checkbox-label { color: var(--text-secondary) !important; }



.gr-checkbox input[type="checkbox"] { accent-color: var(--accent) !important; }







/* --- File Upload --- */



.gr-file .file-preview { background: var(--surface-input) !important; border-radius: var(--radius-sm) !important; }







/* --- Level Badges --- */



.level-badge-high { display:inline-block;padding:4px 14px;border-radius:20px;font-weight:700;font-size:.82rem;letter-spacing:.04em;background:var(--danger-soft);color:#fecaca;border:1px solid rgba(239,68,68,.3); }



.level-badge-medium { display:inline-block;padding:4px 14px;border-radius:20px;font-weight:700;font-size:.82rem;letter-spacing:.04em;background:var(--warning-soft);color:#fde68a;border:1px solid rgba(245,158,11,.3); }



.level-badge-low { display:inline-block;padding:4px 14px;border-radius:20px;font-weight:700;font-size:.82rem;letter-spacing:.04em;background:var(--success-soft);color:#bbf7d0;border:1px solid rgba(34,197,94,.3); }







/* --- Scrollbar --- */



::-webkit-scrollbar { width: 8px; height: 8px; }



::-webkit-scrollbar-track { background: var(--surface-root); }



::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 4px; }



::-webkit-scrollbar-thumb:hover { background: var(--border-strong); }







/* --- Selection --- */



::selection { background: rgba(59,130,246,.35); color: #fff; }







/* --- Disposal Tab: Accordions --- */



.disposal-accordion {



    border-left: 3px solid var(--border-subtle) !important;



    padding-left: 4px !important;



    margin-bottom: 6px !important;



    transition: border-left-color var(--duration-normal) var(--ease-out) !important;



}



.disposal-accordion:hover { border-left-color: var(--accent) !important; }



.disposal-accordion .label-wrap { font-size: 0.9rem !important; font-weight: 600 !important; color: var(--text-heading) !important; }



.disposal-accordion .label-wrap.open { color: var(--accent) !important; }







/* --- Disposal Tab: Level Display --- */



.level-display input, .level-display textarea {



    text-align: center !important;



    font-weight: 700 !important; font-size: 1.1rem !important;



    letter-spacing: .04em !important;



    padding: 12px !important;



    background: var(--surface-input) !important;



    border: 1px solid var(--border-subtle) !important;



}







/* --- Disposal Tab: Notification Status --- */



.notification-status input, .notification-status textarea {



    font-size: 0.86rem !important;



    padding: 10px 14px !important;



    background: var(--surface-input) !important;



    border: 1px solid var(--border-subtle) !important;



}







/* --- Disposal Tab: Level Badges --- */



.level-badge-high {



    display: inline-block; padding: 6px 16px; border-radius: 20px;



    font-weight: 700; font-size: 0.84rem; letter-spacing: .04em;



    background: rgba(239,68,68,.15); color: #fecaca;



    border: 1px solid rgba(239,68,68,.3);



}



.level-badge-medium {



    display: inline-block; padding: 6px 16px; border-radius: 20px;



    font-weight: 700; font-size: 0.84rem; letter-spacing: .04em;



    background: rgba(245,158,11,.15); color: #fde68a;



    border: 1px solid rgba(245,158,11,.3);



}



.level-badge-low {



    display: inline-block; padding: 6px 16px; border-radius: 20px;



    font-weight: 700; font-size: 0.84rem; letter-spacing: .04em;



    background: rgba(34,197,94,.15); color: #bbf7d0;



    border: 1px solid rgba(34,197,94,.3);



}







/* --- Animations --- */



@keyframes pulse-dot {



    0%, 100% { opacity: 1; transform: scale(1); }



    50% { opacity: .5; transform: scale(1.3); }



}







/* --- Video Player --- */



.gr-video video {



    border-radius: var(--radius-sm) !important;



    border: 1px solid var(--border-subtle) !important;



    background: #000 !important;



}



.gr-video { border-radius: var(--radius-sm) !important; }







/* --- Image Display --- */



.gr-image img {



    border-radius: var(--radius-sm) !important;



    border: 1px solid var(--border-subtle) !important;



}







/* --- Tab Content Area --- */



.tabitem {



    background: var(--surface-root) !important;



}







/* --- Progress Bar --- */



.gr-progress { background: var(--surface-input) !important; border-radius: var(--radius-xs) !important; }



.gr-progress .fill { background: var(--accent) !important; border-radius: var(--radius-xs) !important; }







/* --- Toast / Notifications --- */



.gr-toast { background: var(--surface-card) !important; color: var(--text-body) !important; border: 1px solid var(--border-default) !important; border-radius: var(--radius-sm) !important; }







/* --- Error states --- */



.gr-textbox.error textarea, .gr-textbox.error input { border-color: var(--danger) !important; }



.gr-textbox.error textarea:focus, .gr-textbox.error input:focus { box-shadow: 0 0 0 3px var(--danger-soft) !important; }







/* --- Disabled state --- */



.gr-button:disabled, button:disabled {



    opacity: .45 !important; cursor: not-allowed !important;



    transform: none !important; box-shadow: none !important;



}







/* --- Panel / Group --- */



.gr-panel {



    background: var(--surface-card) !important;



    border: 1px solid var(--border-subtle) !important;



    border-radius: var(--radius-sm) !important;



}







/* --- Dataframe / Table --- */



.gr-dataframe table, .gr-dataframe th, .gr-dataframe td {



    border-color: var(--border-subtle) !important;



    color: var(--text-body) !important;



}



.gr-dataframe th { background: var(--surface-card-alt) !important; color: var(--text-heading) !important; font-weight: 600 !important; }



.gr-dataframe tr:nth-child(even) { background: rgba(255,255,255,.01) !important; }



.gr-dataframe tr:hover { background: rgba(59,130,246,.05) !important; }







/* --- Tabs: content padding on mobile --- */



@media (max-width: 768px) {



    .tabs > .tabitem { padding: 12px !important; }



}







/* --- Responsive --- */



@media (min-width: 1920px) { .gradio-container { max-width: 74vw !important; } }



@media (max-width: 768px) {



    .gradio-container { max-width: 100% !important; min-width: auto !important; padding: 8px !important; }



    .header-banner { padding: 16px 18px !important; }



    .header-banner h1 { font-size: 1.3rem !important; }



    .section-card, .section-card-alt { padding: 16px !important; }



    .tab-nav button, .tab-nav .tab-nav-item { padding: 10px 14px !important; font-size: 0.8rem !important; }



}



"""











# ===========================================================================



# Build UI



# ===========================================================================







def build_ui(lang: str = "zh"):



    texts = UI_TEXTS.get(lang, UI_TEXTS["zh"])







    with gr.Blocks(title=texts["title"]) as demo:







        # ━━━ Header ━━━



        gr.HTML(f"""<div class="header-banner">



            <div style="display:flex;align-items:center;gap:16px;">



                <div style="width:44px;height:44px;border-radius:10px;background:rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;backdrop-filter:blur(4px);">&#128065;</div>



                <div>



                    <h1>{texts["title"]}</h1>



                    <p class="subtitle">{texts["subtitle"]}</p>



                </div>



                <div style="margin-left:auto;display:flex;align-items:center;gap:8px;padding:8px 16px;background:rgba(255,255,255,.08);border-radius:20px;border:1px solid rgba(255,255,255,.1);backdrop-filter:blur(4px);">



                    <div style="width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px rgba(34,197,94,.6);animation:pulse-dot 2s ease-in-out infinite;"></div>



                    <span style="font-size:0.82rem;color:rgba(255,255,255,.8);font-weight:500;">System Online</span>



                </div>



            </div>



        </div>""")







        lang_btn = gr.Button(texts["switch_btn"], size="sm")







        with gr.Tabs():



            # ================================================================



            # TAB 1: Vision Detection



            # ================================================================



            with gr.TabItem(texts["tab_detect"], id="detect"):



                gr.Markdown(texts["detect_desc"], elem_classes="tab-desc")







                # Input Area



                with gr.Row():



                    file_input = gr.File(label=texts["file_label"], type="filepath", file_types=["image", "video"], file_count="single", scale=1)



                    source_input = gr.Textbox(label=texts["source_label"], placeholder=texts["source_placeholder"], lines=2, scale=1)



                with gr.Row():



                    task_dropdown = gr.Dropdown(choices=texts["task_choices"], value=texts["task_choices"][0], label=texts["task_label"], scale=1)



                    text_input = gr.Textbox(label=texts["text_label"], placeholder=texts["text_placeholder"], lines=3, scale=1)







                with gr.Accordion(texts["advanced_label"], open=False):



                    with gr.Row():



                        conf_slider = gr.Slider(0.1, 0.95, value=0.4, step=0.05, label=texts["conf_label"])



                        stride_slider = gr.Slider(1, 30, value=5, step=1, label=texts["stride_label"])



                        max_frames_slider = gr.Slider(10, 500, value=100, step=10, label=texts["max_frames_label"])







                run_btn = gr.Button(texts["run_btn"], variant="primary", elem_classes="primary-btn")







                # Results: Left main + Right sidebar



                with gr.Row(equal_height=True):



                    # LEFT: main output



                    with gr.Column(scale=5, elem_classes="section-card"):



                        gr.Markdown(f"**{texts['summary_heading']}**", elem_classes="section-heading")



                        summary_md = gr.Markdown(value=texts["waiting_text"], elem_classes="result-summary")



                    # RIGHT: alarm gallery



                    with gr.Column(scale=2, min_width=300, elem_classes="section-card-alt"):



                        gr.Markdown(f"**{texts['alarm_heading']}**", elem_classes="section-heading")



                        alarm_gallery = gr.Gallery(label="", columns=3, rows=2, height=360, elem_classes="alarm-gallery")







                # Annotated image



                with gr.Row():



                    annotated_image = gr.Image(label=texts["annotated_label"], height=480)







                # Annotated video



                video_output = gr.Video(label=texts["video_label"])







                # JSON + Log path



                with gr.Row():



                    with gr.Column(scale=3, elem_classes="section-card-alt"):



                        gr.Markdown(f"**{texts['json_label']}**", elem_classes="section-heading")



                        json_output = gr.JSON(label="", elem_classes="json-output")



                    with gr.Column(scale=1, min_width=280, elem_classes="section-card-alt"):



                        gr.Markdown(f"**{texts['log_path_label']}**", elem_classes="section-heading")



                        log_path_output = gr.Textbox(label="", interactive=False)







                agent_chat_history = gr.State([])







            # ================================================================



            # TAB 2: RAG Knowledge Q&A



            # ================================================================



            with gr.TabItem(texts["tab_rag"], id="rag"):



                gr.Markdown(texts["rag_desc"], elem_classes="tab-desc")







                # Question input



                with gr.Row():



                    with gr.Column(scale=6):



                        rag_question = gr.Textbox(label=texts["rag_question_label"], placeholder=texts["rag_question_placeholder"], lines=4)



                    with gr.Column(scale=1, min_width=180):



                        rag_top_k = gr.Slider(1, 10, value=4, step=1, label=texts["rag_topk_label"])



                        rag_use_llm = gr.Checkbox(label=texts["rag_llm_label"], value=True)



                        rag_btn = gr.Button(texts["rag_btn"], variant="primary", elem_classes="primary-btn")







                # Answer + Details



                with gr.Row(equal_height=True):



                    with gr.Column(scale=5, elem_classes="section-card"):



                        gr.Markdown(f"**{texts['rag_answer_title']}**", elem_classes="section-heading")



                        rag_answer_md = gr.Markdown(value=texts["rag_answer_default"], elem_classes="rag-answer")



                    with gr.Column(scale=2, min_width=300, elem_classes="section-card-alt"):



                        gr.Markdown(f"**{texts['rag_details_heading']}**", elem_classes="section-heading")



                        rag_model_info = gr.Markdown(value="", elem_classes="rag-details", label=texts["rag_model_label"])



                        rag_sources_md = gr.Markdown(value=texts["rag_sources_default"], elem_classes="rag-details", label=texts["rag_sources_label"])



                        rag_chunks_md = gr.Markdown(value=texts["rag_chunks_default"], elem_classes="rag-details", label=texts["rag_chunks_label"])







                # Example questions



                with gr.Accordion(texts["rag_examples_label"], open=False):



                    gr.Markdown(texts["rag_examples_text"])







                rag_chat_history = gr.State([])







            # ================================================================



            # TAB 3: Logs & Reports



            # ================================================================



            with gr.TabItem(texts["tab_logs"], id="logs"):



                gr.Markdown(texts["logs_desc"], elem_classes="tab-desc")







                # Query bar



                with gr.Row():



                    log_query_input = gr.Textbox(label=texts["log_query_label"], placeholder=texts["log_query_placeholder"], lines=3, scale=5)



                    log_query_btn = gr.Button(texts["log_query_btn"], variant="primary", elem_classes="primary-btn", scale=1, min_width=160)







                # Results + Gallery



                with gr.Row(equal_height=True):



                    with gr.Column(scale=5, elem_classes="section-card"):



                        gr.Markdown(f"**{texts['log_result_heading']}**", elem_classes="section-heading")



                        log_result_md = gr.Markdown(value=texts["log_result_default"], elem_classes="result-summary")



                    with gr.Column(scale=2, min_width=300, elem_classes="section-card-alt"):



                        gr.Markdown(f"**{texts['log_alarm_heading']}**", elem_classes="section-heading")



                        log_alarm_gallery = gr.Gallery(label="", columns=3, rows=2, height=360)



                log_report_path = gr.Textbox(label=texts["log_report_label"], interactive=False)







            # ================================================================



            # TAB 4: Event Disposal (Multi-Agent)



            # ================================================================



            build_disposal_tab(texts)







        # ━━━ Footer ━━━



        gr.HTML(f"<footer>{texts['footer']}</footer>")











        # ━━━ Bind events ━━━



        run_btn.click(



            fn=process,



            inputs=[file_input, text_input, task_dropdown, source_input, conf_slider, stride_slider, max_frames_slider, agent_chat_history],



            outputs=[summary_md, annotated_image, video_output, alarm_gallery, json_output, log_path_output, agent_chat_history],



        )







        rag_btn.click(



            fn=rag_chat,



            inputs=[rag_question, rag_top_k, rag_use_llm, rag_chat_history],



            outputs=[rag_answer_md, rag_model_info, rag_sources_md, rag_chunks_md, rag_chat_history],



        )







        def log_query_handler(query_text: str) -> tuple:



            if not query_text.strip():



                return "*Enter a query.*", [], ""



            try:



                output = run_agent(image=None, text_prompt=query_text.strip())



                if output["error"]:



                    return f"**Error**: {output['error']}", [], ""



                md = _format_agent_result(output)



                alarm_imgs = []



                report_path = ""



                if output.get("intent") in ("inspection_report", "event_log", "fire_log"):



                    result = output.get("result", {})



                    raw_imgs = result.get("alarm_images", []) or result.get("recent_alarms", [])



                    if raw_imgs and isinstance(raw_imgs[0], dict):



                        alarm_imgs = [a.get("alarm_image", "") for a in raw_imgs[:4]]



                    report_path = result.get("report_path", "")



                return md, alarm_imgs, report_path



            except Exception as e:



                return f"**Error**: {e}", [], ""







        log_query_btn.click(



            fn=log_query_handler,



            inputs=[log_query_input],



            outputs=[log_result_md, log_alarm_gallery, log_report_path],



        )







    return demo











# ===========================================================================



# Process handler (unchanged)



# ===========================================================================







def process(file_path, text_prompt, task, source, confidence, stride, max_frames, chat_history):



    from pathlib import Path



    from app.runtime.unified_pipeline import run_unified_detection



    import json as _json







    prompt = text_prompt or ""



    task_map = {



        "自动判断": "auto", "Auto Detect": "auto",



        "通用物品检测": "general", "General Object Detection": "general",



        "火灾烟雾预警": "fire", "Fire & Smoke Warning": "fire",



        "安全帽反光衣工检": "ppe", "PPE Safety Helmet & Reflective Vest Check": "ppe",



    }



    task_name = task_map.get(task, "auto")







    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}



    is_video = False



    video_src = None







    if file_path:



        fp = file_path if isinstance(file_path, str) else str(file_path)



        if Path(fp).suffix.lower() in video_exts:



            is_video = True



            video_src = fp



    elif source and source.strip():



        video_src = source.strip()



        is_video = True







    if is_video and video_src:



        try:



            summary_md, annotated, video_out, alarms, json_str, log_path = run_unified_detection(



                file_obj=video_src if file_path else None,



                text_prompt=prompt, task_dropdown=task,



                source_text=video_src if not file_path else "",



                conf=confidence, frame_stride=stride, max_frames=max_frames,



            )



            json_data = _json.loads(json_str) if isinstance(json_str, str) else json_str



            chat_history = chat_history or []



            chat_history.append({"role": "user", "content": prompt or f"[{task_name}]"})



            chat_history.append({"role": "assistant", "content": summary_md})



            return summary_md, annotated, video_out, alarms, json_data, log_path, chat_history



        except Exception as exc:



            return f"**Error**: {exc}", None, None, [], {}, "", chat_history







    image = None



    if file_path:



        image = file_path if isinstance(file_path, str) else str(file_path)



    elif source and source.strip():



        media_type = detect_media(source.strip())



        if media_type == "image":



            image = source.strip()







    try:



        output = run_agent(image=image, text_prompt=prompt, task=task_name, confidence=confidence)



    except Exception as exc:



        return f"**Error**: {exc}", None, None, [], {}, "", chat_history







    error = output.get("error", "")



    if error:



        return f"**Error**: {error}", None, None, [], {}, "", chat_history







    result = output.get("result", {})



    summary = _format_agent_result(output)







    annotated_path = None



    if image and result.get("detection"):



        try:



            annotated_path = annotate_and_save(image, result["detection"])



        except Exception:



            annotated_path = None







    video_path = result.get("video_path", None)



    alarm_images = []



    if result.get("alarm_images"):



        alarm_images = [a.get("alarm_image", "") if isinstance(a, dict) else a for a in result["alarm_images"][:4]]



    elif result.get("recent_alarms"):



        alarm_images = [a.get("alarm_image", "") if isinstance(a, dict) else a for a in result["recent_alarms"][:4]]







    json_data = result.get("detection", {}) or result



    log_path = result.get("log_path", "") or result.get("report_path", "")







    chat_history = chat_history or []



    chat_history.append({"role": "user", "content": prompt or f"[{task_name}]"})



    chat_history.append({"role": "assistant", "content": summary})







    return summary, annotated_path, video_path, alarm_images, json_data, log_path, chat_history











# ===========================================================================



# Helpers (unchanged)



# ===========================================================================







def annotate_and_save(image_path, detection_result):



    import cv2



    img = cv2.imread(image_path)



    if img is None:



        return None



    detections = detection_result.get("detections", []) or detection_result.get("objects", [])



    for det in detections:



        bbox = det.get("bbox", [])



        if len(bbox) == 4:



            x1, y1, x2, y2 = map(int, bbox)



            cv2.rectangle(img, (x1, y1), (x2, y2), (37, 99, 235), 2)



            label = f"{det.get('class_name', det.get('class', '?'))} {det.get('confidence', 0):.2f}"



            cv2.putText(img, label, (x1, max(y1 - 8, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)



    out_path = str(Path(image_path).parent / f"annotated_{Path(image_path).name}")



    cv2.imwrite(out_path, img)



    return out_path











def _format_agent_result(output: dict) -> str:



    intent = output.get("intent", "unknown")



    error = output.get("error", "")



    result = output.get("result", {})



    if error:



        return f"**Error**: {error}"



    lines = [f"**Intent**: {intent}"]



    if intent == "object_detection":



        det = result.get("detection", {})



        count = det.get("total_detections", 0)



        lines.append(f"- 检测到 **{count}** 个目标")



        classes = det.get("class_counts", {})



        if classes:



            for cls, cnt in classes.items():



                lines.append(f"  - {cls}: {cnt}")



    elif intent == "fire_alarm":



        det = result.get("detection", {})



        count = det.get("total_detections", 0)



        lines.append(f"- 火灾预警检测到 **{count}** 个目标")



        if result.get("alarm_level"):



            lines.append(f"- 报警等级: **{result['alarm_level']}**")



    elif intent == "ppe_check":



        det = result.get("detection", {})



        count = det.get("total_detections", 0)



        lines.append(f"- PPE 检测到 **{count}** 个目标")



        violations = result.get("violations", [])



        if violations:



            lines.append(f"- 违规项: {', '.join(violations)}")



    elif intent == "inspection_report":



        if result.get("report"):



            lines.append(f"- 报告已生成")



            lines.append(f"  - 路径: `{result.get('report_path', '')}`")



    elif intent == "event_log":



        logs = result.get("logs", [])



        lines.append(f"- 查询到 **{len(logs)}** 条日志")



    elif intent == "fire_log":



        logs = result.get("logs", [])



        lines.append(f"- 查询到 **{len(logs)}** 条火灾日志")



    elif intent == "rag_query":



        if result.get("answer"):



            lines.append(f"- RAG 回答已生成")



    elif intent == "unknown":



        lines.append("- 无法判断意图，请提供更明确的指令")



    return "\n".join(lines)











def rag_chat(question, top_k, use_llm, history):



    if not question or not question.strip():



        return "*请输入问题*", "", "*来源将在此显示...*", "*检索片段将在此显示...*", history



    try:



        from app.rag.rag_tool import rag_query



        from app.llm.deepseek_client import DEEPSEEK_MODEL



        result = rag_query(question.strip(), top_k=top_k, use_llm=use_llm)



        answer = result.get("answer", "*无回答*")



        sources = result.get("source_files", [])



        chunks = result.get("retrieved_chunks", [])



        model_info = f"**模型**: {DEEPSEEK_MODEL} | **LLM**: {'启用' if use_llm else '关闭'} | **Top-K**: {top_k}"



        sources_md = "\n".join(f"- `{s}`" for s in sources) if sources else "*无匹配来源*"



        chunks_md = "\n\n".join(f"**{c.get('source', '?')}** ({c.get('chunk_id', '?')})\n{c.get('text', '')[:200]}..." for c in chunks[:3]) if chunks else "*无检索片段*"



        history = history or []



        history.append({"role": "user", "content": question})



        history.append({"role": "assistant", "content": answer})



        return answer, model_info, sources_md, chunks_md, history



    except Exception as e:



        return f"**Error**: {e}", "", "", "", history











# ===========================================================================



# Preload helpers



# ===========================================================================







def preload_embedding_model():



    try:



        from app.rag.vector_store import _get_model



        _get_model()



        logger.info("Embedding model ready")



    except Exception as exc:



        logger.warning("Embedding preload failed", exc_info=True)







# ===========================================================================



# Port finder



# ===========================================================================







def _find_free_port(start=7861):



    for port in range(start, start + 100):



        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:



            try:



                s.bind(("127.0.0.1", port))



                return port



            except OSError:



                continue



    return start







# ===========================================================================



# Cleanup



# ===========================================================================







def _cleanup_on_exit():



    try:



        from app.rag.vector_store import _close_chroma_client



        _close_chroma_client()



    except Exception:



        pass







# ===========================================================================



# Entry point



# ===========================================================================







if __name__ == "__main__":



    atexit.register(_cleanup_on_exit)

    from app.utils.logging_config import setup_logging
    setup_logging()



    logger.info("=" * 60)



    logger.info("RoboVision Agent starting")



    logger.info("=" * 60)



    port = _find_free_port(7861)



    logger.info(f"Starting on http://127.0.0.1:{port}")



    try:



        demo = build_ui()



    except Exception as exc:



        logger.critical("Failed to build UI", exc_info=True)



        sys.exit(1)



    logger.info("Preloading embedding model...")



    preload_embedding_model()



    try:



        demo.launch(server_name="0.0.0.0", server_port=port, inbrowser=True, share=False, show_error=True, css=custom_css)



    except (SystemExit, KeyboardInterrupt):



        pass



    except Exception as exc:



        logger.critical("Failed to launch Gradio server", exc_info=True)



        sys.exit(1)



