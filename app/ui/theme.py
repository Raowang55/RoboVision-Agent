# -*- coding: utf-8 -*-
"""Industrial Console Dark Theme CSS for RoboVision Agent.

Exports `CUSTOM_CSS` — a single string that can be passed to
`gr.Blocks(css=...)`.
"""

from __future__ import annotations

CUSTOM_CSS = """




/* ======================================================



   RoboVision Industrial Console -- Design System v2



   ====================================================== */

























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

    /* Keep RoboVision tokens local so Gradio theme variables cannot override them. */
    --text-heading:      #f8fafc;
    --text-body:         #e2e8f0;
    --text-secondary:    #cbd5e1;
    --text-muted:        #94a3b8;
    --body-text-color:          #e2e8f0;
    --body-text-color-subdued:  #cbd5e1;
    --block-title-text-color:   #f8fafc;
    --block-label-text-color:   #cbd5e1;
    --input-placeholder-color:  #94a3b8;
    --button-secondary-text-color: #e2e8f0;



    width: 100% !important; max-width: 1200px !important;
    min-width: 0 !important; margin: 0 auto !important;



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

.header-content {
    display: flex; align-items: center; gap: 16px; min-width: 0;
}

.header-icon {
    width: 44px; height: 44px; border-radius: 10px;
    background: rgba(255,255,255,.12); display: flex;
    align-items: center; justify-content: center; font-size: 22px;
    flex: 0 0 44px; backdrop-filter: blur(4px);
}

.header-brand { min-width: 0; }

.web-ready-badge {
    margin-left: auto; display: flex; align-items: center; gap: 8px;
    padding: 8px 16px; background: rgba(255,255,255,.08);
    border-radius: 20px; border: 1px solid rgba(255,255,255,.1);
    backdrop-filter: blur(4px); flex: 0 0 auto;
}

.web-ready-badge span {
    font-size: .82rem; color: rgba(255,255,255,.88) !important; font-weight: 600;
}

.web-ready-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
    box-shadow: 0 0 8px rgba(34,197,94,.6); animation: pulse-dot 2s ease-in-out infinite;
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

/* Gradio 5/6 uses ARIA tabs; keep selectors stable across generated classes. */
.gradio-container [role="tab"] {
    color: var(--text-secondary) !important;
}

.gradio-container [role="tab"][aria-selected="true"] {
    color: #60a5fa !important;
    border-bottom-color: #3b82f6 !important;
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

.tab-desc, .tab-desc p, .tab-desc span,
.section-heading, .section-heading p, .section-heading strong,
.result-summary, .result-summary p, .result-summary em,
.rag-details, .rag-details p {
    color: var(--text-body) !important;
}

.section-heading, .section-heading strong { color: #93c5fd !important; }

.gradio-container label,
.gradio-container label span,
.gradio-container .block-info,
.gradio-container .label-wrap,
.gradio-container .wrap > span {
    color: var(--text-secondary) !important;
}

.gradio-container [data-testid="block-label"] {
    background: var(--surface-card-alt) !important;
    color: var(--text-heading) !important;
    border: 1px solid var(--border-default) !important;
}

.gradio-container [data-testid="block-label"] span,
.gradio-container [data-testid="block-label"] svg {
    color: var(--text-secondary) !important;
    stroke: currentColor !important;
}

.gradio-container .wrap:has(> .wrap-inner > .secondary-wrap > [role="listbox"]),
.gradio-container .wrap-inner:has(> .secondary-wrap > [role="listbox"]),
.gradio-container .secondary-wrap:has(> [role="listbox"]),
.gradio-container [role="listbox"] {
    background: var(--surface-input) !important;
    color: var(--text-body) !important;
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



    html, body { overflow-x: hidden !important; }

    div.gradio-container.gradio-container {
        width: 100% !important; max-width: 100% !important;
        min-width: 0 !important; padding: 8px !important; overflow-x: hidden !important;
    }

    div.gradio-container.gradio-container > .main,
    div.gradio-container.gradio-container > .main > .wrap,
    div.gradio-container.gradio-container .contain {
        width: 100% !important; max-width: 100% !important; min-width: 0 !important;
    }

    .gradio-container *, .gradio-container *::before, .gradio-container *::after {
        box-sizing: border-box;
    }



    .header-banner { padding: 16px 18px !important; }

    .header-content { align-items: flex-start; gap: 12px; flex-wrap: wrap; }

    .header-icon { width: 40px; height: 40px; flex-basis: 40px; }

    .header-brand { flex: 1 1 calc(100% - 52px); }

    .header-banner .subtitle {
        font-size: .78rem !important; line-height: 1.45 !important;
        white-space: normal !important; overflow-wrap: anywhere;
    }

    .web-ready-badge {
        margin-left: 52px; padding: 5px 10px; margin-top: -4px;
    }

    .web-ready-badge span { font-size: .72rem; }



    .header-banner h1 { font-size: 1.3rem !important; }



    .section-card, .section-card-alt { padding: 16px !important; }



    .tab-nav {
        display: flex !important; flex-wrap: nowrap !important;
        overflow-x: auto !important; overflow-y: hidden !important;
        scrollbar-width: thin; -webkit-overflow-scrolling: touch;
    }

    .tab-nav button, .tab-nav .tab-nav-item,
    .gradio-container [role="tab"] {
        flex: 0 0 auto !important; white-space: nowrap !important;
        padding: 10px 12px !important; font-size: 0.78rem !important;
    }

    .gr-code, .gr-code .cm-editor, .gr-code .cm-scroller,
    .json-output, .json-output pre {
        max-width: 100% !important; min-width: 0 !important;
        overflow-x: auto !important;
    }

    .json-output pre { white-space: pre-wrap !important; overflow-wrap: anywhere !important; }

    .run-details .section-card-alt { min-width: 0 !important; }



}















"""
